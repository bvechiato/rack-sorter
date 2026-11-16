import logging

from dtos import RerankFeedback

from .db import db_connection

logger = logging.getLogger(__name__)


def insert_rerank_feedback(upload_id: int, item_url: str, feedback_type: str, concept: str = None):
    logger.info("Inserting feedback for %s, %s, %s, %s", upload_id, feedback_type, concept, item_url)
    with db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO rerank_feedback (upload_id, item_url, feedback_type, concept)
                VALUES (?, ?, ?, ?)
            """, (upload_id, item_url, feedback_type, concept))
        except Exception as e:
            logger.warning("Could not insert feedback: %s", e)


def get_feedback_for_upload(upload_id: int) -> list[RerankFeedback]:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT item_url, feedback_type, concept
            FROM rerank_feedback
            WHERE upload_id = ?
            ORDER BY id ASC
        """, (upload_id,))
        rows = cursor.fetchall()

    return [RerankFeedback.from_row(row) for row in rows]
