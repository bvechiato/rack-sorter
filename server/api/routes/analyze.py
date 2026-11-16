from fastapi import APIRouter, HTTPException, UploadFile, File

from api.models import AnalyseAnchorImageResponse, AnalyseResponse
from service.identifier import extract_tags_from_image
from service.eval_db import save_user_upload

router = APIRouter()


@router.post("/analyze", response_model=AnalyseAnchorImageResponse)
async def analyze_anchor_image(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        analysis_payload = extract_tags_from_image(contents)
        upload_id = save_user_upload(contents, analysis_payload)
        return AnalyseAnchorImageResponse(
            upload_id=upload_id,
            analysis=AnalyseResponse(**analysis_payload),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis crashed: {str(e)}")