# cleanup-legacy.ps1
# v3 restructure (2026-05-18) -- Physically moves retired systems into legacy/
# and deletes regeneratable build artifacts.
#
# USAGE:
#   Dry run (default -- prints what would happen):
#     powershell -ExecutionPolicy Bypass -File .\scripts\cleanup-legacy.ps1
#   Actually do it:
#     powershell -ExecutionPolicy Bypass -File .\scripts\cleanup-legacy.ps1 -Apply
#
# SAFETY:
#   - Never overwrites: if a target in legacy/ already exists, the move is skipped.
#   - All operations are logged to logs/cleanup-legacy-<timestamp>.log
#   - Vault folders (raw/, wiki/, Processed/, _templates/) are never touched.

param(
    [switch]$Apply = $false
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logDir = Join-Path $repoRoot "logs"
if (!(Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
$logFile = Join-Path $logDir "cleanup-legacy-$timestamp.log"

function Log {
    param([string]$msg)
    $line = "[$(Get-Date -Format 'HH:mm:ss')] $msg"
    Write-Host $line
    Add-Content -Path $logFile -Value $line
}

$mode = if ($Apply) { "APPLY" } else { "DRY RUN" }
Log "===================================================="
Log "cleanup-legacy.ps1 -- mode: $mode"
Log "Repo root: $repoRoot"
Log "Log file:  $logFile"
Log "===================================================="

# --- Step 1: Ensure legacy/ destination directories exist ---
$legacyDirs = @(
    "legacy",
    "legacy\intelligence-platform",
    "legacy\nextjs-dashboard",
    "legacy\v1-dashboard",
    "legacy\static-html",
    "legacy\static-html\offline-trials",
    "legacy\k8s",
    "legacy\deploy-alternates",
    "legacy\root-scripts",
    "legacy\prompts-archive",
    "legacy\docs",
    "legacy\duplicates"
)
foreach ($d in $legacyDirs) {
    $full = Join-Path $repoRoot $d
    if (!(Test-Path $full)) {
        Log "MKDIR  $d"
        if ($Apply) { New-Item -ItemType Directory -Path $full -Force | Out-Null }
    }
}

# --- Step 2: Move retired trees ---
# Format: source (relative) → destination subdir under legacy/
$moves = @(
    # Parallel monorepo
    @{ src = "intelligence-platform";          dst = "legacy\intelligence-platform" },

    # Next.js dashboard (apps/web)
    @{ src = "apps\web";                        dst = "legacy\nextjs-dashboard\web" },

    # V1 dashboard + companion JSON
    @{ src = "index.html";                      dst = "legacy\v1-dashboard\index.html" },
    @{ src = "news_database.json";              dst = "legacy\v1-dashboard\news_database.json" },
    @{ src = "news-dashboard-soulslab.html";    dst = "legacy\v1-dashboard\news-dashboard-soulslab.html" },
    @{ src = "outputs\atlas-dashboard.html";    dst = "legacy\v1-dashboard\atlas-dashboard.html" },
    @{ src = "outputs\dashboard.html";          dst = "legacy\v1-dashboard\dashboard.html" },
    @{ src = "outputs\sync-dashboard.html";     dst = "legacy\v1-dashboard\sync-dashboard.html" },

    # Static HTML experiments
    @{ src = "demo\dashboard.html";             dst = "legacy\static-html\demo-dashboard.html" },
    @{ src = "demo";                            dst = "legacy\static-html\demo-folder" },
    @{ src = "offline dashboard trial";         dst = "legacy\static-html\offline-trials" },

    # K8s (forbidden by ADR-010)
    @{ src = "infra\k8s";                       dst = "legacy\k8s" },

    # Deploy alternates
    @{ src = "fly.toml";                        dst = "legacy\deploy-alternates\fly.toml" },
    @{ src = "apps\api\Procfile";               dst = "legacy\deploy-alternates\api-Procfile" },
    @{ src = "apps\api\railway.json";           dst = "legacy\deploy-alternates\api-railway.json" },

    # Root scripts superseded by packages/automation + scripts/
    @{ src = "process_news.py";                 dst = "legacy\root-scripts\process_news.py" },
    @{ src = "generate.py";                     dst = "legacy\root-scripts\generate.py" },
    @{ src = "process_news_agent.py";           dst = "legacy\root-scripts\process_news_agent.py" },

    # Prompt / spec archive
    @{ src = "agent.md";                                                  dst = "legacy\prompts-archive\agent.md" },
    @{ src = "production_ai_intelligence_platform_prompt.md";             dst = "legacy\prompts-archive\production_ai_intelligence_platform_prompt.md" },
    @{ src = "infrastructure_prompt.md";                                  dst = "legacy\prompts-archive\infrastructure_prompt.md" },
    @{ src = "dashboard_design_prompt.md";                                dst = "legacy\prompts-archive\dashboard_design_prompt.md" },
    @{ src = "ai_dashboard_redesign_prompt.md";                           dst = "legacy\prompts-archive\ai_dashboard_redesign_prompt.md" },
    @{ src = "usage_guide.md";                                            dst = "legacy\prompts-archive\usage_guide.md" },
    @{ src = "ai_intelligence_prompt_bundle.zip";                         dst = "legacy\prompts-archive\ai_intelligence_prompt_bundle.zip" }
)

foreach ($m in $moves) {
    $src = Join-Path $repoRoot $m.src
    $dst = Join-Path $repoRoot $m.dst
    if (!(Test-Path $src)) {
        Log "SKIP   (source missing)  $($m.src)"
        continue
    }
    if (Test-Path $dst) {
        Log "SKIP   (target exists)   $($m.dst)"
        continue
    }
    $dstParent = Split-Path -Parent $dst
    if (!(Test-Path $dstParent)) {
        Log "MKDIR  $dstParent"
        if ($Apply) { New-Item -ItemType Directory -Path $dstParent -Force | Out-Null }
    }
    Log "MOVE   $($m.src) -> $($m.dst)"
    if ($Apply) {
        Move-Item -LiteralPath $src -Destination $dst
    }
}

# --- Step 3: Delete regeneratable build artifacts ---
$junkPatterns = @(
    "**\node_modules",
    "**\__pycache__",
    "**\.next",
    "**\.pytest_cache",
    "**\.mypy_cache",
    "**\.ruff_cache",
    "**\.venv",
    "**\dist",
    "**\*.pyc"
)

Log "----------------------------------------------------"
Log "Scanning for regeneratable junk to delete..."
foreach ($pat in $junkPatterns) {
    $found = Get-ChildItem -Path $repoRoot -Recurse -Force -ErrorAction SilentlyContinue |
             Where-Object { $_.FullName -like "*\$($pat -replace '\\\*\*\\', '\')" -or
                            $_.Name -like ($pat -replace '\*\*\\', '') }
    # Simpler: explicit per-pattern handling
}

# Explicit handling -- more reliable than glob expansion:
$nodeModules = Get-ChildItem -Path $repoRoot -Recurse -Directory -Force -Filter "node_modules" -ErrorAction SilentlyContinue
foreach ($nm in $nodeModules) {
    Log "DELETE node_modules: $($nm.FullName)"
    if ($Apply) { Remove-Item -LiteralPath $nm.FullName -Recurse -Force -ErrorAction SilentlyContinue }
}

$pycaches = Get-ChildItem -Path $repoRoot -Recurse -Directory -Force -Filter "__pycache__" -ErrorAction SilentlyContinue
foreach ($pc in $pycaches) {
    Log "DELETE __pycache__: $($pc.FullName)"
    if ($Apply) { Remove-Item -LiteralPath $pc.FullName -Recurse -Force -ErrorAction SilentlyContinue }
}

$nextDirs = Get-ChildItem -Path $repoRoot -Recurse -Directory -Force -Filter ".next" -ErrorAction SilentlyContinue
foreach ($nd in $nextDirs) {
    Log "DELETE .next: $($nd.FullName)"
    if ($Apply) { Remove-Item -LiteralPath $nd.FullName -Recurse -Force -ErrorAction SilentlyContinue }
}

$pycFiles = Get-ChildItem -Path $repoRoot -Recurse -File -Force -Filter "*.pyc" -ErrorAction SilentlyContinue
foreach ($pf in $pycFiles) {
    Log "DELETE *.pyc: $($pf.FullName)"
    if ($Apply) { Remove-Item -LiteralPath $pf.FullName -Force -ErrorAction SilentlyContinue }
}

# --- Step 4: Promote canonical artifacts ---
# Copy news-dashboard-v2.html to apps/dashboard/index.html as the canonical dashboard.
$dashboardSrc = Join-Path $repoRoot "news-dashboard-v2.html"
$dashboardDst = Join-Path $repoRoot "apps\dashboard\index.html"
$dashboardDstDir = Join-Path $repoRoot "apps\dashboard"

if (Test-Path $dashboardSrc) {
    if (!(Test-Path $dashboardDstDir)) {
        Log "MKDIR  apps\dashboard"
        if ($Apply) { New-Item -ItemType Directory -Path $dashboardDstDir -Force | Out-Null }
    }
    if (Test-Path $dashboardDst) {
        Log "SKIP   (canonical dashboard already exists)  apps\dashboard\index.html"
    } else {
        Log "COPY   news-dashboard-v2.html -> apps\dashboard\index.html  (canonical MVP per ADR-002)"
        if ($Apply) { Copy-Item -LiteralPath $dashboardSrc -Destination $dashboardDst }
    }
} else {
    Log "WARN   news-dashboard-v2.html not found at repo root -- canonical dashboard NOT populated."
}

# --- Step 5: Summary ---
Log "===================================================="
Log "Done. Mode: $mode"
if (!$Apply) {
    Log "This was a DRY RUN. Re-run with -Apply to execute the operations above."
} else {
    Log "Operations complete. Review legacy/ before considering further deletion."
}
Log "===================================================="
