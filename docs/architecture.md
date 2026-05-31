# Architecture

## System overview

```
┌─────────────────────────────────────────────────────────────────────┐
│  React SPA (Vite + TypeScript + Tailwind + shadcn/ui)               │
│  Pages: Evals · Compare · Gates · RAG · Agent · Observe · Audit    │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ HTTP  (X-API-Key auth)
┌──────────────────────────▼──────────────────────────────────────────┐
│  FastAPI  (app.main:create_app)                                      │
│  Middlewares: SecurityHeaders → RateLimit                            │
│  Auth: API key → RBAC (viewer/evaluator/approver/admin)             │
│  Routers: 16 domain routers + health + admin                        │
└──────┬──────────┬──────────┬────────────┬──────────────────────────┘
       │          │          │            │
  Services   Providers  Scheduler    Telemetry (OTel, opt-in)
       │          │          │
  SQLAlchemy  Ollama     APScheduler (soft dep)
  (Alembic)   adapter
       │
  PostgreSQL  ←→  pgvector (ANN for RAG in production)
  SQLite      (zero-infra offline fallback)
```

## Domain model layers

### Versioned entities (VersionedBase)
Immutable rows — a change creates a new version with a lineage pointer. Every version is
permanently auditable.

| Entity | Phase | Purpose |
|--------|-------|---------|
| Provider / Model | P1–P2 | LLM provider registration |
| Prompt | P1 | Template with input_variables |
| Dataset | P1 | Ground-truth items |
| Metric | P3 | Scorer definition (kind + config) |
| ReleaseGate | P6 | Pass/fail criteria |
| Benchmark | P7 | Domain evaluation suite |
| RagCorpus | P8 | Document retrieval corpus |
| EvalSchedule | P10 | Recurring evaluation config |
| Experiment | P10 | A/B grouping of evaluations |

### Immutable event records (Base, not versioned)
Append-only — never mutated. Each row is a durable fact.

`InferenceRun · Evaluation · EvaluationResult · Comparison · GateDecision · Approval`  
`RagDocument · RagEval · RagEvalResult`  
`AgentRun · AgentStep · AgentEval · AgentEvalResult`  
`EvalJob · AuditEvent`

### Mutable governance record
`DatasetPolicy` — one per dataset_key; updated in-place (upsert pattern).

## Key decisions

**Offline-first:** SQLite + Ollama replaces Postgres + cloud LLM for zero-infra dev.  
**No Temporal:** evaluation orchestration is in-process; Temporal is a future swap-in.  
**Pure-Python metrics:** TF-cosine semantic similarity needs no ML libraries.  
**Hash-chained audit:** every `AuditEvent` chains to its predecessor via sha256 — tamper-evident.  
**Immutable versioning:** entities never mutate; new row = new version preserves lineage.

## Migration chain

```
a40763e31c9b (P0)  →  b3556b7705c3 (P2)  →  a8a557afd538 (P3)
  →  c5d6e7f8a9b0 (P5)  →  d6e7f8a9b0c1 (P6)  →  e7f8a9b0c1d2 (P7)
  →  f0a1b2c3d4e5 (P8)  →  g1b2c3d4e5f6 (P9)  →  h2c3d4e5f6g7 (P10)
  →  i3d4e5f6g7h8 (P11)
```
