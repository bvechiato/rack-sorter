"""Orchestration for a feedback request: persist, fetch more, rerank once.

Kept out of the HTTP layer so routers stay thin and the flow is reusable/testable.
"""

import logging

from api.models import FetchInitialResponse, FeedbackEvent
from model.mapper import to_ItemResponse
from model.repository.feedback import get_feedback_for_upload, insert_rerank_feedback
from service.pool import fetch_more_for_upload
from service.repository import get_results_by_upload_id
from service.rerank import rerank

logger = logging.getLogger(__name__)


def apply_feedback_and_rerank(
    upload_id: int,
    events: list[FeedbackEvent],
    fetch_more: bool,
) -> FetchInitialResponse:
    """Persist feedback, fetch one page, then rerank once."""
    if not events:
        raise ValueError("feedback must contain at least one event")

    for event in events:
        insert_rerank_feedback(upload_id, event.item_url, event.feedback_type, event.concept)
    logger.info("Inserted %d feedback event(s) for upload %d", len(events), upload_id)

    new_items = 0
    if fetch_more:
        try:
            new_items = fetch_more_for_upload(upload_id)
        except Exception as e:
            logger.warning("Fetch-more failed for upload %d: %s; ranking the existing pool", upload_id, e)

    previous_results = get_results_by_upload_id(upload_id)
    feedback_history = get_feedback_for_upload(upload_id)
    processed_items = rerank(previous_results, feedback_history, upload_id=upload_id)
    return FetchInitialResponse(pool=to_ItemResponse(processed_items), new_items=new_items)
