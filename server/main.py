import os
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routes import analyze, health, search

# Keep uvicorn's INFO logs, but drop the repetitive liveness/model-discovery probes
# that OpenCode and other local tools send to every localhost port.
class _ProbeNoiseFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        return "/health" not in message and "/v1/models" not in message


logging.getLogger("uvicorn.access").addFilter(_ProbeNoiseFilter())
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from service.eval_db import init

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

app.include_router(health.router)
app.include_router(analyze.router)
app.include_router(search.router)


@app.get("/")
async def serve_frontend():
    return FileResponse("index.html")


@app.get("/manifest.json")
async def serve_manifest():
    return FileResponse("manifest.json")
PY