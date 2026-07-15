from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
from contextlib import asynccontextmanager

from api.models import *
from api.errors import ServerError
from repository.search_items import SearchItem
from service.scraper import scrape_vinted_pool
from service.rerank import rerank
from service.rank import process_and_rank_pool
from service.identifier import extract_tags_from_image
from service.static.CONSTANTS import COLOUR_MAP, VINTED_CATEGORY_MAP
from service.eval_db import save_query_to_db, init, save_user_upload
from service.repository import get_results_by_upload_id
from repository.feedback import insert_rerank_feedback, get_feedback_for_upload


def _serialize_items(items) -> list[ItemResponse]:
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = init()
    conn.close()
    yield

app = FastAPI(title="RackSorter Unified Engine", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
if os.path.exists("dist"):
    app.mount("/assets", StaticFiles(directory="dist/assets"), name="assets")

@app.get("/")
async def serve_frontend():
    return FileResponse("index.html")

@app.get("/manifest.json")
async def serve_manifest():
    return FileResponse("manifest.json")

@app.post("/analyze", response_model=AnalyseAnchorImageResponse)
async def analyze_anchor_image(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        analysis_payload = extract_tags_from_image(contents)
        upload_id = save_user_upload(contents, analysis_payload)
        
        return AnalyseAnchorImageResponse(
            upload_id=upload_id, 
            analysis=AnalyseResponse(**analysis_payload)
        )
    except Exception as e:
        return ServerError(message=f"Analysis crashed: {str(e)}")

@app.post("/fetch_initial")
async def fetch_initial(bg_tasks: BackgroundTasks, request: FetchInitialRequest) -> FetchInitialResponse:
    keyword = request.keyword.replace(' ', '+')
    catalog_id = VINTED_CATEGORY_MAP.get(request.selectedCategory, "")
    colour_ids = []
    for c_name in request.selectedColors.split(","):
        if c_name in COLOUR_MAP.keys():
            colour_ids.extend(COLOUR_MAP.get(c_name))

    query_params = f"search_text={keyword}"
    if catalog_id:
        query_params += f"&catalog[]={catalog_id}"
    if colour_ids:
        for c_id in colour_ids:
            query_params += f"&color_ids[]={c_id}"
    if request.selectedSizes:
        for size_id in request.selectedSizes.split(","):
            query_params += f"&size_ids[]={size_id}"
    if request.maxPrice:
        query_params += f"&price_to={request.maxPrice}&currency=GBP"
    if request.selectedConditions:
        for cid in request.selectedConditions.split(","):
            if cid:
                query_params += f"&status_ids[]={cid}"

    print(f"\n[INFO] Constructed Query Parameters: {query_params}")
    items: set[SearchItem] = scrape_vinted_pool(query_params)

    processed_items = process_and_rank_pool(items, request.uploadId)

    bg_tasks.add_task(save_query_to_db, request.uploadId, keyword, query_params, processed_items)
    return FetchInitialResponse(pool=_serialize_items(processed_items))

@app.post("/rerank")
async def rerank_pool(bg_tasks: BackgroundTasks, request: RerankRequest):
    print(f"\n[INFO] Received rerank request: {request.feedback_type} for item: {request.item_url} on upload ID: {request.upload_id}")
    try:
        insert_rerank_feedback(request.upload_id, request.item_url, request.feedback_type)
        
        previous_results = get_results_by_upload_id(request.upload_id)
        feedback_history = get_feedback_for_upload(request.upload_id)

        processed_items = rerank(previous_results, feedback_history, upload_id=request.upload_id)
        return FetchInitialResponse(pool=_serialize_items(processed_items))
    except Exception as e:
        return ServerError(message=f"Reranking crashed: {str(e)}")