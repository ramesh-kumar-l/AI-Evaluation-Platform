# Implementation Status (save-state)

_Last updated: 2026-05-31_

## Legend
✅ done & verified · 🟡 authored, not verified here · ⬜ not started

## Phase 0 — Foundations & Memory Bank ✅
| Item | Status | Notes |
|------|--------|-------|
| Memory bank seeded (brief, product, system, tech, progress, active, impl-status) | ✅ | source of truth |
| Governance folders (ADRs, evaluations, dataset/benchmark/metric/release gov, frontend-design, risk) | ✅ | READMEs + ADR-0001/0002 + risk register |
| Monorepo layout (backend/frontend/infra/docs/memory) | ✅ | |
| FastAPI app skeleton + health/ready | ✅ | offline-first |
| Config (env-driven, Postgres + SQLite fallback) | ✅ | `app/core/config.py` |
| Structured logging (structlog) | ✅ | `app/core/logging.py` |
| OpenTelemetry skeleton (opt-in, no-op offline) | ✅ | `app/core/telemetry.py` |
| Alembic baseline | ✅ | `migrations/`, env wired to settings |
| Docker (backend Dockerfile, docker-compose pg+pgvector) | 🟡 | authored; not run on a Docker host here |
| Frontend shell (Vite+React+TS+Tauri+Tailwind+shadcn tokens) | 🟡 | authored; no Node/Rust build run (R6) |
| CI (ruff + mypy + pytest; frontend typecheck+build) | ✅ | `.github/workflows/ci.yml`; gates pass locally |

## Phase 1 — Core Domain Model & Versioning ✅ (backend)
| Item | Status | Notes |
|------|--------|-------|
| `VersionedMixin` + abstract `VersionedBase` (immutable versioning + lineage) | ✅ | `app/models/mixins.py` |
| Entities: Provider, Model, Prompt, Dataset | ✅ | one file each, < 300 lines |
| Append-only, hash-chained `AuditEvent` | ✅ | `app/models/audit_event.py` |
| Audit service (`record_event`, `verify_chain`) | ✅ | tamper-evident; tested |
| Generic versioning service (PEP 695 generics) | ✅ | `app/services/versioning.py` |
| Per-domain services (provider/prompt/dataset) | ✅ | thin; strict modularity |
| Pydantic schemas (versioned-out exposes all version/lineage fields) | ✅ | `app/schemas/` |
| API routers (versioned create/revise/read + audit) | ✅ | `app/api/` |
| Migration `a40763e31c9b` (5 tables) + no drift | ✅ | `alembic check` clean |
| Tests: versioning/lineage, item_count, 404, audit chain + tamper | ✅ | 8 passed |

### Phase 1 entities deferred to owning phases (per ADR-0002)
⬜ Benchmark (P7) · ⬜ Metric (P3) · ⬜ Evaluation/Run/Result (P2–P3) · ⬜ Approval/ReleaseGate (P6).
All will reuse `VersionedBase` + the audit service — no retrofit needed.

## Phase 2 — Provider Abstraction & Offline Execution ✅ (backend)
| Item | Status | Notes |
|------|--------|-------|
| `ProviderAdapter` Protocol + `InferenceRequest`/`InferenceResponse` dataclasses | ✅ | `app/services/providers/base.py` |
| `OllamaAdapter` (HTTP, offline-first, `/api/generate`) | ✅ | `app/services/providers/ollama.py` |
| Adapter registry (`get_adapter(kind, base_url)`) | ✅ | `app/services/providers/registry.py` |
| `InferenceRun` model (immutable event, not versioned) | ✅ | `app/models/run.py` |
| `run_service.execute_run` (render prompt, call adapter, persist + audit) | ✅ | provider failures → status="failed", not 5xx |
| Run schemas (`RunCreate`, `RunOut`) | ✅ | `app/schemas/run.py` |
| Runs API (`POST /runs`, `GET /runs`, `GET /runs/{id}`) | ✅ | `app/api/runs.py` |
| Migration `b3556b7705c3` (`inference_runs` table + 3 indexes) | ✅ | `alembic check` clean |
| Audit bugfix: UUID→str in JSON payload | ✅ | `audit.record_event` normalises via json round-trip |
| Tests (success, offline-fail, missing-var 422, not-found 404, list/filter, audit event) | ✅ | 18/18 passed |

## Phases 3–11 ⬜ Not started
See [progress.md](./progress.md). **STOP for review before starting Phase 3.**
