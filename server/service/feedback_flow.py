"""Orchestration for a feedback request: persist, fetch more, rerank once.

Kept out of the HTTP layer so routers stay thin and the flow is reusable/testable.
"""

import logging

from api.models import FeedbackEvent, FetchInitialResponse
from model.mapper import to_ItemResponse
from model.repository.feedback import (
    delete_last_feedback_for_upload,
    get_feedback_for_upload,
    insert_rerank_feedback,
)
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
        insert_rerank_feedback(upload_id, event.item_url, event.feedback_type, event.concept, event.aesthetic)
    logger.info("Inserted %d feedback event(s) for upload %d", len(events), upload_id)

    if fetch_more:
        try:
            fetch_more_for_upload(upload_id)
        except Exception as e:
            logger.warning("Fetch-more failed for upload %d: %s; ranking the existing pool", upload_id, e)

    previous_results = get_results_by_upload_id(upload_id)
    feedback_history = get_feedback_for_upload(upload_id)
    processed_items = rerank(previous_results, feedback_history, upload_id=upload_id)
    return FetchInitialResponse(pool=to_ItemResponse(processed_items))


def undo_feedback_and_rerank(upload_id: int) -> FetchInitialResponse:
    """Delete the last feedback event for an upload, then re-rank with remaining history.

    Undo never fetches more catalogue pages: it only removes the most recent steering
    event and re-ranks the existing pool, so add-then-undo stays cadence-neutral
    (no fetch-more slot consumed).
    """
    deleted = delete_last_feedback_for_upload(upload_id)
    if not deleted:
        raise ValueError("no feedback to undo")
    logger.info("Undid last feedback for upload %d", upload_id)

    previous_results = get_results_by_upload_id(upload_id)
    feedback_history = get_feedback_for_upload(upload_id)
    processed_items = rerank(previous_results, feedback_history, upload_id=upload_id)
    return FetchInitialResponse(pool=to_ItemResponse(processed_items))
