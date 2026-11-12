import json
import sqlite3
from typing import List, Iterable, Union
from . import constants
import numpy as np
from dtos import SearchItem


def _blob_to_vector(blob) -> list | None:
    if blob is None:
        return None
    try:
        return np.frombuffer(blob, dtype=np.float32).tolist()
    except Exception:
        # ignore malformed embedding blob
        return None


def _vector_to_blob(vector) -> bytes | None:
    if vector is None:
        return None
    try:
        return np.asarray(vector, dtype=np.float32).tobytes()
    except Exception:
        return None


def get_items_by_query_id(query_id: int) -> List[SearchItem]:
    conn = sqlite3.connect(constants.DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT title, url, image_url, blob_data, embedding, clip_embedding
        FROM search_items 
        WHERE query_id = ?
    """, (query_id,))

    results = cursor.fetchall()
    conn.close()
    
    items = []
    for row in results:
        si = SearchItem.from_json(row[3])
        si.embedding = _blob_to_vector(row[4]) if len(row) > 4 else None
        si.clip_embedding = _blob_to_vector(row[5]) if len(row) > 5 else None
        items.append(si)

    return items

def get_item_urls_for_query(query_id: int) -> set[str]:
    """URLs already stored for a query, used to merge a freshly scraped page."""
    conn = sqlite3.connect(constants.DB)
    cursor = conn.cursor()
    cursor.execute("SELECT url FROM search_items WHERE query_id = ?", (query_id,))
    urls = {row[0] for row in cursor.fetchall() if row[0]}
    conn.close()
    return urls


def get_item_by_url(item_url: str) -> SearchItem:
    conn = sqlite3.connect(constants.DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT blob_data, embedding, clip_embedding
        FROM search_items
        WHERE url = ?
        ORDER BY id DESC
        LIMIT 1
    """, (item_url,))

    result = cursor.fetchone()
    conn.close()

    if not result:
        raise ValueError(f"No item found for URL: {item_url}")

    si = SearchItem.from_json(result[0])
    si.embedding = _blob_to_vector(result[1]) if len(result) > 1 else None
    si.clip_embedding = _blob_to_vector(result[2]) if len(result) > 2 else None

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
            clip_embedding = i.clip_embedding
        else:
            blob = json.dumps({k: v for k, v in i.items() if k != 'clip_embedding'})
            title = i.get('title')
            url = i.get('url')
            image_url = i.get('image_url')
            embedding = i.get('embedding')
            clip_embedding = i.get('clip_embedding')

        item_data.append((
            query_id,
            title,
            url,
            image_url,
            blob,
            _vector_to_blob(embedding),
            _vector_to_blob(clip_embedding),
        ))

    cursor.executemany("""
        INSERT INTO search_items (query_id, title, url, image_url, blob_data, embedding, clip_embedding) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, item_data)

    conn.commit()
    conn.close()


def update_item_clip_embedding(item_url: str, clip_embedding: Union[list, np.ndarray, None]):
    """Update the FashionCLIP (`clip_embedding`) BLOB for an item identified by `url`.

    The vector is kept out of `blob_data` on purpose: it is only read by the trait
    scorer, and duplicating 512 floats per item would inflate every JSON blob.
    """
    conn = sqlite3.connect(constants.DB)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE search_items SET clip_embedding = ? WHERE url = ?",
        (_vector_to_blob(clip_embedding), item_url),
    )
    updated = cursor.rowcount

    conn.commit()
    conn.close()

    if updated == 0:
        raise ValueError(f"No item found for URL: {item_url}")


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
