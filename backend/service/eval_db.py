import sqlite3
import json

def save_query_to_db(keyword, query_params, items):
    conn = sqlite3.connect("search_eval.db")
    cursor = conn.cursor()
    
    # 1. Save the main query
    cursor.execute("INSERT INTO queries (search_keyword, query_params) VALUES (?, ?)", 
                   (keyword, query_params))
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
    
def init():
    connection = sqlite3.connect("search_eval.db")
    cursor = connection.cursor()
    cursor.executescript(CREATE_TABLE_QUERY)
    connection.commit()
    print(f"[LOG] Db initialized and tables successfully.")
    return connection

CREATE_TABLE_QUERY = """
CREATE TABLE IF NOT EXISTS queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    search_keyword TEXT,
    query_params TEXT
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
"""