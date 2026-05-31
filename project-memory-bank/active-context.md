# Active Context (save-state)

_Last updated: 2026-05-31_

## Where we are
- **Phase 0 — Foundations & Memory Bank: COMPLETE & verified.**
- **Phase 1 — Core Domain Model & Versioning: COMPLETE & verified (backend).**
- **Phase 2 — Provider Abstraction & Offline Execution: COMPLETE & verified (backend).**
- Next up: **Phase 3 — Evaluation Engine + Metrics** (STOP for review first, per protocol).

## What works right now
- Backend boots fully offline (SQLite fallback, no infra) — `uvicorn app.main:app`.
- Endpoints: `/health`, `/ready`, versioned CRUD-read for **providers, models, prompts, datasets**,
  `/audit/events`, `/audit/verify`, and **`POST/GET /runs`** (inference execution).
- Immutable versioning + hash-chained `AuditEvent` on every mutation.
- **Ollama adapter**: `POST /runs` renders the prompt template, calls Ollama `/api/generate`
  (stream=false), persists `InferenceRun` with full provenance (exact version IDs for prompt/model/
  provider, rendered prompt, raw output, latency, trace). Provider failures → `status="failed"` run
  persisted for audit; missing template variables → 422.
- Migrations: `a40763e31c9b` (5 entity tables) + `b3556b7705c3` (`inference_runs`).
- Quality gates green: **ruff, ruff format, mypy --strict, pytest (18 passed), alembic check clean**.

## How to run / verify (from `backend/`)
```
uv venv --python 3.12 .venv
uv pip install -e ".[dev]"
.venv/Scripts/python -m alembic upgrade head
.venv/Scripts/python -m pytest
.venv/Scripts/ruff check . ; .venv/Scripts/python -m mypy app
```

## Key decisions in play
- [[ADR-0001]] foundations; [[ADR-0002]] versioning + audit.
- `InferenceRun` is NOT `VersionedBase` — it is an immutable event record (written once, no revisions).
- Audit `record_event` normalises payloads via `json.loads(json.dumps(..., default=str))` so UUID
  and datetime values are stored as strings in the JSON column.

## Open threads / next-phase notes
- **Frontend shell** files exist but **not build-verified** (no Node/Rust toolchain; risk R6).
- **docker-compose** authored but not run here.
- Phase 3 needs: Metric model, Evaluation model, Run→Evaluation orchestration, metric catalog
  (exact-match, similarity), confidence levels, in-process fallback (no Temporal cluster needed).
- Concurrency note: audit hash chain uses last-seq lookup; fine for single-writer/offline.
  Revisit for concurrent writers before multi-user (Phase 11).
