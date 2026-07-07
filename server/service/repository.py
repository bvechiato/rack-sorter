import json
import sqlite3
import os

DB = "search_eval.db"
UPLOADS_PATH = "server/service/static/uploads"

def get_upload_bytes_by_id(upload_id: int) -> bytes:
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    
    cursor.execute("SELECT image_path FROM user_uploads WHERE id = ?", (upload_id,))
    result = cursor.fetchone()    
    conn.close()
    
    if not result:
        raise FileNotFoundError(f"No database entry found for upload ID: {upload_id}")
        
    filename = result[0]
    
    full_path = os.path.join(UPLOADS_PATH, filename)
    
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Image file missing from disk: {full_path}")
        
    # Read the file directly into raw memory bytes
    with open(full_path, 'rb') as file:
        return file.read()

def get_results_by_upload_id(upload_id: int) -> list:
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    # get most recent query for the given upload_id
    cursor.execute("""
        SELECT id FROM queries 
        WHERE upload_id = ? 
        ORDER BY id DESC LIMIT 1
    """, (upload_id,))
    query_result = cursor.fetchone()
    if not query_result:
        conn.close()
        raise ValueError(f"No queries found for upload ID: {upload_id}")
    
    # get all items associated with that query
    query_id = query_result[0]
    cursor.execute("""
        SELECT title, url, image_url, blob_data
        FROM search_items 
        WHERE query_id = ?
    """, (query_id,))

    results = cursor.fetchall()
    conn.close()
    
    # Convert results to a list of dictionaries
    return [
        json.loads(row[3])
        for row in results
    ]

def get_item_by_url(item_url: str) -> dict:
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT blob_data
        FROM search_items
        WHERE url = ?
    """, (item_url,))

    result = cursor.fetchone()
    conn.close()

    if not result:
        raise ValueError(f"No item found for URL: {item_url}")

    return json.loads(result[0])

def insert_rerank_feedback(upload_id: int, item_url: str, feedback_type: str):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO rerank_feedback (upload_id, item_url, feedback_type)
        VALUES (?, ?, ?)
    """, (upload_id, item_url, feedback_type))

    conn.commit()
    conn.close()

def get_feedback_for_upload(upload_id: int):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT item_url, feedback_type
        FROM rerank_feedback
        WHERE upload_id = ?
        ORDER BY timestamp ASC
    """, (upload_id,))

    rows = cursor.fetchall()
    conn.close()

    return [
        { "item_url": row[0], "feedback_type": row[1]}
        for row in rows
    ]

CREATE_TABLES_QUERY = """
CREATE TABLE IF NOT EXISTS user_uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    image_path TEXT,
    model_version TEXT DEFAULT 'v1.0'
);

CREATE TABLE IF NOT EXISTS queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_id INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    search_keyword TEXT,
    query_params TEXT,
    FOREIGN KEY (upload_id) REFERENCES user_uploads(id)
);

CREATE TABLE IF NOT EXISTS search_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_id INTEGER,
    title TEXT,
    url TEXT,
    image_url TEXT,
    blob_data TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    model_version TEXT DEFAULT 'v1.0',
    FOREIGN KEY (query_id) REFERENCES queries(id)
);

CREATE TABLE IF NOT EXISTS clip_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_id INTEGER,
    tag_name TEXT,
    score REAL,
    category_type TEXT,
    model_version TEXT DEFAULT 'v1.0',
    FOREIGN KEY (upload_id) REFERENCES user_uploads(id)
);

CREATE TABLE IF NOT EXISTS rerank_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_id INTEGER,
    item_url TEXT,
    feedback_type TEXT CHECK(feedback_type IN ('MORE', 'LESS')),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (upload_id) REFERENCES user_uploads(id)
);
"""