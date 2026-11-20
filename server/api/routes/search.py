import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException

from api.models import (
    BatchRerankRequest,
    FeedbackEvent,
    FetchInitialRequest,
    FetchInitialResponse,
    RerankRequest,
    TraitProfileResponse,
)
from model.mapper import to_ItemResponse
from model.repository.search_items import SearchItem
from service.eval_db import save_query_to_db
from service.feedback_flow import apply_feedback_and_rerank
from service.pool import reset_page_cursor
from service.profile import build_trait_profile
from service.rank import process_and_rank_pool
from service.scraper import build_query_params, scrape_vinted_pool

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/fetch_initial")
async def fetch_initial(bg_tasks: BackgroundTasks, request: FetchInitialRequest) -> FetchInitialResponse:
    query_params = build_query_params(request)
    logger.info("Constructed Query Parameters: %s", query_params)
    items: set[SearchItem] = scrape_vinted_pool(query_params)
    processed_items = process_and_rank_pool(items, request.uploadId)
    bg_tasks.add_task(
        save_query_to_db, request.uploadId, request.keyword.replace(" ", "+"), query_params, processed_items
    )
    reset_page_cursor(request.uploadId)
    return FetchInitialResponse(pool=to_ItemResponse(processed_items))


@router.post("/rerank")
async def rerank_pool(request: RerankRequest):
    logger.info(
        "Received rerank request: TYPE=%s ON=%s %s Upload=%d",
        request.feedback_type,
        request.concept,
        request.item_url,
        request.upload_id,
    )
    try:
        return apply_feedback_and_rerank(
            request.upload_id,
            [
                FeedbackEvent(
                    item_url=request.item_url,
                    feedback_type=request.feedback_type,
                    concept=request.concept,
                )
            ],
            request.fetch_more,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reranking crashed: {str(e)}")


@router.post("/rerank_batch")
async def rerank_batch(request: BatchRerankRequest):
    logger.info("Received batch rerank: %d event(s) for upload %d", len(request.feedback), request.upload_id)
    try:
        return apply_feedback_and_rerank(request.upload_id, request.feedback, request.fetch_more)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reranking crashed: {str(e)}")


@router.get("/trait-profile")
async def trait_profile(upload_id: int, item_url: str | None = None) -> TraitProfileResponse:
    """Debug view: where the anchor and the current top results sit on every trait axis."""
    try:
        return TraitProfileResponse(**build_trait_profile(upload_id, item_url))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trait profile failed: {str(e)}")
