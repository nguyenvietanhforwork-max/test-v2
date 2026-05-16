#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
echo "==> Stopping intelligence-platform stack..."
docker compose -f infra/docker/docker-compose.yml --env-file .env down
echo "    Done. To wipe volumes too: add  -v"
