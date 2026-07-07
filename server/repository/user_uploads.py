import sqlite3
from . import constants

def get_image_path_by_upload_id(upload_id: int):
    conn = sqlite3.connect(constants.DB)
    cursor = conn.cursor()
    
    cursor.execute("SELECT image_path FROM user_uploads WHERE id = ?", (upload_id,))
    result = cursor.fetchone()    
    conn.close()
    
    if not result:
        raise FileNotFoundError(f"No database entry found for upload ID: {upload_id}")
    return result