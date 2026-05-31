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

## Phase 7 — Dataset & Benchmark Governance ✅ (backend) / 🟡 (frontend)
| Item | Status | Notes |
|------|--------|-------|
| `app/models/benchmark.py` — `Benchmark` versioned entity | ✅ | name, domain, task_type, metric_keys, dataset_key, status (draft/active/deprecated/archived) |
| `app/models/dataset_policy.py` — `DatasetPolicy` mutable governance record | ✅ | one per dataset_key; quality_rules, ground_truth_policy, owner, status |
| `app/schemas/benchmark.py` — `BenchmarkCreate`, `BenchmarkOut`, `BenchmarkStatusUpdate` | ✅ | status validator |
| `app/schemas/dataset_policy.py` — `DatasetPolicyUpsert`, `DatasetPolicyOut` | ✅ | status validator |
| `app/services/benchmark_service.py` — create, get, list, set_status | ✅ | lifecycle state machine: draft→active→deprecated→archived; draft→deprecated shortcut |
| `app/services/dataset_policy_service.py` — upsert, get | ✅ | validates dataset exists; audit on every upsert |
| `app/api/benchmarks.py` — POST/GET /benchmarks, GET /{key}, PATCH /{key}/status | ✅ | 422 on invalid lifecycle transition |
| `app/api/datasets.py` — PUT/GET /datasets/{key}/policy | ✅ | appended policy endpoints |
| Migration `e7f8a9b0c1d2` (benchmarks + dataset_policies tables) | ✅ | `alembic check` clean; indexes: ix_benchmarks_entity_key, ix_benchmarks_status, ix_dataset_policies_dataset_key |
| `app/models/__init__.py` + `app/main.py` wired | ✅ | |
| Tests (create, list, filter by status, 404, draft→active, active→deprecated, deprecated→archived, draft→deprecated skip, invalid transition 422, unknown status 422, new version created, policy create, policy update, policy GET, policy 404, dataset not found 422, invalid status 422) | ✅ | **77/77 passed** · ruff ✅ · mypy --strict ✅ (75 files) · alembic clean ✅ |
| `src/types/index.ts` — `Benchmark`, `BenchmarkStatus`, `DatasetPolicy` types | 🟡 | |
| `src/lib/api.ts` — createBenchmark, listBenchmarks, getBenchmark, setBenchmarkStatus, upsertDatasetPolicy, getDatasetPolicy | 🟡 | |
| `src/pages/BenchmarksPage.tsx` — BenchmarkExplorer + DatasetPolicyPanel | 🟡 | create form, list, lifecycle transitions, dataset policy inline |
| `src/app/Layout.tsx` + `App.tsx` — Benchmarks nav + /benchmarks route | 🟡 | |
| Exit criteria: benchmark created, lifecycle transitioned, dataset policy attached, all audited | ✅ (backend) 🟡 (UI) | backend 100% verified; UI CI-gated (R6) |

## Phase 8 — RAG Evaluation ✅ (backend) / 🟡 (frontend)
| Item | Status | Notes |
|------|--------|-------|
| `app/models/rag_corpus.py` — `RagCorpus` versioned entity | ✅ | name, description, embedding_model ("tf-idf" default), chunk_size, chunk_overlap |
| `app/models/rag_document.py` — `RagDocument` immutable chunk | ✅ | corpus_key, content, chunk_index, doc_source, embedding (JSON TF vector) |
| `app/models/rag_eval.py` — `RagEval` immutable event | ✅ | corpus_key, dataset_key, top_k, query_count, mean_context_relevance, mean_faithfulness, mean_answer_relevance, status |
| `app/models/rag_eval_result.py` — `RagEvalResult` immutable per-query | ✅ | rag_eval_id, query_text, retrieved_doc_ids, retrieved_content, answer_text, 3 scores |
| `app/schemas/rag.py` — all RAG schemas | ✅ | RagCorpusCreate/Out, RagDocumentCreate/Out, RagSearchRequest/Response, RagEvalCreate/Out, RagEvalResultOut |
| `app/services/metrics/_utils.py` — shared TF-cosine utils | ✅ | tf_vector, cosine — offline, no ML deps |
| `app/services/metrics/context_relevance.py` — mean TF-cosine(query, docs) | ✅ | confidence "medium" |
| `app/services/metrics/faithfulness.py` — overlap coefficient(answer, context) | ✅ | confidence "low" |
| `app/services/metrics/answer_relevance.py` — TF-cosine(question, answer) | ✅ | confidence "medium" |
| `app/services/rag_corpus_service.py` — create/get/list corpora | ✅ | wraps versioning service |
| `app/services/rag_document_service.py` — ingest_documents, list_documents | ✅ | computes TF embedding on ingest; validates corpus exists |
| `app/services/rag_retrieval_service.py` — retrieve(db, corpus_key, query, top_k) | ✅ | pure-Python TF-IDF cosine; swap for pgvector ANN in production |
| `app/services/rag_eval_service.py` — run_rag_eval orchestrator | ✅ | retrieve → score 3 metrics per query → persist results + aggregate; audit event |
| `app/api/rag.py` — all RAG endpoints | ✅ | POST/GET /rag/corpora, POST /corpora/{key}/documents, GET /corpora/{key}/documents, POST /corpora/{key}/search, POST/GET /rag/evaluations, GET /evaluations/{id}/results |
| Migration `f0a1b2c3d4e5` (rag_corpora + rag_documents + rag_evals + rag_eval_results) | ✅ | alembic check clean; 5 indexes |
| `app/models/__init__.py` + `app/main.py` wired | ✅ | |
| Tests (corpus CRUD, doc ingest, 422s, search, empty-corpus, RAG eval run, results, 404s, scorer unit tests) | ✅ | **96/96 passed** · ruff ✅ · mypy --strict ✅ (89 files) · alembic clean ✅ |
| `src/types/index.ts` — RagCorpus, RagDocument, RagSearchResponse, RagEval, RagEvalResult types | 🟡 | |
| `src/lib/api.ts` — createRagCorpus, listRagCorpora, getRagCorpus, ingestDocuments, listRagDocuments, searchRagCorpus, runRagEval, getRagEval, getRagEvalResults | 🟡 | |
| `src/pages/RagCorpusPanels.tsx` — CorpusCreateForm, IngestPanel, SearchPanel | 🟡 | <300 lines |
| `src/pages/RagPage.tsx` — EvalPanel, CorpusDetail, RagPage (2-col layout) | 🟡 | <300 lines; /rag route |
| `src/app/Layout.tsx` + `App.tsx` — RAG Eval nav + /rag route | 🟡 | |
| Exit criteria: corpus created, docs ingested, retrieval tested, RAG eval scored | ✅ (backend) 🟡 (UI) | backend 100% verified; UI CI-gated (R6) |

## Phase 9 — Agent & Tool Evaluation ✅ (backend) / 🟡 (frontend)
| Item | Status | Notes |
|------|--------|-------|
| `app/models/agent_run.py` — `AgentRun` immutable trajectory record | ✅ | agent_name, query, final_answer, tool_calls (JSON), step_count, status |
| `app/models/agent_step.py` — `AgentStep` immutable step record | ✅ | step_index, step_type (thinking/tool_call/response), tool_name, tool_input, tool_output, reasoning_text |
| `app/models/agent_eval.py` — `AgentEval` immutable eval record | ✅ | dataset_key, agent_name, query_count, 3 aggregate scores, status |
| `app/models/agent_eval_result.py` — `AgentEvalResult` per-query result | ✅ | agent_eval_id, query_text, expected/actual answer, expected/actual tools, 3 scores |
| `app/schemas/agent.py` — all agent schemas | ✅ | AgentStepCreate/Out, AgentRunCreate/Out, AgentEvalCreate/Out, AgentEvalResultOut |
| `app/services/metrics/tool_call_accuracy.py` — F1 over tool-name sets | ✅ | confidence "medium"; order-independent |
| `app/services/metrics/trajectory_score.py` — Dice-LCS over ordered tool sequences | ✅ | confidence "low"; captures ordering |
| `app/services/metrics/task_completion.py` — TF-cosine(expected, actual answer) | ✅ | confidence "medium"; reuses _utils.py |
| `app/services/agent_run_service.py` — create_run, get_run, list_runs, list_steps | ✅ | inline step creation; audit event on create |
| `app/services/agent_eval_service.py` — run_agent_eval orchestrator | ✅ | matches runs by agent_name+query; expected.tools dict format; 3 scorers |
| `app/api/agent.py` — all agent endpoints | ✅ | POST/GET /agent/runs, GET /runs/{id}, GET /runs/{id}/steps, POST/GET /agent/evaluations, GET /evaluations/{id}, GET /evaluations/{id}/results |
| Migration `g1b2c3d4e5f6` (agent_runs + agent_steps + agent_evals + agent_eval_results) | ✅ | alembic check clean; 5 indexes |
| `app/models/__init__.py` + `app/main.py` wired | ✅ | |
| Tests (metric scorers ×10, run CRUD ×5, agent eval ×6) | ✅ | **117/117 passed** · ruff ✅ · mypy --strict ✅ (100 files) · alembic clean ✅ |
| `src/types/index.ts` — AgentStep, AgentRun, AgentEval, AgentEvalResult types | 🟡 | |
| `src/lib/api.ts` — submitAgentRun, listAgentRuns, getAgentRun, getAgentRunSteps, runAgentEval, listAgentEvals, getAgentEval, getAgentEvalResults | 🟡 | |
| `src/pages/AgentRunPanels.tsx` — RunCreateForm, RunStepsPanel | 🟡 | <300 lines |
| `src/pages/AgentPage.tsx` — EvalPanel, AgentDetail, AgentPage (2-col layout) | 🟡 | <300 lines; /agent route |
| `src/app/Layout.tsx` + `App.tsx` — Agent Eval nav + /agent route | 🟡 | |
| Exit criteria: run submitted, steps recorded, eval scored with 3 metrics | ✅ (backend) 🟡 (UI) | backend 100% verified; UI CI-gated (R6) |

## Phase 10 — Observability & Continuous Evaluation ✅ (backend) / 🟡 (frontend)
| Item | Status | Notes |
|------|--------|-------|
| `app/models/eval_schedule.py` — `EvalSchedule` versioned entity | ✅ | name, description, dataset_key, model_key, prompt_key, metric_keys, cron_expr, status (active/paused/archived), last_run_at, next_run_at |
| `app/models/eval_job.py` — `EvalJob` immutable event | ✅ | schedule_id, status (pending/running/completed/failed), eval_id, error_msg, triggered_by, started/completed timestamps |
| `app/models/experiment.py` — `Experiment` versioned entity | ✅ | name, description, evaluation_ids (JSON), status (active/concluded/archived), hypothesis, conclusion |
| `app/schemas/observability.py` — all P10 schemas | ✅ | EvalScheduleCreate/StatusUpdate/Out, EvalJobOut, ExperimentCreate/Update/Out, TrendPoint/TrendOut |
| `app/services/trend_service.py` — trend query from existing Evaluation data | ✅ | get_metric_trend(dataset_key, metric_kind): derives from aggregate_scores, no new model |
| `app/services/experiment_service.py` — experiment CRUD | ✅ | create_experiment, update_experiment (new version), get/list; ObservabilityError defined here |
| `app/services/schedule_service.py` — schedule CRUD + trigger | ✅ | lifecycle: active↔paused→archived; trigger runs execute_evaluation inline; job records result |
| `app/core/scheduler.py` — APScheduler soft dependency | ✅ | importlib.util.find_spec for detection; graceful degrade if not installed; configure_scheduler/stop_scheduler wired to lifespan |
| `app/api/observability.py` — 11 endpoints under /observe | ✅ | schedules CRUD + status + trigger + jobs; experiments CRUD; trends query |
| Migration `h2c3d4e5f6g7` (3 tables: eval_schedules + eval_jobs + experiments + 7 indexes) | ✅ | alembic check clean |
| `app/models/__init__.py` + `app/main.py` wired | ✅ | scheduler wired to lifespan |
| `pyproject.toml` — scheduler optional extra added | ✅ | `[scheduler] = ["apscheduler>=3.10"]` |
| Tests (schedule CRUD×5, trigger×4, experiments×5, trends×2, scheduler soft-dep graceful) | ✅ | **134/134 passed** · ruff ✅ · mypy --strict ✅ (109 files) · alembic clean ✅ |
| `src/types/index.ts` — EvalSchedule, EvalJob, Experiment, TrendPoint, TrendOut types | 🟡 | |
| `src/lib/api.ts` — createEvalSchedule, listEvalSchedules, updateScheduleStatus, triggerSchedule, listEvalJobs, createExperiment, listExperiments, updateExperiment, getMetricTrend | 🟡 | |
| `src/pages/ObservabilityPanels.tsx` — ScheduleCreateForm, ScheduleList, SchedulePanel | 🟡 | <300 lines |
| `src/pages/ObservabilityPage.tsx` — TrendsPanel, ExperimentsPanel, ObservabilityPage (3-tab) | 🟡 | <300 lines; /observe route |
| `src/app/Layout.tsx` + `App.tsx` — Observability nav + /observe route | 🟡 | |
| Exit criteria: schedule created, triggered, job recorded; experiment created; trend queried | ✅ (backend) 🟡 (UI) | backend 100% verified; UI CI-gated (R6) |

## Phase 11 — Governance, Security, Accessibility, Docs & Deployment Hardening ✅ (backend) / 🟡 (frontend)
| Item | Status | Notes |
|------|--------|-------|
| `app/models/api_key.py` — `ApiKey` immutable record | ✅ | id, name, key_hash (sha256, unique), role, created_at, revoked_at; is_active property |
| `app/schemas/auth.py` — auth schemas | ✅ | ApiKeyCreate, ApiKeyCreatedOut (raw_key shown once), ApiKeyOut (last4 hash only) |
| `app/services/auth_service.py` — key lifecycle | ✅ | create_key, get_key_by_raw (sha256 lookup), revoke_key, list_keys |
| `app/core/auth.py` — FastAPI dependency | ✅ | get_current_key: returns ApiKey or None (when disabled); 401 missing, 403 invalid/revoked |
| `app/core/rbac.py` — role hierarchy | ✅ | viewer(0) < evaluator(1) < approver(2) < admin(3); require_role(min) factory |
| `app/core/rate_limit.py` — sliding-window middleware | ✅ | in-process deque per key/IP; 429 with Retry-After; bypassed on health/ready |
| `app/core/security_headers.py` — security headers middleware | ✅ | X-Content-Type-Options, X-Frame-Options, Referrer-Policy, X-XSS-Protection, Permissions-Policy |
| `app/api/admin.py` — key management endpoints | ✅ | POST/GET/DELETE /admin/api-keys; protected by X-Admin-Secret header |
| `app/core/config.py` — added api_auth_enabled, admin_secret, rate_limit_per_minute | ✅ | auth disabled by default (offline-first); enable in production |
| `app/api/deps.py` — updated get_actor | ✅ | actor from API key name when auth enabled; X-Actor fallback when disabled |
| `app/main.py` — middlewares + auth wired | ✅ | RateLimitMiddleware + SecurityHeadersMiddleware; Depends(get_current_key) on all routers except health |
| Migration `i3d4e5f6g7h8` (api_keys table, 3 constraints, 1 index) | ✅ | alembic check clean |
| Tests (create key, list, revoke, 404 revoke, 401 missing, 403 invalid, valid access, revoked 403, viewer read, RBAC hierarchy, RBAC rejects, evaluator write, admin secret required, wrong secret, security headers, rate limit 429) | ✅ | **150/150 passed** · ruff ✅ · mypy --strict ✅ (117 files) · alembic clean ✅ |
| `infra/k8s/` — 7 Kubernetes manifests | 🟡 | namespace, configmap, secret (template), deployment (non-root, read-only fs, resource limits), service, ingress, hpa |
| `infra/docker-compose.prod.yml` — hardened production compose | 🟡 | non-root user, read-only fs, resource limits, internal+external networks |
| `backend/Dockerfile` — multi-stage build | 🟡 | builder stage + production stage (non-root, minimal image, 2 workers) |
| `mkdocs.yml` + `docs/` — MkDocs documentation | 🟡 | index, architecture (domain model + migration chain), api reference, deployment guide |
| `frontend/src/components/SkipToContent.tsx` — skip nav | 🟡 | keyboard-accessible, sr-only until focused, WCAG AA |
| `frontend/src/app/Layout.tsx` — ARIA landmarks | 🟡 | role=navigation, role=main, id=main-content, aria-label on aside; skip link wired |
| Exit criteria: auth enforced, security headers present, rate limiting active, K8s deployable, docs authored | ✅ (backend) 🟡 (infra/docs/UI) | backend 100% verified; infra/docs authored |
