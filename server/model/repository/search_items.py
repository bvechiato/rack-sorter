import json
import sqlite3
from typing import List, Iterable, Union
from . import constants
import numpy as np
from dtos import SearchItem


def get_items_by_query_id(query_id: int) -> List[SearchItem]:
    conn = sqlite3.connect(constants.DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT title, url, image_url, blob_data, embedding
        FROM search_items 
        WHERE query_id = ?
    """, (query_id,))

    results = cursor.fetchall()
    conn.close()
    
    items = []
    for row in results:
        si = SearchItem.from_json(row[3])
        embedding_blob = row[4] if len(row) > 4 else None
        if embedding_blob is not None:
            try:
                si.embedding = np.frombuffer(embedding_blob, dtype=np.float32).tolist()
            except Exception:
                # ignore malformed embedding blob
                pass
        items.append(si)

    return items

def get_item_by_url(item_url: str) -> SearchItem:
    conn = sqlite3.connect(constants.DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT blob_data, embedding
        FROM search_items
        WHERE url = ?
    """, (item_url,))

    result = cursor.fetchone()
    conn.close()

    if not result:
        raise ValueError(f"No item found for URL: {item_url}")

    si = SearchItem.from_json(result[0])
    embedding_blob = result[1] if len(result) > 1 else None
    if embedding_blob is not None:
        try:
            si.embedding = np.frombuffer(embedding_blob, dtype=np.float32).tolist()
        except Exception:
            pass

    return si

def insert_search_items(query_id, items: Iterable[Union[SearchItem, dict]]):
    """Insert multiple search items. Accepts either `SearchItem` instances or dict-like objects.
    Stores `embedding` into the `embedding` BLOB column when present.
    """
    conn = sqlite3.connect(constants.DB)
    cursor = conn.cursor()

    item_data = []
    for i in items:
        if isinstance(i, SearchItem):
            blob = i.to_json()
            title = i.title
            url = i.url
            image_url = i.image_url
            embedding = i.embedding
        else:
            blob = json.dumps(i)
            title = i.get('title')
            url = i.get('url')
            image_url = i.get('image_url')
            embedding = i.get('embedding')

        # Convert embedding to bytes if present
        emb_blob = None
        if embedding is not None:
            try:
                arr = np.asarray(embedding, dtype=np.float32)
                emb_blob = arr.tobytes()
            except Exception:
                emb_blob = None

        item_data.append((query_id, title, url, image_url, blob, emb_blob))

    cursor.executemany("""
        INSERT INTO search_items (query_id, title, url, image_url, blob_data, embedding) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, item_data)

    conn.commit()
    conn.close()


def update_item_embedding(item_url: str, embedding: Union[list, np.ndarray]):
    """Update the `embedding` BLOB for an item identified by `url`.
    Also updates the JSON `blob_data` to include the embedding list if present.
    """
    conn = sqlite3.connect(constants.DB)
    cursor = conn.cursor()

    emb_blob = None
    try:
        arr = np.asarray(embedding, dtype=np.float32)
        emb_blob = arr.tobytes()
    except Exception:
        emb_blob = None

    # Fetch existing blob_data to update JSON copy
    cursor.execute("SELECT blob_data FROM search_items WHERE url = ?", (item_url,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"No item found for URL: {item_url}")

    try:
        data = json.loads(row[0])
    except Exception:
        data = {}

    data['embedding'] = list(np.asarray(embedding).tolist()) if embedding is not None else None

    cursor.execute(
        """
        UPDATE search_items
        SET embedding = ?, blob_data = ?
        WHERE url = ?
        """,
        (emb_blob, json.dumps(data, ensure_ascii=False), item_url)
    )

    conn.commit()
    conn.close()
