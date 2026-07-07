import sqlite3
from dataclasses import dataclass
from typing import Tuple
from . import constants

@dataclass
class UserUpload:
    id: int
    image_path: str

    @staticmethod
    def from_row(row: Tuple) -> "UserUpload":
        return UserUpload(id=row[0], image_path=row[1])


def get_upload_by_id(upload_id: int) -> UserUpload:
    conn = sqlite3.connect(constants.DB)
    cursor = conn.cursor()

    cursor.execute("SELECT id, image_path FROM user_uploads WHERE id = ?", (upload_id,))
    result = cursor.fetchone()
    conn.close()

    if not result:
        raise FileNotFoundError(f"No database entry found for upload ID: {upload_id}")

    return UserUpload.from_row(result)