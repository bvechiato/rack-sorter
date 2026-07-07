import json
import sqlite3
from typing import List, Iterable, Union, Any, Dict, Optional
from dataclasses import dataclass, field
from . import constants

@dataclass
class SearchItem:
    title: str
    url: str
    image_url: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "SearchItem":
        title = d.get("title")
        url = d.get("url")
        image_url = d.get("image_url")
        data = {k: v for k, v in d.items() if k not in {"title", "url", "image_url"}}
        return SearchItem(title=title, url=url, image_url=image_url, data=data)

    def to_dict(self) -> Dict[str, Any]:
        base = {"title": self.title, "url": self.url}
        if self.image_url is not None:
            base["image_url"] = self.image_url
        base.update(self.data)
        return base

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @staticmethod
    def from_json(s: str) -> "SearchItem":
        return SearchItem.from_dict(json.loads(s))


def get_items_by_query_id(query_id: int) -> List[SearchItem]:
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
    return [SearchItem.from_json(row[3]) for row in results]

def get_item_by_url(item_url: str) -> SearchItem:
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

    return SearchItem.from_json(result[0])

def insert_search_items(query_id, items: Iterable[Union[SearchItem, dict]]):
    """Insert multiple search items. Accepts either `SearchItem` instances or dict-like objects.
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
        else:
            blob = json.dumps(i)
            title = i.get('title')
            url = i.get('url')
            image_url = i.get('image_url')

        item_data.append((query_id, title, url, image_url, blob))

    cursor.executemany("""
        INSERT INTO search_items (query_id, title, url, image_url, blob_data) 
        VALUES (?, ?, ?, ?, ?)
    """, item_data)

    conn.commit()
    conn.close()
