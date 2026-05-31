# AI Evaluation Platform (AEP)

The **system of record for AI quality** — benchmarking, regression detection, release assurance, and
deployment trust. It answers one question: **"Can we safely deploy?"**

Offline-first, trust-first, governance-heavy. See [`project-memory-bank/`](./project-memory-bank/)
for the authoritative project context, the phased roadmap, and the current save-state.

## Repository layout
```
backend/             FastAPI service (Python) — API, services, models, migrations
frontend/            React + TS + Vite + Tauri + Tailwind shell
infra/               docker-compose (Postgres+pgvector, API, frontend)
docs/                documentation (MkDocs, later phases)
project-memory-bank/ source of truth: context, roadmap, governance, save-state
```

## Quick start (backend, zero infra / offline)
```bash
cd backend
uv venv && uv pip install -e ".[dev]"
uv run uvicorn app.main:app --reload      # http://localhost:8000/health
uv run pytest
```
With no `AEP_DATABASE_URL` set, the backend uses a local SQLite fallback — no database server
required. See `backend/.env.example` for Postgres and other settings.

## Full local stack (Postgres+pgvector + API + frontend)
```bash
docker compose -f infra/docker-compose.yml up --build
```

## Status
**Phase 0 — Foundations & Memory Bank.** See
[`project-memory-bank/implementation-status.md`](./project-memory-bank/implementation-status.md).
