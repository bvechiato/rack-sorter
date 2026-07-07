import json
import sqlite3
from . import constants

def get_items_by_query_id(query_id: int) -> list:
    conn = sqlite3.connect(constants.DB)
    cursor = conn.cursor()

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
    conn = sqlite3.connect(constants.DB)
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

def insert_search_items(query_id, items):
    conn = sqlite3.connect(constants.DB)
    cursor = conn.cursor()
    
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
