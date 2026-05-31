# API Reference

Interactive docs are served at `http://localhost:8000/docs` (Swagger UI) and
`http://localhost:8000/redoc` (ReDoc) when the backend is running.

## Authentication

When `AEP_API_AUTH_ENABLED=true` every request (except `/health` and `/ready`) must carry:

```
X-API-Key: aep_<your-key>
```

Keys are created via the admin bootstrap flow (see [Deployment](deployment.md)).

## Role permissions

| Endpoint group | Minimum role |
|---|---|
| GET any resource | viewer |
| POST evaluations, runs, comparisons | evaluator |
| POST gate approvals | approver |
| POST /admin/api-keys | admin secret |

## Endpoint summary

### Core

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness probe |
| GET | `/ready` | Readiness probe (DB ping) |

### Providers & Models

| Method | Path | Description |
|--------|------|-------------|
| POST | `/providers` | Register a provider |
| GET | `/providers` | List providers |
| POST | `/providers/models` | Register a model |
| GET | `/providers/models` | List models |

### Prompts / Datasets / Metrics

Standard versioned CRUD: `POST`, `GET`, `GET /{key}`, `GET /{key}/versions`.

### Evaluations

| Method | Path | Description |
|--------|------|-------------|
| POST | `/evaluations` | Run a dataset evaluation |
| GET | `/evaluations` | List evaluations |
| GET | `/evaluations/{id}/results` | Per-item results |

### Comparisons

`POST /comparisons` — compare two evaluations; returns metric deltas and regression flags.

### Release Gates

`POST /gates` → `POST /gates/{key}/evaluate` → `POST /decisions/{id}/approve`

### RAG Evaluation

`/rag/corpora` CRUD → `/corpora/{key}/documents` ingest → `/rag/evaluations` run

### Agent Evaluation

`/agent/runs` submit trajectory → `/agent/evaluations` run scoring

### Observability

`/observe/schedules` CRUD + trigger → `/observe/experiments` → `/observe/trends`

### Admin

| Method | Path | Description |
|--------|------|-------------|
| POST | `/admin/api-keys` | Create a key (requires X-Admin-Secret) |
| GET | `/admin/api-keys` | List keys |
| DELETE | `/admin/api-keys/{id}` | Revoke a key |
