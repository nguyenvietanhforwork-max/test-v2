# ============================================================
# install-task.ps1
# Dang ky Task Scheduler de auto-sync chay khi dang nhap Windows.
# Khong can quyen Admin (chay duoi user hien tai, an cua so).
# ============================================================
[CmdletBinding()]
param(
    [string]$TaskName = 'AutoSyncGitHub',
    [int]$DelayMinutes = 1
)
$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$VbsPath   = Join-Path $ScriptDir 'run-hidden.vbs'

if (-not (Test-Path $VbsPath)) {
    Write-Error "Khong tim thay $VbsPath"
    exit 1
}

# Xoa task cu neu co (de re-install sach se)
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Xoa task cu '$TaskName'..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

$Action  = New-ScheduledTaskAction -Execute 'wscript.exe' -Argument "`"$VbsPath`""

# Trigger: AtLogOn cho user hien tai
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
# Delay them 1 phut de mang + GitHub credential manager san sang
$Trigger.Delay = "PT${DelayMinutes}M"

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -ExecutionTimeLimit ([System.TimeSpan]::Zero) `
    -MultipleInstances IgnoreNew

$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description 'Auto-sync raw/*.md to GitHub (background, hidden window)' `
    -Force | Out-Null

Write-Host "`n[OK] Da dang ky Task Scheduler '$TaskName'." -ForegroundColor Green
Write-Host "  - Tu chay $DelayMinutes phut sau khi ban dang nhap Windows."
Write-Host "  - Quan ly: taskschd.msc -> Task Scheduler Library -> $TaskName"
Write-Host "  - Go bo: powershell -ExecutionPolicy Bypass -File uninstall-task.ps1"
Write-Host ""
Write-Host "Co the chay thu task ngay bay gio:" -ForegroundColor Yellow
Write-Host "  Start-ScheduledTask -TaskName $TaskName"
