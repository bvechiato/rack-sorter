"""Centralised configuration.

Paths and CORS can be overridden with environment variables so containers can mount
persistent volumes. Reading env vars at import is not a side effect.
"""

import os

DB_PATH = os.getenv("RS_DB_PATH", "search_eval.db")
UPLOADS_PATH = os.getenv("RS_UPLOADS_PATH", "service/static/uploads")
DINO_MODEL_ID = "facebook/dinov2-base"
CLIP_MODEL_ID = "patrickjohncyh/fashion-clip"
CORS_ORIGINS = os.getenv("RS_CORS_ORIGINS", "*")
# Load the ML models during lifespan instead of on the first request. Off by default
# so local dev and tests stay fast; the Docker image opts in.
WARM_MODELS = os.getenv("RS_WARM_MODELS", "0").lower() in ("1", "true", "yes")
# Persist the original upload bytes to disk (local/dev debugging only). Off by default:
# prod stores embeddings in the DB and never writes the image file. Opt in locally with
# RS_SAVE_UPLOAD_IMAGES=1.
SAVE_UPLOAD_IMAGES = os.getenv("RS_SAVE_UPLOAD_IMAGES", "0").lower() in ("1", "true", "yes")
