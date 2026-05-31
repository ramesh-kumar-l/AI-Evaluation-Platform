# System Patterns

## Monorepo layout
```
ai-evaluation-platform/
├── backend/                 # FastAPI service (Python)
│   ├── app/
│   │   ├── core/            # config, logging, telemetry, db
│   │   ├── api/             # routers (thin; one concern per file)
│   │   ├── models/          # SQLAlchemy ORM (one entity per file)
│   │   ├── schemas/         # Pydantic DTOs (one entity per file)
│   │   └── services/        # business logic (one domain per file)
│   ├── migrations/          # Alembic
│   └── tests/
├── frontend/                # React + TS + Vite + Tauri + Tailwind + shadcn/ui
│   └── src/{app,components,lib,styles}
├── infra/                   # docker-compose, env templates
├── docs/                    # MkDocs (later)
└── project-memory-bank/     # source of truth (this folder)
```

## Strict modularity rule
- **Files stay under 300 lines.** A growing `services.py` is split by domain
  (`dataset_service.py`, `prompt_service.py`, …). One concern per file so any single file can be
  read in isolation.

## Backend layering
`api` (HTTP, validation) → `services` (business rules, versioning, audit) → `models` (persistence).
Routers never touch the DB session directly beyond dependency injection; services own transactions.

## Offline-first pattern
- Config resolves a **local Postgres** by default; **SQLite fallback** for zero-infra dev/tests.
- Telemetry/OTel is **no-op unless** an OTLP endpoint is configured — never blocks offline runs.
- No outbound network call is on any critical path.

## Trust & audit patterns (foundations; deepened in Phase 1)
- **Immutable versioning:** entities are versioned; a new version is a new row, never an in-place
  edit. Lineage via `parent_id`.
- **Append-only audit:** every mutation emits an `AuditEvent`; the log is never updated or deleted.

## Configuration
- 12-factor: all config via environment variables, typed via Pydantic `Settings`.
- `.env.example` documents every variable; secrets never committed.
