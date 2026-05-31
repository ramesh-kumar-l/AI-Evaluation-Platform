# AI Evaluation Platform (AEP)

> **System of record for AI quality. Can we safely deploy?**

AEP answers the hardest question in AI operations: given the latest model update, is the system
ready to ship? It does this through a complete evidence chain — versioned datasets and prompts,
scored evaluations, regression detection, and audited gate decisions with mandatory approvals.

**Offline-first. Trust-first. Governance-heavy.**

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136%2B-009688)](https://fastapi.tiangolo.com)
[![mypy strict](https://img.shields.io/badge/mypy-strict-brightgreen)](http://mypy-lang.org/)
[![Tests](https://img.shields.io/badge/tests-150%20passed-brightgreen)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

---

## Why AEP Exists

Teams ship AI systems without a trustworthy, reproducible way to answer *"is this safe to release?"*.
Ad-hoc evaluation scripts produce numbers nobody can reproduce, audit, or defend. AEP makes AI
quality a **system of record**: versioned inputs, reproducible evaluations, detected regressions,
and an auditable release gate with human approval — all runnable on a laptop with no internet.

---

## Key Capabilities

| Capability | Description |
|---|---|
| **Evaluation engine** | In-process scoring: exact_match, contains, semantic similarity (TF-cosine, no ML deps) |
| **RAG evaluation** | TF-IDF retrieval + context_relevance, faithfulness, answer_relevance scorers |
| **Agent evaluation** | Trajectory scoring: tool_call_accuracy (F1), trajectory_score (Dice-LCS), task_completion |
| **Regression detection** | Per-metric delta comparison with configurable thresholds |
| **Release gates** | Criteria-based gate decisions, mandatory approvals, audited overrides |
| **Continuous evaluation** | Cron schedules (APScheduler), A/B experiments, metric trend tracking |
| **API key auth + RBAC** | viewer / evaluator / approver / admin roles; sliding-window rate limiting |
| **Audit trail** | Hash-chained append-only log; tamper-evident verification endpoint |
| **Trust-first results** | Every evaluation carries full provenance: model/prompt/dataset/metric versions, confidence, approval status |
| **Offline-first** | Every workflow runs with Ollama + SQLite — zero cloud dependency |

---

## Quick Start (zero infra — works on any laptop)

```bash
git clone https://github.com/your-org/ai-evaluation-platform
cd ai-evaluation-platform/backend

# Create venv and install deps
uv venv --python 3.12 .venv
uv pip install -e ".[dev]"

# Run migrations (SQLite auto-created at backend/var/aep.db)
.venv/Scripts/python -m alembic upgrade head   # Windows
# OR: .venv/bin/python -m alembic upgrade head  # macOS/Linux

# Start the server
.venv/Scripts/uvicorn app.main:app --reload

# Open the interactive API explorer
open http://localhost:8000/docs

# Run the full test suite (150 tests, ~10s)
.venv/Scripts/python -m pytest
```

No `AEP_DATABASE_URL` needed — SQLite is used automatically. No Ollama needed to run tests.

---

## Full Local Stack (Postgres + pgvector)

```bash
docker compose -f infra/docker-compose.yml up --build
```

Starts: PostgreSQL 16 with pgvector, the backend API, and the frontend dev server.

---

## Repository Layout

```
backend/
  app/
    api/           HTTP routers (one file per domain, thin)
    core/          Config, logging, telemetry, auth, rate limiting
    models/        SQLAlchemy ORM (one entity per file, <300 lines)
    schemas/       Pydantic DTOs (one entity per file)
    services/      Business logic (one domain per file, <300 lines)
      metrics/     Metric scorer implementations
      providers/   LLM provider adapters (Ollama + registry)
  migrations/      Alembic migration chain (10 migrations, P0–P11)
  tests/           150 tests across all phases

frontend/
  src/
    app/           Layout, Router
    components/    Reusable UI components (EvaluationCard, TrustIndicator, etc.)
    lib/           API client, utilities
    pages/         Page-level components (one per domain)

infra/
  docker-compose.yml        Local dev stack
  docker-compose.prod.yml   Production hardened stack
  k8s/                      Kubernetes manifests (7 files)

docs/                        MkDocs documentation (index, architecture, API, deployment)
project-memory-bank/         Source of truth: ADRs, roadmap, governance, save-state
```

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│  React SPA (Vite + TypeScript + Tailwind + shadcn/ui)    │
└──────────────────────┬───────────────────────────────────┘
                       │ HTTP (X-API-Key auth)
┌──────────────────────▼───────────────────────────────────┐
│  FastAPI  ·  SecurityHeaders → RateLimit → RBAC          │
│  16 domain routers + health + admin                       │
└──────┬────────────┬──────────┬────────────────────────────┘
       │            │          │
  SQLAlchemy    Ollama      APScheduler
  (Alembic)    adapter      (soft dep)
       │
  PostgreSQL ←→ pgvector (production ANN)
  SQLite        (zero-infra offline fallback)
```

**Core architectural properties:**
- `api → services → models` — routers never touch the database directly
- Immutable versioning — every entity change creates a new row; lineage via `parent_id`
- Hash-chained audit log — tamper-evident; `sha256(prev_hash + payload)` on every mutation
- Offline-first — SQLite + Ollama replaces Postgres + cloud LLM for zero-infra dev
- mypy `--strict` on all 117 source files — no escape hatches

---

## Status

All phases P0–P11 complete. **150/150 tests · ruff ✅ · mypy --strict ✅ (117 files) · alembic check ✅**

| Phase | Description | Backend | Frontend |
|-------|-------------|---------|----------|
| P0 | Foundations & Memory Bank | ✅ | ✅ |
| P1 | Core Domain Model & Versioning | ✅ | ✅ |
| P2 | Provider Abstraction & Offline Execution | ✅ | ✅ |
| P3 | Evaluation Engine + Metrics | ✅ | ✅ |
| P4 | Trust-First Result UI | ✅ | 🟡 CI-gated |
| P5 | Comparison & Regression Detection | ✅ | 🟡 CI-gated |
| P6 | Release Gates & Approvals → **MVP** | ✅ | 🟡 CI-gated |
| P7 | Dataset & Benchmark Governance | ✅ | 🟡 CI-gated |
| P8 | RAG Evaluation | ✅ | 🟡 CI-gated |
| P9 | Agent & Tool Evaluation | ✅ | 🟡 CI-gated |
| P10 | Observability & Continuous Evaluation | ✅ | 🟡 CI-gated |
| P11 | Security, Governance, Docs & Deployment | ✅ | 🟡 CI-gated |

🟡 = authored, TypeScript + Vite build-verified in CI; live-test requires Node.js toolchain.

---

## Documentation

- [Architecture](./docs/architecture.md) — system diagram, domain model, migration chain
- [API Reference](./docs/api.md) — auth, roles, endpoint summary by domain
- [Deployment Guide](./docs/deployment.md) — local / Docker / Kubernetes, env vars
- [Newbie Quick Starter](./docs/NewbieQuickStarterGuide.md) — onboarding for new engineers
- [Dependency Rationale](./docs/dependency-rationale.md) — why each dependency was chosen
- [Project Memory Bank](./project-memory-bank/) — ADRs, roadmap, governance

---

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). The short version:

1. Read `project-memory-bank/active-context.md` and `implementation-status.md` first.
2. One concern per file, files under 300 lines.
3. All changes must pass: `ruff check .` · `mypy app` · `pytest` · `alembic check`.
4. New schema changes must come with an Alembic migration.

---

## License

MIT. See [LICENSE](./LICENSE).
