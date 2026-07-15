import sqlite3
import uuid
import os
from repository.constants import UPLOADS_PATH, DB, CREATE_TABLES_QUERY
from repository.query import insert_query
from repository.search_items import insert_search_items

def save_query_to_db(upload_id, keyword, query_params, items):
    query_id = insert_query(upload_id, keyword, query_params)
    sanitized = []
    for it in items:
        if isinstance(it, dict):
            itm = it.copy()
        else:
            try:
                itm = it.to_dict()
            except Exception:
                itm = {}

        emb = None
        if isinstance(itm, dict):
            emb = itm.get('embedding') or (itm.get('data') or {}).get('embedding')

        if emb is not None:
            try:
                if hasattr(emb, 'tolist'):
                    emb_list = emb.tolist()
                else:
                    emb_list = list(map(float, emb))
            except Exception:
                emb_list = None

            if emb_list is not None:
                try:
                    emb_list = [float(x) for x in emb_list]
                except Exception:
                    emb_list = None

            if emb_list is not None:
                itm['embedding'] = emb_list

        sanitized.append(itm)

    insert_search_items(query_id, sanitized)

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
    print(f"[LOG] User upload saved with ID: {upload_id} and path: {image_path}")

    save_clip_analysis(cursor, upload_id, tags_dict)
    print(f"[LOG] CLIP analysis tags saved for upload ID: {upload_id}")

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
    connection.commit()
    print(f"[LOG] Db initialized and tables successfully.")
    return connection
