# syntax=docker/dockerfile:1

# Stage 1: build the React app. `vite build` does not need a running server
# (type generation only happens in `npm run dev`).
FROM node:20-alpine AS client-build
WORKDIR /client
COPY client/package.json client/package-lock.json ./
RUN npm ci
COPY client/ ./
RUN npm run build

# Stage 2: FastAPI serves both the API and the built app, from its working directory.
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/app/.cache/huggingface \
    RS_DB_PATH=/app/data/search_eval.db \
    RS_UPLOADS_PATH=/app/data/uploads

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/server
COPY server/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY server/ ./
COPY --from=client-build /client/dist/ /app/server/dist/
COPY --from=client-build /client/dist/index.html /app/server/index.html
COPY --from=client-build /client/manifest.json /app/server/manifest.json

RUN mkdir -p /app/data /app/data/uploads /app/.cache/huggingface

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=300s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health').read()"

# Single process: the page cursor, CLIP anchor cache and SQLite writer are process-local.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
