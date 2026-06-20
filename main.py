import json
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
from contextlib import asynccontextmanager

from backend.api.models import *
from backend.service.scraper import scrape_vinted_pool
from backend.service.vector_engine import extract_tags_from_image, rank_pool_by_sliders
from backend.service.static.CONSTANTS import COLOUR_MAP, VINTED_CATEGORY_MAP
from backend.service.eval_db import save_query_to_db, init, save_user_upload

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
        return JSONResponse(status_code=500, content={"message": str(e)})
   
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

    print(f"\n[INFO] Constructed Query Parameters: {query_params}\n")
    items = scrape_vinted_pool(query_params)
    bg_tasks.add_task(save_query_to_db, request.uploadId, keyword, query_params, items)
    return FetchInitialResponse(pool=items)

@app.post("/rerank")
async def rerank_pool(pool_data: list, weights: str = Form(...)):
    try:
        parsed_weights = json.loads(weights)
        ranked_feed = rank_pool_by_sliders(pool_data, parsed_weights)
        return ranked_feed
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Reranking crashed: {str(e)}"})