# ============================================================
# uninstall-task.ps1
# Xoa Task Scheduler 'AutoSyncGitHub'.
# ============================================================
[CmdletBinding()]
param([string]$TaskName = 'AutoSyncGitHub')
$ErrorActionPreference = 'Stop'

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $existing) {
    Write-Host "Khong tim thay task '$TaskName'." -ForegroundColor Yellow
    exit 0
}

Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
Write-Host "[OK] Da xoa task '$TaskName'." -ForegroundColor Green
