# AI Evaluation Platform

**System of record for AI quality. Can we safely deploy?**

The AEP answers the hardest question in AI operations: given the latest model update, is the
system ready to ship? It does this through a full evidence chain — from versioned datasets and
prompts through scored evaluations, regression detection, and audited gate decisions with approvals.

## Key capabilities

| Capability | Description |
|---|---|
| **Trust-first results** | Every evaluation carries full provenance — model/prompt/dataset/metric versions, confidence, audit history |
| **Evaluation engine** | In-process execution: exact_match, contains, semantic similarity (TF-cosine, no ML deps) |
| **RAG evaluation** | TF-IDF retrieval with context_relevance, faithfulness, answer_relevance scorers |
| **Agent evaluation** | Trajectory scoring: tool_call_accuracy (F1), trajectory_score (Dice-LCS), task_completion |
| **Continuous evaluation** | Scheduled runs (APScheduler optional), A/B experiments, metric trend tracking |
| **Release gates** | Criteria-based gate decisions, mandatory approvals, audited overrides |
| **Offline-first** | Every workflow runs with Ollama + SQLite — no cloud required |
| **Audit trail** | Hash-chained append-only event log, tamper-evident verification endpoint |
| **API key auth + RBAC** | viewer / evaluator / approver / admin roles; rate limiting included |

## Quick start

```bash
cd backend
uv venv --python 3.12 .venv
uv pip install -e ".[dev]"
.venv/Scripts/python -m alembic upgrade head
.venv/Scripts/uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs` for the interactive API explorer.

## Status

All backend phases (P0–P11) are complete. Frontend pages are CI-gated (TypeScript + Vite build).
