# Changelog

All notable changes to AI Evaluation Platform are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).  
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added — Phase 11: Governance, Security, Accessibility, Docs & Deployment Hardening
- API key authentication: SHA256-hashed keys (prefix `aep_`), raw key shown once at creation, never stored
- RBAC roles: `viewer(0) < evaluator(1) < approver(2) < admin(3)`, enforced via `require_role()` factory
- Auth disabled by default (`AEP_API_AUTH_ENABLED=false`) — offline/local dev unaffected; enable in production
- Admin bootstrap via `X-Admin-Secret` header — solves chicken-and-egg for first key creation
- `RateLimitMiddleware`: in-process sliding window per API key or IP, 1000 req/min default, `Retry-After` on 429
- `SecurityHeadersMiddleware`: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`
- `POST/GET/DELETE /admin/api-keys` — key lifecycle management
- `get_actor` updated: actor from API key name when auth enabled; `X-Actor` fallback when disabled
- All 15 protected routers use `Depends(get_current_key)` centrally in `main.py`
- Migration `i3d4e5f6g7h8`: `api_keys` table (unique name, unique key_hash, indexed role)
- Multi-stage Dockerfile: builder + production (non-root UID 1000, `--workers 2`, minimal image)
- `infra/docker-compose.prod.yml`: non-root user, read-only rootfs, resource limits, network isolation
- Kubernetes manifests: namespace, configmap, secret template, deployment (securityContext, probes), service, ingress (nginx+TLS), HPA (min 2/max 10, CPU 70% target)
- MkDocs (Material theme): `docs/index.md`, `docs/architecture.md`, `docs/api.md`, `docs/deployment.md`
- Frontend: `SkipToContent.tsx` (WCAG AA skip-nav), ARIA landmarks on `Layout.tsx`
- 16 new security tests (total: 150/150 passing)

### Added — Phase 10: Observability & Continuous Evaluation
- `EvalSchedule` versioned entity: cron-based evaluation schedule with active/paused/archived lifecycle
- `EvalJob` immutable event: record of one schedule trigger (pending/running/completed/failed)
- `Experiment` versioned entity: A/B grouping of evaluations with hypothesis + conclusion
- `POST/GET/PATCH /observe/schedules` + trigger endpoint + job listing
- `POST/GET/PATCH /observe/experiments`
- `GET /observe/trends` — derives from `Evaluation.aggregate_scores`, no new model
- APScheduler soft dependency: detected via `importlib.util.find_spec`, graceful degrade when absent
- Migration `h2c3d4e5f6g7`: 3 tables (eval_schedules, eval_jobs, experiments), 7 indexes
- 17 new tests (total: 134/134 passing)

### Added — Phase 9: Agent & Tool Evaluation
- `AgentRun` + `AgentStep` immutable trajectory records (submit with inline steps)
- `AgentEval` + `AgentEvalResult` evaluation records
- `tool_call_accuracy` scorer: F1 over tool-name sets (order-independent)
- `trajectory_score` scorer: Dice-LCS over ordered tool sequences (captures ordering)
- `task_completion` scorer: TF-cosine(expected_answer, actual_answer)
- 8 endpoints under `/agent`
- Migration `g1b2c3d4e5f6`: 4 tables, 5 indexes
- 21 new tests (total: 117/117 passing)

### Added — Phase 8: RAG Evaluation
- `RagCorpus` versioned entity + `RagDocument` immutable chunk (TF embedding on ingest)
- `RagEval` + `RagEvalResult` immutable evaluation records
- `rag_retrieval_service`: pure-Python TF-IDF cosine retrieval (pgvector ANN swap-in for production)
- `context_relevance` scorer: TF-cosine(query, retrieved_docs)
- `faithfulness` scorer: overlap coefficient(answer, context)
- `answer_relevance` scorer: TF-cosine(question, answer)
- 9 endpoints under `/rag`
- Migration `f0a1b2c3d4e5`: 4 tables (rag_corpora, rag_documents, rag_evals, rag_eval_results), 5 indexes
- 21 new tests (total: 96/96 passing)

### Added — Phase 7: Dataset & Benchmark Governance
- `Benchmark` versioned entity with lifecycle state machine (draft→active→deprecated→archived)
- `DatasetPolicy` mutable governance record (one per dataset key; quality rules + owner)
- `PATCH /benchmarks/{key}/status` — lifecycle transitions with validation
- `PUT/GET /datasets/{key}/policy`
- Migration `e7f8a9b0c1d2`: 2 tables (benchmarks, dataset_policies), 3 indexes
- 17 new tests (total: 77/77 passing)

### Added — Phase 6: Release Gates & Approvals (MVP complete)
- `ReleaseGate` versioned entity: named criteria (metric thresholds + max regressions + require_approval)
- `GateDecision` immutable event: 6-state lifecycle (passed/failed/pending_approval/approved/rejected/overridden)
- `Approval` immutable event: action + mandatory justification (min 10 chars)
- Gate evaluation service: per-criterion check + regression count check + status logic
- Approval state machine: approve/reject/override with audit
- `POST/GET /gates` + evaluate + decisions + approve
- Migration `d6e7f8a9b0c1`: 3 tables (release_gates, gate_decisions, approvals)
- 15 new tests (total: 60/60 passing)

### Added — Phase 5: Comparison & Regression Detection
- `Comparison` immutable event: per-metric deltas, regression/improvement detection
- `comparison_service`: DEFAULT_THRESHOLD=0.02, per-metric threshold override
- `POST/GET /comparisons`
- Migration `c5d6e7f8a9b0`: comparisons table, 3 indexes
- 12 new tests (total: 45/45 passing)

### Added — Phase 4: Trust-First Result UI
- React frontend shell: React Router v6, sidebar nav, Tailwind + shadcn/ui tokens
- `EvaluationDetailPage` with all 8 trust fields (dataset/prompt/model/metric versions, method, confidence, approval, audit)
- Components: `EvaluationCard`, `MetricCard`, `TrustIndicator`, `AuditTimeline`, `Badge`, `Card`, `Spinner`
- Pages: Dashboard, Evaluations, Datasets, Audit, Compare, Gates

### Added — Phase 3: Evaluation Engine + Metrics
- `Metric` versioned entity (kind + config)
- `Evaluation` + `EvaluationResult` immutable event records
- `exact_match` scorer: normalized string equality, confidence "high"
- `contains` scorer: substring check, confidence "medium"
- `semantic_similarity` scorer: pure-Python TF-cosine, confidence "low", no ML deps
- In-process orchestration: render → call → score → persist (no Temporal cluster required)
- `POST/GET /metrics`, `POST/GET /evaluations`, `GET /evaluations/{id}/results`
- Migration `a8a557afd538`: 3 tables (metrics, evaluations, evaluation_results)
- 12 new tests (total: 33/33 passing)

### Added — Phase 2: Provider Abstraction & Offline Execution
- `ProviderAdapter` Protocol + `InferenceRequest`/`InferenceResponse` dataclasses
- `OllamaAdapter`: HTTP `/api/generate`, offline-first
- Adapter registry: `get_adapter(kind, base_url)`
- `InferenceRun` immutable event record
- `run_service.execute_run`: render prompt → call adapter → persist + audit
- `POST/GET /runs`
- Migration `b3556b7705c3`: inference_runs table, 3 indexes
- 10 new tests (total: 18/18 passing)

### Added — Phase 1: Core Domain Model & Versioning
- `VersionedMixin` + `VersionedBase`: immutable versioning + lineage (entity_key, version, parent_id, is_latest)
- Domain entities: Provider/Model, Prompt, Dataset
- Append-only hash-chained `AuditEvent`: `sha256(prev_hash + canonical_payload)` tamper-evident chain
- Generic versioning service (create_version, get_latest, get_by_version, list_versions)
- Per-domain services (provider, prompt, dataset)
- `POST/GET /providers`, `/prompts`, `/datasets`, `/audit/events`, `/audit/verify`
- Migration `a40763e31c9b`: 5 tables (providers, prompts, datasets, audit_events, models)
- 8 tests (total: 8/8 passing)

### Added — Phase 0: Foundations & Memory Bank
- Monorepo layout: `backend/`, `frontend/`, `infra/`, `docs/`, `project-memory-bank/`
- FastAPI app skeleton: `/health`, `/ready`
- SQLite fallback: zero-infra offline dev with no `AEP_DATABASE_URL`
- structlog structured logging, OTel skeleton (no-op unless `OTEL_EXPORTER_OTLP_ENDPOINT` set)
- Alembic baseline, pyproject.toml, uv + ruff + mypy CI
- `.github/workflows/ci.yml`
- Memory bank: ADR-0001, ADR-0002, risk register, governance folders

---

## Format Notes

- Types: `Added` for new features; `Changed` for behavior changes; `Fixed` for bug fixes; `Removed` for removals
- Unreleased changes live under `[Unreleased]` until a version is tagged
- When cutting a release: move `[Unreleased]` section to `[x.y.z] — YYYY-MM-DD`
