# start-local.ps1 — one-shot local deploy for the Intelligence Platform
# Usage:  pwsh ./scripts/start-local.ps1
# Stop:   pwsh ./scripts/stop-local.ps1
#
# What this does:
#   1. Verifies Docker Desktop is running
#   2. Sanity-checks .env (must have VAULT_PATH pointing at your vault root)
#   3. Builds and starts the full stack with docker compose
#   4. Tails health until API + dashboard are reachable
#   5. Opens http://localhost:3000 in your default browser

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

Write-Host "==> Intelligence Platform — local deploy" -ForegroundColor Cyan
Write-Host "    Repo root: $root" -ForegroundColor DarkGray

# --- 1. Docker check --------------------------------------------------------
try {
    docker info *> $null
} catch {
    Write-Host "ERROR: Docker Desktop is not running. Start it and re-run." -ForegroundColor Red
    exit 1
}

# --- 2. .env sanity --------------------------------------------------------
if (-not (Test-Path ".env")) {
    Write-Host "ERROR: .env not found at repo root. Copy .env.example or ask Claude to regenerate it." -ForegroundColor Red
    exit 1
}
$envText = Get-Content .env -Raw
if ($envText -notmatch 'VAULT_PATH=') {
    Write-Host "ERROR: VAULT_PATH is missing in .env. The watcher won't know where your vault is." -ForegroundColor Red
    exit 1
}
$vaultLine = ($envText -split "`n" | Where-Object { $_ -match '^\s*VAULT_PATH=' } | Select-Object -First 1)
$vaultPath = ($vaultLine -split '=', 2)[1].Trim().Trim('"')
if (-not (Test-Path $vaultPath)) {
    Write-Host "ERROR: VAULT_PATH=$vaultPath does not exist on disk." -ForegroundColor Red
    exit 1
}
$rawDir = Join-Path $vaultPath "raw"
if (-not (Test-Path $rawDir)) {
    Write-Host "WARNING: $rawDir not found — the watcher will create empty subdirs on first run." -ForegroundColor Yellow
}
Write-Host "==> Vault: $vaultPath" -ForegroundColor Green

# --- 3. Build & start -------------------------------------------------------
Write-Host "==> docker compose build (this takes a few minutes the first time)" -ForegroundColor Cyan
docker compose -f infra/docker/docker-compose.yml --env-file .env build

Write-Host "==> docker compose up -d" -ForegroundColor Cyan
docker compose -f infra/docker/docker-compose.yml --env-file .env up -d

# --- 4. Wait for health -----------------------------------------------------
Write-Host "==> Waiting for API at http://localhost:8000/healthz ..." -ForegroundColor Cyan
$ok = $false
for ($i = 0; $i -lt 60; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8000/healthz" -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200) { $ok = $true; break }
    } catch { Start-Sleep -Seconds 2 }
}
if (-not $ok) {
    Write-Host "WARNING: API did not come up in 120s. Check: docker compose -f infra/docker/docker-compose.yml logs api" -ForegroundColor Yellow
} else {
    Write-Host "    API is up." -ForegroundColor Green
}

Write-Host "==> Waiting for dashboard at http://localhost:3000 ..." -ForegroundColor Cyan
$ok = $false
for ($i = 0; $i -lt 60; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200) { $ok = $true; break }
    } catch { Start-Sleep -Seconds 2 }
}
if ($ok) { Write-Host "    Dashboard is up." -ForegroundColor Green }

# --- 5. Trigger a refresh so anything already in raw/ gets ingested ---------
try {
    Invoke-WebRequest -Uri "http://localhost:8000/v1/ingest/refresh" -Method POST -UseBasicParsing -TimeoutSec 5 | Out-Null
    Write-Host "==> Triggered full re-scan of raw/" -ForegroundColor Green
} catch {
    Write-Host "    (skipped) Could not trigger /v1/ingest/refresh — watcher will pick up files on its 5-min scan." -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "✓ Stack is up:" -ForegroundColor Green
Write-Host "    Dashboard:  http://localhost:3000"
Write-Host "    API docs:   http://localhost:8000/docs"
Write-Host "    n8n:        http://localhost:5678"
Write-Host "    Meilisearch http://localhost:7700"
Write-Host ""
Write-Host "Logs:  docker compose -f infra/docker/docker-compose.yml logs -f"
Write-Host "Stop:  pwsh ./scripts/stop-local.ps1"

Start-Process "http://localhost:3000"
