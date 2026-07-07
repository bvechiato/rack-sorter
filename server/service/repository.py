import os
from repository.user_uploads import get_image_path_by_upload_id
from repository.query import get_query_by_upload_id
from repository.search_items import get_items_by_query_id
from repository.constants import UPLOADS_PATH

def get_upload_bytes_by_id(upload_id: int) -> bytes:
    result = get_image_path_by_upload_id(upload_id)
    filename = result[0]
    full_path = os.path.join(UPLOADS_PATH, filename)
    
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Image file missing from disk: {full_path}")
        
    with open(full_path, 'rb') as file:
        return file.read()

def get_results_by_upload_id(upload_id: int) -> list:
    query_result = get_query_by_upload_id(upload_id)

    query_id = query_result[0]
    return get_items_by_query_id(query_id)
