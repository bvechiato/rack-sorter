# Centralised configuration. Edit these values directly; no logic, no secrets.

import os

DB_PATH = "search_eval.db"
UPLOADS_PATH = "service/static/uploads"
DINO_MODEL_ID = "facebook/dinov2-base"
CLIP_MODEL_ID = "patrickjohncyh/fashion-clip"
CORS_ORIGINS = "*"

# Persist the original upload bytes to disk (local/dev debugging only). Off by default:
# prod stores embeddings in the DB and never writes the image file. Opt in locally with
# RS_SAVE_UPLOAD_IMAGES=1. Reading an env var at import is not a side effect.
SAVE_UPLOAD_IMAGES = os.getenv("RS_SAVE_UPLOAD_IMAGES", "0").lower() in ("1", "true", "yes")
