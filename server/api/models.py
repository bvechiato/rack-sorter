from pydantic import BaseModel
from typing import Literal, Optional

from service.traits import Trait

class FetchInitialRequest(BaseModel):
    uploadId: int
    keyword: str
    selectedSizes: str
    selectedCategory: str
    selectedColors: str
    maxPrice: str
    selectedConditions: str

class ItemResponse(BaseModel):
    title: str
    url: str
    image_url: str
    similarity_score: float
    rerank_score: Optional[float] = None

class FetchInitialResponse(BaseModel):
    pool: list[ItemResponse]
    # Items appended by the last rerank's extra catalogue page (0 on a fresh search).
    new_items: int = 0

class AnalyseResponse(BaseModel):
    archetype: str
    classified_tags: list[str]
    colour_archetype: str
    colour_classified_tags: list[str]
    category_archetype: str

class AnalyseAnchorImageResponse(BaseModel):
    upload_id: int
    analysis: AnalyseResponse

class RerankRequest(BaseModel):
    upload_id: int
    item_url: str
    feedback_type: Literal["MORE", "LESS"]
    concept: Optional[Trait] = None
    # Pull one extra catalogue page before ranking; disable for offline/debug replays.
    fetch_more: bool = True

class FeedbackEvent(BaseModel):
    """One queued trait/visual choice, sent when the sheet is dismissed with Done."""
    item_url: str
    feedback_type: Literal["MORE", "LESS"]
    concept: Optional[Trait] = None

class BatchRerankRequest(BaseModel):
    upload_id: int
    # Applied as one unit: one extra page is fetched and one rerank is returned, so the
    # client refreshes exactly once no matter how many traits were queued.
    feedback: list[FeedbackEvent]
    fetch_more: bool = True

class ItemComparisonRequest(BaseModel):
    upload_id: int
    item_clicked_url: str

class ItemComparisonResponse(BaseModel):
    distinguishing_characteristics: list[str]


class TraitProfileResponse(BaseModel):
    """Raw axis projections plus the pool spread the scorer standardises against."""

    count: int
    top_n: int
    mean: dict[str, float]
    std: dict[str, float]
    anchor: dict[str, float]
    top: dict[str, float]
    item: Optional[dict[str, float]] = None