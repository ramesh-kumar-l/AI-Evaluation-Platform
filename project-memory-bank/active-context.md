# Active Context (save-state)

_Last updated: 2026-05-31_

## Where we are
- **Phase 0 — Foundations & Memory Bank: COMPLETE & verified.**
- **Phase 1 — Core Domain Model & Versioning: COMPLETE & verified (backend).**
- Next up: **Phase 2 — Provider Abstraction & Offline Execution** (STOP for review first, per protocol).

## What works right now
- Backend boots fully offline (SQLite fallback, no infra) — `uvicorn app.main:app`.
- Endpoints: `/health`, `/ready`, and versioned CRUD-read for **providers, models, prompts,
  datasets**, plus `/audit/events` and `/audit/verify`.
- Immutable versioning with lineage (`parent_id`) and `is_latest`; every mutation writes a
  hash-chained, tamper-evident `AuditEvent`.
- Alembic migration `a40763e31c9b` creates all 5 tables; `alembic check` reports no drift.
- Quality gates green: **ruff, ruff format, mypy --strict, pytest (8 passed)**.

## How to run / verify (from `backend/`)
```
uv venv --python 3.12 .venv
uv pip install --python .venv -e ".[dev]"
.venv/Scripts/python -m alembic upgrade head
.venv/Scripts/python -m pytest
.venv/Scripts/ruff check . ; .venv/Scripts/python -m mypy app
```

## Key decisions in play
- [[ADR-0001]] foundations; [[ADR-0002]] versioning + audit (incl. the scoping decision to build the
  versioning/audit *foundation* + the 3 exercisable entities now, and adopt the same `VersionedBase`
  for remaining entities in their owning phases).

## Open threads / next-phase notes
- **Frontend shell** files exist (Vite+React+TS+Tauri+Tailwind+tokens) but are **not build-verified**
  here — no Node/Rust toolchain was run (risk R6). Verify on a machine with the toolchain.
- **docker-compose** (Postgres+pgvector + api + frontend) is authored but not run here; verify
  `docker compose -f infra/docker-compose.yml up` on a Docker host.
- Provider/Model versioned records exist, but **no execution** yet — that's Phase 2 (Ollama adapter,
  deterministic Run capture).
- Concurrency note: the audit hash chain uses last-seq lookup; fine for single-writer/offline. Revisit
  for concurrent writers before multi-user (Phase 11).
