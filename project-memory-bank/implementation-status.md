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

## Phase 3 — Evaluation Engine + Metrics ✅ (backend)
| Item | Status | Notes |
|------|--------|-------|
| `Metric` entity (VersionedBase) — name, description, kind, config | ✅ | `app/models/metric.py` |
| `Evaluation` model (immutable event) — full provenance + aggregate_scores | ✅ | `app/models/evaluation.py` |
| `EvaluationResult` model (immutable event) — per-item score record | ✅ | `app/models/evaluation_result.py` |
| Metric scorer Protocol + `MetricInput`/`MetricScore` dataclasses | ✅ | `app/services/metrics/base.py` |
| `ExactMatchMetric` — normalized string equality, confidence "high" | ✅ | `app/services/metrics/exact_match.py` |
| `ContainsMetric` — substring search, confidence "medium" | ✅ | `app/services/metrics/contains.py` |
| `SemanticSimilarityMetric` — pure-Python TF cosine, no ML deps, confidence "low" | ✅ | `app/services/metrics/semantic_sim.py` |
| Metric scorer registry (`get_scorer(kind)`) | ✅ | `app/services/metrics/registry.py` |
| `metric_service` — thin CRUD over versioning service | ✅ | `app/services/metric_service.py` |
| `evaluation_service.execute_evaluation` — in-process orchestration, no Temporal | ✅ | provider fails → `status="partial/failed"` |
| Metrics API (`POST/GET /metrics`, `/{key}`, `/{key}/versions`) | ✅ | `app/api/metrics.py` |
| Evaluations API (`POST/GET /evaluations`, `/{id}`, `/{id}/results`) | ✅ | `app/api/evaluations.py` |
| Migration `a8a557afd538` (metrics + evaluations + evaluation_results tables) | ✅ | `alembic check` clean |
| Tests (metric CRUD, exact_match/contains/similarity, provenance, filter, errors) | ✅ | 33/33 passed |

## Phase 4 — Trust-First Result UI 🟡 (frontend — authored, not build-verified)
| Item | Status | Notes |
|------|--------|-------|
| `src/types/index.ts` — all API response types | 🟡 | Health, Evaluation, Metric, Dataset, AuditEvent, EvaluationResult |
| `src/lib/api.ts` — full API client | 🟡 | getHealth, listEvaluations, getEvaluation, getEvaluationResults, listMetrics, getMetric, listDatasets, listAuditEvents |
| `src/lib/utils.ts` — formatting helpers | 🟡 | shortId, formatDate, formatScore, scoreColor, confidenceVariant, statusVariant |
| `src/components/ui/Badge.tsx` — semantic status badge | 🟡 | trust/warning/danger/muted variants |
| `src/components/ui/Card.tsx` — card with header/body | 🟡 | primitive container |
| `src/components/ui/Spinner.tsx` — loading indicator | 🟡 | accessible, animated |
| `src/components/TrustIndicator.tsx` — confidence badge | 🟡 | high(●)/medium(◑)/low(○) with semantic color |
| `src/components/MetricCard.tsx` — metric result card | 🟡 | name, kind, mean_score, confidence distribution, version ID |
| `src/components/EvaluationCard.tsx` — evaluation summary | 🟡 | status, provenance IDs, link to detail |
| `src/components/AuditTimeline.tsx` — hash-chained event list | 🟡 | hash fingerprints, seq, actor, action |
| `src/app/Layout.tsx` — sidebar nav shell | 🟡 | Dashboard / Evaluations / Datasets / Audit Trail |
| `src/app/App.tsx` — React Router v6 setup | 🟡 | BrowserRouter + nested Routes |
| `src/pages/DashboardPage.tsx` — health + recent evals | 🟡 | API health indicator, last 5 evals |
| `src/pages/EvaluationsPage.tsx` — evaluation list | 🟡 | grid of EvaluationCards |
| `src/pages/EvaluationDetailPage.tsx` — trust-first detail | 🟡 | ALL 8 trust fields: provenance (1–4), method (5), metric defs+confidence (6), approval stub (7), audit history (8) |
| `src/pages/DatasetsPage.tsx` — dataset list | 🟡 | version, item_count, created_by |
| `src/pages/AuditPage.tsx` — full audit trail | 🟡 | AuditTimeline with hash chain |
| `package.json` — added react-router-dom ^6.26.0 | 🟡 | only dep change; types bundled in package |
| Exit criteria: every trust field shown for a real eval | 🟡 | All 8 fields present in EvaluationDetailPage; verified by code review; live test blocked by R6 (no Node/Rust toolchain locally) |

**Note:** 🟡 = authored, not live-tested locally (R6: no Node.js toolchain in dev environment). CI will verify `tsc --noEmit` + `vite build`.

## Phase 5 — Comparison & Regression Detection ✅ (backend) / 🟡 (frontend)
| Item | Status | Notes |
|------|--------|-------|
| `app/models/comparison.py` — `Comparison` immutable event model | ✅ | baseline_id, candidate_id, metric_deltas, regressions_detected, improvements_detected, status |
| `app/schemas/comparison.py` — `ComparisonCreate`, `ComparisonOut`, `MetricDeltaOut` | ✅ | kind validator, threshold_config |
| `app/services/comparison_service.py` — delta computation + regression detection | ✅ | DEFAULT_THRESHOLD=0.02; per-metric threshold override; audit event on create |
| `app/api/comparisons.py` — `POST/GET /comparisons`, `GET /comparisons/{id}` | ✅ | filters: baseline_id, candidate_id, dataset_key, status |
| Migration `c5d6e7f8a9b0` (comparisons table + 3 indexes) | ✅ | `alembic check` clean |
| `app/models/__init__.py` + `app/main.py` wired | ✅ | |
| Tests (neutral, regression, improvement, custom threshold, audit, mismatch 422, 404s, list, filter) | ✅ | **45/45 passed** · ruff ✅ · mypy --strict ✅ · alembic clean ✅ |
| `src/types/index.ts` — `MetricDelta`, `Comparison` types | 🟡 | |
| `src/lib/api.ts` — createComparison, listComparisons, getComparison | 🟡 | |
| `src/components/RegressionBadge.tsx` — regression/improvement/neutral badge | 🟡 | |
| `src/components/ComparisonGrid.tsx` — metric delta table with pp badges | 🟡 | |
| `src/pages/ComparePage.tsx` — form + history + detail | 🟡 | select baseline/candidate, run comparison, view deltas |
| `src/app/Layout.tsx` + `App.tsx` — Compare nav + /compare route | 🟡 | |
| Exit criteria: regression detected, shown with evidence, recorded | ✅ (backend) 🟡 (UI) | backend 100% verified; UI CI-gated (R6) |

## Phase 6 — Release Gates & Approvals → MVP ✅ (backend) / 🟡 (frontend)
| Item | Status | Notes |
|------|--------|-------|
| `app/models/release_gate.py` — `ReleaseGate` versioned entity | ✅ | name, criteria JSON, max_regressions_allowed, require_approval |
| `app/models/gate_decision.py` — `GateDecision` immutable event | ✅ | status lifecycle: passed/failed/pending_approval/approved/rejected/overridden |
| `app/models/approval.py` — `Approval` immutable event | ✅ | action + mandatory justification |
| `app/schemas/release_gate.py` — `ReleaseGateCreate`, `ReleaseGateOut` | ✅ | GateCriterionIn with min_score validation |
| `app/schemas/gate_decision.py` — `GateDecisionOut`, `ApprovalCreate`, `ApprovalOut` | ✅ | action validator |
| `app/services/gate_service.py` — create gate, evaluate gate | ✅ | per-criterion check, regression count check, status logic |
| `app/services/approval_service.py` — approve/reject/override | ✅ | state machine validation + audit |
| `app/api/gates.py` — all gate endpoints | ✅ | POST/GET /gates, POST /{gate_key}/evaluate, GET /{gate_key}/decisions, POST /decisions/{id}/approve |
| Migration `d6e7f8a9b0c1` (release_gates + gate_decisions + approvals tables) | ✅ | `alembic check` clean |
| `app/models/__init__.py` + `app/main.py` wired | ✅ | |
| Tests (create, list, 404, evaluate passed/pending/failed criteria/regressions, 422s, approve, reject, override, invalid transition, list decisions) | ✅ | **60/60 passed** · ruff ✅ · mypy --strict ✅ · alembic clean ✅ |
| `src/types/index.ts` — ReleaseGate, GateDecision, Approval, GateCriterion, CriterionResult types | 🟡 | |
| `src/lib/api.ts` — createGate, listGates, getGate, evaluateGate, listGateDecisions, approveDecision | 🟡 | |
| `src/components/GateStatusBadge.tsx` — status badge (passed/failed/pending/approved/rejected/overridden) | 🟡 | |
| `src/components/GateCriteriaResults.tsx` — per-criterion pass/fail table | 🟡 | |
| `src/pages/GatesPage.tsx` — create/list gates, evaluate, decisions list, approve/reject/override | 🟡 | |
| `src/app/Layout.tsx` + `App.tsx` — Release Gates nav + /gates route | 🟡 | |
| Exit criteria: end-to-end dataset→eval→compare→gate→approval, fully audited | ✅ (backend) 🟡 (UI) | backend 100% verified; UI CI-gated (R6) |

## Phases 7–11 ⬜ Not started
See [progress.md](./progress.md). Phase 6 = MVP complete (backend). STOP for review before starting Phase 7.
