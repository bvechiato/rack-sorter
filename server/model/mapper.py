from api.models import *

def to_ItemResponse(items) -> list[ItemResponse]:
    serialized = []
    for item in items:
        if isinstance(item, dict):
            title = item.get("title", "")
            url = item.get("url", "")
            image_url = item.get("image_url", "") or ""
            similarity_score = item.get("similarity_score", item.get("rerank_score", 0.0))
        else:
            title = getattr(item, "title", "")
            url = getattr(item, "url", "")
            image_url = getattr(item, "image_url", "") or ""
            similarity_score = getattr(item, "similarity_score", None)
            if similarity_score is None:
                similarity_score = getattr(item, "rerank_score", 0.0)

        serialized.append(
            ItemResponse(
                title=title,
                url=url,
                image_url=image_url,
                similarity_score=float(similarity_score or 0.0),
            )
        )
    return serialized