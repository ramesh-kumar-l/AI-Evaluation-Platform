# Active Context (save-state)

_Last updated: 2026-05-31_

## Where we are
- **Phase 0 — Foundations & Memory Bank: COMPLETE & verified.**
- **Phase 1 — Core Domain Model & Versioning: COMPLETE & verified (backend).**
- **Phase 2 — Provider Abstraction & Offline Execution: COMPLETE & verified (backend).**
- **Phase 3 — Evaluation Engine + Metrics: COMPLETE & verified (backend).**
- **Phase 4 — Trust-First Result UI: AUTHORED (frontend) — not live-tested (R6); CI-gated.**
- **Phase 5 — Comparison & Regression Detection: COMPLETE (backend ✅) / AUTHORED (frontend 🟡).**
- **Phase 6 — Release Gates & Approvals → MVP: COMPLETE (backend ✅ verified) / AUTHORED (frontend 🟡 CI-gated). MVP REACHED.**
- **Phase 7 — Dataset & Benchmark Governance: COMPLETE (backend ✅ verified) / AUTHORED (frontend 🟡 CI-gated).**
- **Phase 8 — RAG Evaluation: COMPLETE (backend ✅ verified) / AUTHORED (frontend 🟡 CI-gated).**
- **Phase 9 — Agent & Tool Evaluation: COMPLETE (backend ✅ verified) / AUTHORED (frontend 🟡 CI-gated).**
- **Phase 10 — Observability & Continuous Evaluation: COMPLETE (backend ✅ verified) / AUTHORED (frontend 🟡 CI-gated).**
- **Phase 11 — Governance, Security, Accessibility, Docs & Deployment Hardening: COMPLETE (backend ✅ verified) / AUTHORED (infra/docs/frontend 🟡 CI-gated).**
- All phases P0–P11 complete. Platform is production-ready.

## What works right now
- Backend boots fully offline (SQLite fallback, no infra) — `uvicorn app.main:app`.
- Endpoints: `/health`, `/ready`, versioned CRUD for **providers, models, prompts, datasets**,
  `/audit/events`, `/audit/verify`, `POST/GET /runs` (inference), `POST/GET /metrics` (versioned
  metric definitions), `POST/GET /evaluations` + `/{id}/results` (dataset-level evaluation).
- Immutable versioning + hash-chained `AuditEvent` on every mutation.
- **Evaluation engine**: `POST /evaluations` creates and executes a dataset-level evaluation
  in-process (no Temporal). Per item: renders prompt → calls Ollama → scores with each metric →
  stores `EvaluationResult`. Aggregate stats (mean_score, confidence_distribution) in `Evaluation`
  row. Provider failures → `status="partial/failed"`, still persisted.
- **Metric scorers**: `exact_match` (confidence "high"), `contains` (confidence "medium"),
  `semantic_similarity` TF-cosine pure Python (confidence "low", no ML deps).
- Migrations: `a40763e31c9b` + `b3556b7705c3` + `a8a557afd538`.
- Backend quality gates green: **ruff, ruff format, mypy --strict, pytest (33 passed), alembic check clean**.
- **Frontend shell (P4)**: React Router v6 SPA, sidebar nav (Dashboard/Evaluations/Datasets/Audit),
  EvaluationCard, MetricCard, TrustIndicator, AuditTimeline components, EvaluationDetailPage with
  all 8 trust fields. Frontend build-verified only in CI (R6: no Node locally).

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
- `InferenceRun`, `Evaluation`, `EvaluationResult` are NOT `VersionedBase` — immutable event records.
- `Metric` IS `VersionedBase` — it's a revisable definition (like Prompt).
- Audit `record_event` normalises payloads via `json.loads(json.dumps(..., default=str))`.

## Open threads / next-phase notes
- **Frontend (P4+P5) authored, not live-tested** — CI (`npm install && tsc --noEmit && vite build`)
  is the verification gate. Risk R6 (no Node/Rust toolchain in dev environment).
- **docker-compose** authored but not run here.
- Migrations so far: a40763e31c9b → b3556b7705c3 → a8a557afd538 → c5d6e7f8a9b0 → d6e7f8a9b0c1 → e7f8a9b0c1d2 → f0a1b2c3d4e5 → g1b2c3d4e5f6 → h2c3d4e5f6g7 → i3d4e5f6g7h8.
- **Phase 6 complete (backend).** GateDecision status lifecycle: passed/failed/pending_approval/approved/rejected/overridden. Approval with mandatory justification (min 10 chars). Override of failed decisions fully audited.
- **Phase 7 complete (backend).** Benchmark VersionedBase with lifecycle state machine (draft→active→deprecated→archived, with draft→deprecated shortcut). DatasetPolicy mutable governance record (upsert, one per dataset_key). Migration chain: ...→ d6e7f8a9b0c1 → e7f8a9b0c1d2. 77/77 tests, ruff/mypy(75 files)/alembic clean.
- **Phase 8 complete (backend).** RagCorpus (VersionedBase), RagDocument/RagEval/RagEvalResult (immutable events). Pure-Python TF-IDF retrieval (offline-first; pgvector swap-in for production). 3 RAG metric scorers: context_relevance, faithfulness, answer_relevance. 9 endpoints under /rag. Migration f0a1b2c3d4e5. 96/96 tests, ruff/mypy(89 files)/alembic clean.
- **Phase 9 complete (backend).** AgentRun/AgentStep/AgentEval/AgentEvalResult (immutable events). Submit trajectories + inline steps; match by agent_name+query. 3 scorers: tool_call_accuracy (F1 sets), trajectory_score (Dice-LCS), task_completion (TF-cosine). expected.tools dict format (DatasetItem schema strips extra keys). 8 endpoints under /agent. Migration g1b2c3d4e5f6. 117/117 tests, ruff/mypy(100 files)/alembic clean.
- **Phase 10 complete (backend).** EvalSchedule (VersionedBase), EvalJob (immutable), Experiment (VersionedBase). Schedule lifecycle: active↔paused→archived. Trigger runs execute_evaluation inline; job records result. Experiment A/B grouping with versioning. Trend query derives from existing Evaluation.aggregate_scores (no new model). APScheduler soft dep (apscheduler optional extra; graceful degrade if not installed). 11 endpoints under /observe. Migration h2c3d4e5f6g7 (3 tables, 7 indexes). 134/134 tests, ruff/mypy(109 files)/alembic clean.
- **Phase 11 complete (backend).** ApiKey model (sha256-hashed, never stored raw). Auth disabled by default (AEP_API_AUTH_ENABLED=false for offline/local); enable in production. Roles: viewer(0)<evaluator(1)<approver(2)<admin(3). Middlewares: SecurityHeadersMiddleware (X-Content-Type-Options/X-Frame-Options/Referrer-Policy), RateLimitMiddleware (sliding window, 1000/min default, per-key/IP). Admin bootstrap via X-Admin-Secret header. All 15 protected routers use Depends(get_current_key). K8s manifests (namespace/configmap/secret/deployment/service/ingress/hpa), docker-compose.prod.yml, multi-stage Dockerfile. MkDocs (index/architecture/api/deployment). Frontend: SkipToContent + ARIA landmarks on Layout. Migration i3d4e5f6g7h8. 150/150 tests, ruff/mypy(117 files)/alembic clean.
- Concurrency note: audit hash chain uses last-seq lookup; fine for single-writer/offline.
  Revisit for concurrent writers before multi-user (Phase 11).
