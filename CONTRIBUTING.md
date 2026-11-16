# Contributing

## No import-time side effects

Importing a module must not download a model, open a database connection, or print.
Construction happens in `lifespan` or on first use via a lazy getter (see
`service/rank.py::get_dino_model` and `service/identifier.py::get_clip_model`).

This keeps the test suite fast and importable without network access.

## Running checks locally

```bash
cd server && .venv/bin/python -m ruff check . && .venv/bin/python -m pytest tests -q
cd client && npm run lint && npm run typecheck && npm run build
```

Or install [pre-commit](https://pre-commit.com) and run `pre-commit install`.
PY