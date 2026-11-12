import sqlite3
from . import constants
from dtos import QueryDTO

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
    
    # `timestamp` has 1 second resolution, so order by the autoincrement id instead:
    # a single upload can legitimately produce several queries (repeated searches).
    cursor.execute(
        "SELECT id, search_keyword, query_params FROM queries WHERE upload_id = ? ORDER BY id DESC LIMIT 1",
        (upload_id,),
    )
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise ValueError(f"No query found for upload ID: {upload_id}")
    
    return QueryDTO.from_row(result)