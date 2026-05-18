#!/usr/bin/env bash
# start-local.sh — one-shot local deploy for the Intelligence Platform
# Usage:  ./scripts/start-local.sh
# Stop:   ./scripts/stop-local.sh

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

cyan() { printf "\033[36m%s\033[0m\n" "$*"; }
green() { printf "\033[32m%s\033[0m\n" "$*"; }
yellow() { printf "\033[33m%s\033[0m\n" "$*"; }
red() { printf "\033[31m%s\033[0m\n" "$*"; }

cyan "==> Intelligence Platform — local deploy"
echo "    Repo root: $ROOT"

# --- 1. Docker check --------------------------------------------------------
if ! docker info >/dev/null 2>&1; then
  red "ERROR: Docker is not running. Start Docker Desktop / dockerd and re-run."
  exit 1
fi

# --- 2. .env sanity --------------------------------------------------------
if [[ ! -f .env ]]; then
  red "ERROR: .env not found at repo root."
  exit 1
fi
VAULT_PATH=$(grep -E '^\s*VAULT_PATH=' .env | head -1 | cut -d= -f2- | tr -d '"')
if [[ -z "${VAULT_PATH:-}" ]]; then
  red "ERROR: VAULT_PATH is missing in .env."
  exit 1
fi
if [[ ! -d "$VAULT_PATH" ]]; then
  red "ERROR: VAULT_PATH=$VAULT_PATH does not exist."
  exit 1
fi
green "==> Vault: $VAULT_PATH"

# --- 3. Build & start -------------------------------------------------------
cyan "==> docker compose build"
docker compose -f infra/docker/docker-compose.yml --env-file .env build

cyan "==> docker compose up -d"
docker compose -f infra/docker/docker-compose.yml --env-file .env up -d

# --- 4. Wait for health -----------------------------------------------------
cyan "==> Waiting for API at http://localhost:8000/healthz ..."
for i in $(seq 1 60); do
  if curl -fsS http://localhost:8000/healthz >/dev/null 2>&1; then
    green "    API is up."
    break
  fi
  sleep 2
done

cyan "==> Waiting for dashboard at http://localhost:3000 ..."
for i in $(seq 1 60); do
  if curl -fsS http://localhost:3000 >/dev/null 2>&1; then
    green "    Dashboard is up."
    break
  fi
  sleep 2
done

# --- 5. Trigger refresh -----------------------------------------------------
curl -fsS -X POST http://localhost:8000/v1/ingest/refresh >/dev/null 2>&1 \
  && green "==> Triggered full re-scan of raw/" \
  || yellow "    (skipped) /v1/ingest/refresh not reachable; watcher will rescan in <=5min."

echo ""
green "✓ Stack is up:"
echo "    Dashboard:   http://localhost:3000"
echo "    API docs:    http://localhost:8000/docs"
echo "    n8n:         http://localhost:5678"
echo "    Meilisearch: http://localhost:7700"
echo ""
echo "Logs:  docker compose -f infra/docker/docker-compose.yml logs -f"
echo "Stop:  ./scripts/stop-local.sh"
