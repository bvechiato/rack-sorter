import sqlite3
from dataclasses import dataclass
from typing import Optional, Tuple
from . import constants


@dataclass
class QueryDTO:
    id: int
    search_keyword: str
    query_params: Optional[str] = None

    @staticmethod
    def from_row(row: Tuple) -> "QueryDTO":
        return QueryDTO(id=row[0], search_keyword=row[1], query_params=row[2])


def insert_query(upload_id, keyword, query_params) -> int:
    conn = sqlite3.connect(constants.DB)
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO queries (upload_id, search_keyword, query_params) VALUES (?, ?, ?)", 
                   (upload_id, keyword, query_params))
    conn.commit()
    conn.close()
    return cursor.lastrowid

def get_query_by_upload_id(upload_id: int) -> QueryDTO:
    conn = sqlite3.connect(constants.DB)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, search_keyword, query_params FROM queries WHERE upload_id = ?", (upload_id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise ValueError(f"No query found for upload ID: {upload_id}")
    
    return QueryDTO.from_row(result)