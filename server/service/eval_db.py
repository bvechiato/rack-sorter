import sqlite3
import json
import uuid
import os
from . import repository

DB = "search_eval.db"
UPLOADS_PATH = "server/service/static/uploads"

def save_query_to_db(upload_id, keyword, query_params, items):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    
    # 1. Save the main query
    cursor.execute("INSERT INTO queries (upload_id, search_keyword, query_params) VALUES (?, ?, ?)", 
                   (upload_id, keyword, query_params))
    query_id = cursor.lastrowid
    
    # 2. Save each item + full JSON blob
    item_data = []
    for i in items:
        blob = json.dumps(i)
        item_data.append((query_id, i.get('title'), i.get('url'), i.get('image_url'), blob))
        
    cursor.executemany("""
        INSERT INTO search_items (query_id, title, url, image_url, blob_data) 
        VALUES (?, ?, ?, ?, ?)
    """, item_data)
    
    conn.commit()
    conn.close()

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
    cursor.executescript(repository.CREATE_TABLES_QUERY)
    connection.commit()
    print(f"[LOG] Db initialized and tables successfully.")
    return connection
