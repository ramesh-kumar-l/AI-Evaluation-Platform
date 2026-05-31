# ADR-0001 — Phase 0 Foundations

- **Status:** Accepted
- **Date:** 2026-05-31

## Context
Greenfield repo. We need a minimal, runnable, offline-first scaffold that the rest of the platform
can grow into without rework, and a memory bank as the source of truth.

## Decisions
1. **Monorepo** with `backend/`, `frontend/`, `infra/`, `docs/`, `project-memory-bank/`.
2. **Backend layering**: `api → services → models`; one concern per file; files < 300 lines.
3. **Offline-first config**: PostgreSQL+pgvector primary, **SQLite fallback** for zero-infra
   dev/tests so the app boots with no external services.
4. **Telemetry is opt-in**: OTel activates only when an OTLP endpoint is configured; otherwise no-op.
   Never blocks offline operation.
5. **Migrations-only schema**: Alembic is the only path for schema changes (baseline established in
   Phase 0; first tables in Phase 1). No runtime auto-create outside tests.
6. **Tooling**: `uv`, `ruff`, `mypy`, `pytest`; CI gates on all three checks.

## Consequences
- The scaffold boots and is testable before any domain logic exists.
- The SQLite fallback keeps dev frictionless but means Postgres-only features (pgvector) are guarded
  and exercised in Postgres-targeted contexts (from Phase 8).
- Strict modularity trades a few more files for far cheaper reads/edits later.
