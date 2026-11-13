from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe; cheap and independent of the models/database."""
    return {"status": "ok"}
