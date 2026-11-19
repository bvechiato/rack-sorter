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

## Flow docs check

CI has one narrow rule: if a PR changes `server/api/`, `server/main.py`, or `client/src/api.ts`, it must also change `docs/flows/README.md`. Run it locally against your base branch:

```bash
python3 scripts/check_flows.py --diff-base origin/main
```

Add `[skip-flows]` to the PR description only when the change truly has no flow impact. The check is a coupling proxy, not a diagram validator; keeping the README accurate is still the job of the rule in `AGENTS.md`.
