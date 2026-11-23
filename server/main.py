import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routes import analyze, health, search
from config import CORS_ORIGINS, WARM_MODELS


# Keep uvicorn's INFO logs, but drop the repetitive liveness/model-discovery probes
# that OpenCode and other local tools send to every localhost port.
class _ProbeNoiseFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        return "/health" not in message and "/v1/models" not in message


logging.basicConfig(level=logging.INFO)

logging.getLogger("uvicorn.access").addFilter(_ProbeNoiseFilter())
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Schema is owned by Alembic; import here to keep module import side-effect free.
    from alembic import command
    from alembic.config import Config

    command.upgrade(Config(str(Path(__file__).with_name("alembic.ini"))), "head")

    if WARM_MODELS:
        # Best-effort: a failed download must not stop the app from serving /health.
        # The lazy getters will retry when a request actually needs the model.
        try:
            from service.identifier import get_clip_model, get_concept_embeddings
            from service.rank import get_dino_model, get_dino_processor

            get_dino_processor()
            get_dino_model()
            get_clip_model()
            get_concept_embeddings()
            logger.info("Models warmed; ready to serve")
        except Exception:
            logger.exception("Model warming failed; models will load lazily on first use")

    yield


app = FastAPI(title="RackSorter Unified Engine", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o for o in CORS_ORIGINS.split(",") if o],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
if os.path.exists("dist"):
    app.mount("/assets", StaticFiles(directory="dist/assets"), name="assets")

app.include_router(health.router)
app.include_router(analyze.router)
app.include_router(search.router)


@app.get("/")
async def serve_frontend():
    return FileResponse("index.html")


@app.get("/manifest.json")
async def serve_manifest():
    return FileResponse("manifest.json")
