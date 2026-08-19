# Community Intelligence

Market intelligence for the video-game industry, built from **player voice** —
what players actually say in open communities (Reddit, Steam reviews), structured
into a queryable graph of signals and trends.

We don't answer "how many copies sold" — we answer *"why are players angry / what do
they want / what is rising"*.

## Pipeline

```
collectors → Postgres (raw signals) → LLM processing → Neo4j (graph) → API / dashboard
  Reddit         games + signals         topics+sentiment      insights          output
  Steam
```

## Repository layout

- `docs/architecture.md` — full system architecture (data model, levels 1–3, tech stack).
- `SPEC.md` — original (Russian) architecture spec; superseded by `docs/architecture.md`.
- `openspec/specs/` — the **spec** (source of truth): each capability is a set of
  requirements + scenarios. This is the contract the implementation follows.
- `openspec/config.yaml` — project context injected into the spec-driven workflow.

## Specs (OpenSpec)

This project uses [OpenSpec](https://github.com/Fission-AI/OpenSpec) — spec-driven
development. The spec lives in `openspec/specs/`; each capability maps to a roadmap
item (CI-1…CI-6):

| Capability | Roadmap | What it defines |
|---|---|---|
| `games-catalog` | CI-1 | Postgres `games` table + name matching |
| `steam-collector` | CI-2 | Steam reviews + metadata ingestion |
| `reddit-collector` | CI-3 | Reddit mention search via Arctic Shift |
| `signal-processing` | CI-4 | LLM topic + sentiment extraction (DeepSeek-V3) |
| `knowledge-graph` | CI-5 | Neo4j nodes/edges + time series |
| `api-dashboard` | CI-6 | JSON API: sentiment trend + top-5 pains |

## Tech stack

Python 3.13 · FastAPI · PostgreSQL · Neo4j · Docker · **DeepSeek-V3 (LLM)** ·
Arctic Shift (Reddit) · Steam storefront / appreviews APIs.

## Development

```bash
# 1. Create a virtualenv and install dependencies (Python 3.13)
uv venv .venv
uv pip install --python .venv/bin/python "psycopg[binary]>=3.2" "pytest>=8.3"

# 2. Apply migrations (reads DEV_POSTGRES_URL)
.venv/bin/python -m catalog.migrate

# 3. Seed the catalog (10-20 games, idempotent)
.venv/bin/python -m catalog.seed

# 4. Run tests
.venv/bin/python -m pytest
```

The database connection comes from the `DEV_POSTGRES_URL` environment variable.
Integration tests skip automatically when the database is unavailable.
