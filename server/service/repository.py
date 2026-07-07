import os
from repository.user_uploads import get_upload_by_id
from repository.query import get_query_by_upload_id
from repository.search_items import get_items_by_query_id
from repository.constants import UPLOADS_PATH

def get_upload_bytes_by_id(upload_id: int) -> bytes:
    upload = get_upload_by_id(upload_id)
    filename = upload.image_path
    full_path = os.path.join(UPLOADS_PATH, filename)
    
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Image file missing from disk: {full_path}")
        
    with open(full_path, 'rb') as file:
        return file.read()

def get_results_by_upload_id(upload_id: int) -> list:
    query_dto = get_query_by_upload_id(upload_id)

    query_id = query_dto.id
    items = get_items_by_query_id(query_id)
    sanitized = []
    for item in items:
        if isinstance(item, dict):
            sanitized.append(item)
        elif hasattr(item, "to_dict"):
            sanitized.append(item.to_dict())
        else:
            try:
                sanitized.append(vars(item))
            except TypeError:
                sanitized.append(item)
    return sanitized
