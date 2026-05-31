# Tech Context

## Backend
- **Python 3.12+** (dev host currently 3.14). **FastAPI** + **Uvicorn**.
- **Pydantic v2** (models + `pydantic-settings` for config).
- **SQLAlchemy 2.x** ORM + **Alembic** migrations.
- **PostgreSQL 16 + pgvector** (primary); **SQLite** fallback for offline/dev/tests.
- **structlog** for structured JSON logging.
- **OpenTelemetry SDK** skeleton — active only when `OTEL_EXPORTER_OTLP_ENDPOINT` is set.
- Tooling: **uv** (env/deps), **ruff** (lint+format), **mypy** (types), **pytest** (tests).

## Frontend
- **React 18 + TypeScript + Vite**.
- **Tauri** for desktop/offline packaging.
- **Tailwind CSS** + **shadcn/ui** (design tokens defined in Phase 0).
- Planned (later phases): TanStack Query, Zustand, Framer Motion, React Hook Form, Zod.

## AI providers
- **Ollama** — mandatory, offline. Default base URL `http://localhost:11434`.
- OpenAI / Anthropic / Google / OpenRouter — optional, feature-flagged adapters (Phase 2+).

## Workflows / observability (later phases)
- **Temporal** for orchestration, with an **in-process fallback** so offline dev needs no cluster
  (Phase 3).
- Prometheus / Grafana / Langfuse (Phase 10).

## Deployment
- **Docker** + **docker-compose** for local; **Kubernetes** for hardened deploy (Phase 11).

## Conventions
- Config via env vars only (see `backend/.env.example`).
- Migrations are the only way schema changes land; no auto-create in non-test environments.
- CI gates: ruff, mypy, pytest must pass.
