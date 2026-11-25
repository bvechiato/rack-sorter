from typing import Literal, Optional

from pydantic import BaseModel

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
    """One queued trait/visual choice, sent when the sheet is dismissed with Done.

    For aesthetic events (``aesthetic`` set) the lane is absolute: the phrase carries
    the intent, so ``feedback_type`` is required for wire compatibility but is not
    used by the aesthetic lane.
    """

    item_url: str
    feedback_type: Literal["MORE", "LESS"]
    concept: Optional[Trait] = None
    aesthetic: Optional[str] = None


class BatchRerankRequest(BaseModel):
    upload_id: int
    # Applied as one unit: one extra page is fetched and one rerank is returned, so the
    # client refreshes exactly once no matter how many traits were queued.
    feedback: list[FeedbackEvent]
    fetch_more: bool = True


class UndoFeedbackRequest(BaseModel):
    upload_id: int
    # Undo never pulls an extra catalogue page; it only removes the last steering event
    # and re-ranks the existing pool, keeping add-then-undo cadence-neutral.
    fetch_more: bool = False


class TraitProfileResponse(BaseModel):
    """Raw axis projections plus the pool spread the scorer standardises against."""

    count: int
    mean: dict[str, float]
    std: dict[str, float]
    anchor: dict[str, float]
    item: Optional[dict[str, float]] = None
