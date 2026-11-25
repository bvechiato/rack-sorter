import logging

from dtos import RerankFeedback

from .db import db_connection

logger = logging.getLogger(__name__)


def insert_rerank_feedback(upload_id: int, item_url: str, feedback_type: str, concept: str = None, aesthetic: str = None):
    logger.info("Inserting feedback for %s, %s, %s, %s, %s", upload_id, feedback_type, concept, item_url, aesthetic)
    with db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO rerank_feedback (upload_id, item_url, feedback_type, concept, aesthetic)
                VALUES (?, ?, ?, ?, ?)
            """, (upload_id, item_url, feedback_type, concept, aesthetic))
        except Exception as e:
            logger.warning("Could not insert feedback: %s", e)


def get_feedback_for_upload(upload_id: int) -> list[RerankFeedback]:
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT item_url, feedback_type, concept, aesthetic
            FROM rerank_feedback
            WHERE upload_id = ?
            ORDER BY id ASC
        """, (upload_id,))
        rows = cursor.fetchall()

    return [RerankFeedback.from_row(row) for row in rows]


def delete_last_feedback_for_upload(upload_id: int) -> bool:
    """Delete the most recent rerank_feedback row for an upload.

    Returns True if a row was deleted, False if there was nothing to undo.
    """
    logger.info("Deleting last feedback for upload %s", upload_id)
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM rerank_feedback
            WHERE upload_id = ?
            ORDER BY id DESC
            LIMIT 1
        """, (upload_id,))
        row = cursor.fetchone()
        if not row:
            return False
        cursor.execute("DELETE FROM rerank_feedback WHERE id = ?", (row[0],))
    return True


def get_last_feedback_for_upload(upload_id: int):
    """Return the most recent feedback event for an upload, or None if none exists."""
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT item_url, feedback_type, concept, aesthetic
            FROM rerank_feedback
            WHERE upload_id = ?
            ORDER BY id DESC
            LIMIT 1
        """, (upload_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return RerankFeedback.from_row(row)
