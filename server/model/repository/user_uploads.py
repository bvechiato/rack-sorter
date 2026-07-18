import sqlite3
from . import constants
from dtos import UserUpload
import numpy as np

def get_upload_by_id(upload_id: int) -> UserUpload:
    conn = sqlite3.connect(constants.DB)
    cursor = conn.cursor()

    cursor.execute("SELECT id, image_path FROM user_uploads WHERE id = ?", (upload_id,))
    result = cursor.fetchone()
    conn.close()

    if not result:
        raise FileNotFoundError(f"No database entry found for upload ID: {upload_id}")

    return UserUpload.from_row(result)

def get_embedding_by_upload_id(upload_id: int) -> np.array:
    conn = sqlite3.connect(constants.DB)
    cursor = conn.cursor()

    cursor.execute("SELECT embedding FROM user_uploads WHERE id = ?", (upload_id,))
    result = cursor.fetchone()
    conn.close()

    if not result or result[0] is None:
        raise ValueError(f"No embedding found for upload ID: {upload_id}")

    return np.frombuffer(result[0], dtype=np.float32).tolist()

def insert_embedding_for_upload(upload_id: int, embedding: list[float]):
    conn = sqlite3.connect(constants.DB)
    cursor = conn.cursor()

    embedding_bytes = np.asarray(embedding, dtype=np.float32).tobytes()

    cursor.execute("UPDATE user_uploads SET embedding = ? WHERE id = ?", (embedding_bytes, upload_id))
    conn.commit()
    conn.close()