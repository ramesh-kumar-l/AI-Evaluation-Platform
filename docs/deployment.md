# Deployment

## Local development (offline-first)

```bash
cd backend
uv venv --python 3.12 .venv
uv pip install -e ".[dev]"
.venv/Scripts/python -m alembic upgrade head
.venv/Scripts/uvicorn app.main:app --reload
```

No external services required. SQLite is used automatically when `AEP_DATABASE_URL` is not set.

## Docker Compose (local stack with Postgres)

```bash
docker compose -f infra/docker-compose.yml up
```

This starts Postgres+pgvector, the backend API, and the frontend shell.

## Docker Compose (production)

1. Copy `.env.prod.example` → `.env.prod` and fill in values:

```env
AEP_DB_USER=aep
AEP_DB_PASSWORD=<strong-password>
AEP_ADMIN_SECRET=<strong-secret>
AEP_OLLAMA_BASE_URL=http://your-ollama-host:11434
```

2. Run:

```bash
docker compose -f infra/docker-compose.prod.yml --env-file .env.prod up -d
```

3. Bootstrap the first API key:

```bash
curl -X POST http://localhost:8000/admin/api-keys \
  -H "X-Admin-Secret: <your-admin-secret>" \
  -H "Content-Type: application/json" \
  -d '{"name": "admin-key", "role": "admin"}'
```

The response includes `raw_key` — **store it securely, it is shown only once.**

## Kubernetes

Apply manifests in order:

```bash
kubectl apply -f infra/k8s/namespace.yaml
kubectl apply -f infra/k8s/configmap.yaml
# Fill in secret.yaml values first:
kubectl apply -f infra/k8s/secret.yaml
kubectl apply -f infra/k8s/deployment.yaml
kubectl apply -f infra/k8s/service.yaml
kubectl apply -f infra/k8s/ingress.yaml
kubectl apply -f infra/k8s/hpa.yaml
```

### Security context
- Non-root user (UID 1000)
- Read-only root filesystem
- All Linux capabilities dropped
- `allowPrivilegeEscalation: false`

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `AEP_ENV` | `local` | `local` / `test` / `production` |
| `AEP_DATABASE_URL` | *(SQLite)* | PostgreSQL URL e.g. `postgresql+psycopg://...` |
| `AEP_LOG_JSON` | `false` | Structured JSON logs for production |
| `AEP_API_AUTH_ENABLED` | `false` | Enable API key auth and RBAC |
| `AEP_ADMIN_SECRET` | *(none)* | Secret for `X-Admin-Secret` bootstrap header |
| `AEP_RATE_LIMIT_PER_MINUTE` | `1000` | Sliding-window rate limit per key |
| `AEP_OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | *(none)* | OTel exporter; enables telemetry when set |

## APScheduler (optional)

To enable automatic cron-based evaluation scheduling:

```bash
uv pip install -e ".[scheduler]"
```

Without APScheduler installed, manual triggers via `POST /observe/schedules/{key}/trigger` always work.
