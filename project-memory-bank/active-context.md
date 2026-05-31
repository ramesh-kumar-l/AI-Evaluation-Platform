# Active Context (save-state)

_Last updated: 2026-05-31_

## Where we are
- **Phase 0 — Foundations & Memory Bank: COMPLETE & verified.**
- **Phase 1 — Core Domain Model & Versioning: COMPLETE & verified (backend).**
- **Phase 2 — Provider Abstraction & Offline Execution: COMPLETE & verified (backend).**
- **Phase 3 — Evaluation Engine + Metrics: COMPLETE & verified (backend).**
- **Phase 4 — Trust-First Result UI: AUTHORED (frontend) — not live-tested (R6: no Node toolchain locally); CI-gated.**
- Next up: **Phase 5 — Comparison & Regression Detection** (STOP for review first, per protocol).

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
- **Frontend (P4) authored, not live-tested** — CI (`npm install && tsc --noEmit && vite build`) is
  the verification gate. Risk R6 (no Node/Rust toolchain in dev environment).
- **docker-compose** authored but not run here.
- Phase 5 needs: Comparison engine (model-vs-model, prompt-vs-prompt), regression detection +
  thresholds, ComparisonGrid/ResultDiffViewer/RegressionViewer components.
- Concurrency note: audit hash chain uses last-seq lookup; fine for single-writer/offline.
  Revisit for concurrent writers before multi-user (Phase 11).
