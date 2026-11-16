from .db import db_connection
from dtos import QueryDTO
import logging

logger = logging.getLogger(__name__)


def insert_query(upload_id, keyword, query_params) -> int:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO queries (upload_id, search_keyword, query_params) VALUES (?, ?, ?)",
            (upload_id, keyword, query_params),
        )
        return cursor.lastrowid


def get_query_by_upload_id(upload_id: int) -> QueryDTO:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, search_keyword, query_params FROM queries WHERE upload_id = ? ORDER BY id DESC LIMIT 1",
            (upload_id,),
        )
        result = cursor.fetchone()

    if not result:
        raise ValueError(f"No query found for upload ID: {upload_id}")

    return QueryDTO.from_row(result)
