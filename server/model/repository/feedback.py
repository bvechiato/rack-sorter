import sqlite3
from . import constants
from dtos import RerankFeedback


def insert_rerank_feedback(upload_id: int, item_url: str, feedback_type: str, concept: str = None):
    conn = sqlite3.connect(constants.DB)
    cursor = conn.cursor()

    print(f"[INFO] Inserting feedback for {upload_id}, {feedback_type}, {concept}, {item_url}")
    try:
        cursor.execute("""
            INSERT INTO rerank_feedback (upload_id, item_url, feedback_type, concept)
            VALUES (?, ?, ?, ?)
        """, (upload_id, item_url, feedback_type, concept))
    except Exception as e:
        print(f"[WARN] Could not insert feedback: {e}")

    conn.commit()
    conn.close()


def get_feedback_for_upload(upload_id: int) -> list[RerankFeedback]:
    conn = sqlite3.connect(constants.DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT item_url, feedback_type, concept
        FROM rerank_feedback
        WHERE upload_id = ?
        ORDER BY timestamp ASC
    """, (upload_id,))

    rows = cursor.fetchall()
    conn.close()

    return [RerankFeedback.from_row(row) for row in rows]
