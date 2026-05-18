# stop-local.ps1 — bring the local stack down
$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

Write-Host "==> Stopping intelligence-platform stack..." -ForegroundColor Cyan
docker compose -f infra/docker/docker-compose.yml --env-file .env down
Write-Host "    Done. Volumes (pgdata, meilidata, n8ndata) preserved." -ForegroundColor Green
Write-Host "    To wipe data too: docker compose -f infra/docker/docker-compose.yml --env-file .env down -v"
