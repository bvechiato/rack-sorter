import json
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Optional

from backend.scraper import scrape_vinted_pool
from backend.vector_engine import extract_tags_from_image, rank_pool_by_sliders
from static.CONSTANTS import VINTED_CATEGORY_MAP, VINTED_COLOUR_MAP

app = FastAPI(title="RackSorter Unified Engine")

# Permit local area connections across your network
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

@app.get("/")
async def serve_frontend():
    return FileResponse("index.html")

@app.get("/manifest.json")
async def serve_manifest():
    return FileResponse("manifest.json")

@app.post("/analyze")
async def analyze_anchor_image(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        analysis_payload = extract_tags_from_image(contents)
        return analysis_payload
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Analysis crashed: {str(e)}"})

@app.post("/fetch_initial")
async def fetch_initial(
    keyword: str = Form(...),
    size_id: Optional[str] = Form(None),
    category_name: str = Form("All clothes"),
    colour_name: str = Form(""),
    max_price: Optional[str] = Form(None),
    condition_id: Optional[List[str]] = Form(default=None)
):
    catalog_id = VINTED_CATEGORY_MAP.get(category_name, "")
    color_id = VINTED_COLOUR_MAP.get(colour_name, "")

    query_params = f"search_text={keyword}"
    if catalog_id:
        query_params += f"&catalog[]={catalog_id}"
    if color_id:
        query_params += f"&color_ids[]={color_id}"
    if size_id:
        query_params += f"&size_ids[]={size_id}"
    if max_price:
        query_params += f"&price_to={max_price}&currency=GBP"
    if condition_id:
        for cid in condition_id:
            if cid:
                query_params += f"&status_ids[]={cid}"

    items = scrape_vinted_pool(keyword, query_params)
    return {"pool": items}

@app.post("/rerank")
async def rerank_pool(pool_data: list, weights: str = Form(...)):
    try:
        parsed_weights = json.loads(weights)
        ranked_feed = rank_pool_by_sliders(pool_data, parsed_weights)
        return ranked_feed
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Reranking crashed: {str(e)}"})