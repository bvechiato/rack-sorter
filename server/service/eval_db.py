import logging
import sqlite3
import uuid
import os
from model.repository.constants import UPLOADS_PATH, DB, CREATE_TABLES_QUERY
from model.repository.query import insert_query
from model.repository.search_items import insert_search_items
logger = logging.getLogger(__name__)

def save_query_to_db(upload_id, keyword, query_params, items):
    query_id = insert_query(upload_id, keyword, query_params)
    sanitized = []
    for it in items:
        if isinstance(it, dict):
            itm = it.copy()
            embedding = itm.get('embedding')
            clip_embedding = itm.get('clip_embedding')
        else:
            itm = it.to_dict()
            embedding = getattr(it, 'embedding', None)
            clip_embedding = getattr(it, 'clip_embedding', None)

        itm['embedding'] = _as_float_list(embedding)
        itm['clip_embedding'] = _as_float_list(clip_embedding)
        sanitized.append(itm)

    insert_search_items(query_id, sanitized)


def _as_float_list(vector):
    if vector is None:
        return None
    try:
        if hasattr(vector, 'tolist'):
            return [float(x) for x in vector.tolist()]
        return [float(x) for x in vector]
    except Exception:
        return None

def save_clip_analysis(cursor, upload_id, tags_dict):
    INSERT_INTO_QUERY = """
        INSERT INTO clip_tags (upload_id, tag_name, category_type) 
        VALUES (?, ?, ?)
    """

    for category in ["classified_tags", "colour_classified_tags"]:
        for tag in tags_dict[category]:
            cursor.execute(INSERT_INTO_QUERY, (upload_id, tag, category))

    cursor.execute(INSERT_INTO_QUERY, (upload_id, tags_dict["category_archetype"], "category_archetype"))

def save_user_upload(file_contents: bytes, tags_dict: dict):
    image_path = save_image(file_contents)
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO user_uploads (image_path) VALUES (?)", (image_path,))
    upload_id = cursor.lastrowid
    logger.info(f"User upload saved with ID: {upload_id} and path: {image_path}")

    save_clip_analysis(cursor, upload_id, tags_dict)
    logger.info(f"CLIP analysis tags saved for upload ID: {upload_id}")

    conn.commit()
    conn.close()
    return upload_id

def save_image(file_contents):    
    if not os.path.exists(UPLOADS_PATH):
        os.makedirs(UPLOADS_PATH)
        
    filename = f"{uuid.uuid4()}.jpg"
    file_path = os.path.join(UPLOADS_PATH, filename)
    
    with open(file_path, 'wb') as out_file:
        out_file.write(file_contents)
        
    return filename

def init():
    connection = sqlite3.connect(DB)
    cursor = connection.cursor()
    cursor.executescript(CREATE_TABLES_QUERY)
    _add_missing_columns(cursor)
    connection.commit()
    logger.info(f"Db initialized and tables successfully.")
    return connection


def _add_missing_columns(cursor):
    """Apply additive migrations to databases created before a column existed.

    `CREATE TABLE IF NOT EXISTS` does not alter existing tables, so new columns need
    an explicit, idempotent ALTER for every tracked database.
    """
    existing = {row[1] for row in cursor.execute("PRAGMA table_info(search_items)")}
    if "clip_embedding" not in existing:
        cursor.execute("ALTER TABLE search_items ADD COLUMN clip_embedding BLOB")
        logger.info("Migrated search_items: added clip_embedding column")
