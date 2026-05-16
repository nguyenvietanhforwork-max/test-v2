# Atlas — Deployment Playbook

## 1. Environments

| Env | Stack | Notes |
|---|---|---|
| `dev` | `docker compose` on laptop | hot-reload, all services local |
| `staging` | k8s single-node (Talos, k3s) | mirrors prod, smaller resources |
| `prod` | k8s cluster (3+ nodes) | HA postgres, replicated meili |

## 2. Dev — `docker compose up`

```yaml
# docker-compose.yml (excerpt — see infra/compose/docker-compose.yml for full)
services:
  web:        { build: ./infra/docker/web.Dockerfile,     ports: ["3000:3000"] }
  api:        { build: ./infra/docker/api.Dockerfile,     ports: ["8000:8000"] }
  worker:     { build: ./infra/docker/worker.Dockerfile }
  watcher:    { build: ./infra/docker/watcher.Dockerfile, volumes: [./raw:/vault/raw:ro, ./wiki:/vault/wiki] }
  pdf:        { build: ./infra/docker/pdf.Dockerfile,     ports: ["4000:4000"] }
  postgres:   { image: pgvector/pgvector:pg16, ports: ["5432:5432"] }
  redis:      { image: redis:7-alpine }
  meili:      { image: getmeili/meilisearch:v1.6 }
  minio:      { image: minio/minio, ports: ["9000:9000", "9001:9001"] }
```

## 3. Secrets

Required `.env` keys:

```env
# core
NODE_ENV=production
LOG_LEVEL=info

# auth
JWT_SECRET=change-me
JWT_ACCESS_TTL=3600
JWT_REFRESH_TTL=2592000

# db
POSTGRES_HOST=postgres
POSTGRES_USER=atlas
POSTGRES_PASSWORD=...
POSTGRES_DB=atlas

# redis
REDIS_URL=redis://redis:6379/0

# meili
MEILI_HOST=http://meili:7700
MEILI_MASTER_KEY=...

# llm
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...
DEFAULT_MODEL=claude-sonnet-4-6
FALLBACK_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-large

# minio
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=...
MINIO_SECRET_KEY=...
MINIO_BUCKET=atlas-pdfs

# vault paths (inside containers)
VAULT_RAW=/vault/raw
VAULT_WIKI=/vault/wiki
VAULT_PROCESSED=/vault/Processed
```

## 4. First-boot checklist

1. `cp .env.example .env` and fill secrets.
2. `docker compose up -d postgres redis meilisearch minio`.
3. Wait for postgres ready: `docker compose exec postgres pg_isready -U atlas`.
4. `docker compose run --rm api alembic upgrade head`.
5. `docker compose run --rm api python -m app.scripts.seed`.
6. `docker compose up -d` (everything).
7. Visit `http://localhost:3000`, create admin user via `/auth/register?invite_code=...`.
8. Drop a sample clipping in `raw/news/` to verify pipeline.

## 5. Prod — Kubernetes

Manifests under `infra/k8s/`. Apply order:

```
kubectl create namespace atlas
kubectl apply -f infra/k8s/secrets/
kubectl apply -f infra/k8s/postgres.statefulset.yaml
kubectl apply -f infra/k8s/redis.deploy.yaml
kubectl apply -f infra/k8s/meili.deploy.yaml
kubectl apply -f infra/k8s/minio.statefulset.yaml
kubectl apply -f infra/k8s/api.deploy.yaml
kubectl apply -f infra/k8s/worker.deploy.yaml
kubectl apply -f infra/k8s/web.deploy.yaml
kubectl apply -f infra/k8s/ingress.yaml
```

Resource requests (per replica):

| Service | CPU | Mem | Replicas |
|---|---|---|---|
| web | 250m | 512Mi | 2 |
| api | 500m | 1Gi | 3 |
| worker | 1000m | 2Gi | 2 (auto-scale to 8) |
| watcher | 100m | 256Mi | 1 (only) |
| pdf | 500m | 1Gi | 2 |
| postgres | 2000m | 4Gi | 1 primary + 2 replicas |
| redis | 250m | 512Mi | 1 |
| meili | 500m | 1Gi | 2 |
| minio | 250m | 512Mi | 4 |

## 6. CI/CD

GitHub Actions outline (`.github/workflows/ci.yml`):

```
jobs:
  test-api:    pytest, mypy, ruff
  test-web:    pnpm typecheck, pnpm test, pnpm lint
  build:      docker buildx bake → ghcr.io
  deploy-stg:  on push to main → kubectl rollout
  deploy-prod: on tag v* → kubectl rollout + smoke tests
```

## 7. Observability

- Logs: Promtail → Loki → Grafana.
- Metrics: Prometheus scrape `/metrics` on api + worker.
- Traces: OpenTelemetry SDK → Tempo.
- Alerts: Grafana → Slack webhook for: DLQ > 5, daily brief failure, api p95 > 500ms.

## 8. Backups

- Postgres: nightly `pg_basebackup` → S3 (encrypted).
- MinIO: lifecycle to Glacier after 90d.
- Vault filesystem: separate restic backup, hourly increments.
