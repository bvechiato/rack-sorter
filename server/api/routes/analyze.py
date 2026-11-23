from fastapi import APIRouter, File, HTTPException, UploadFile

from api.models import AnalyseAnchorImageResponse, AnalyseResponse
from service.eval_db import save_user_upload
from service.identifier import extract_tags_from_image

router = APIRouter()


@router.post("/analyze", response_model=AnalyseAnchorImageResponse)
async def analyze_anchor_image(file: UploadFile = File(...)):
    try:
        # Local imports keep model loading out of module import time.
        from service.identifier import get_single_clip_embedding
        from service.rank import process_and_normalise

        contents = await file.read()
        analysis_payload = extract_tags_from_image(contents)

        # Persist both anchor vectors at upload time: the image file is optional (dev only),
        # so downstream ranking/trait steering must not depend on re-reading it.
        dino_embedding = process_and_normalise(contents).squeeze().numpy().tolist()
        clip_embedding = get_single_clip_embedding(contents).tolist()
        upload_id = save_user_upload(contents, analysis_payload, dino_embedding, clip_embedding)
        return AnalyseAnchorImageResponse(
            upload_id=upload_id,
            analysis=AnalyseResponse(**analysis_payload),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis crashed: {str(e)}")
