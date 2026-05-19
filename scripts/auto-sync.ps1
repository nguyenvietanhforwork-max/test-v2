# =============================================================
# auto-sync.ps1 - Auto sync raw/*.md to GitHub
# ASCII only on purpose: PowerShell 5.1 reads .ps1 files without
# a BOM as ANSI, which corrupts non-ASCII characters. Keep this
# file ASCII-clean.
# =============================================================

[CmdletBinding()]
param(
    [switch]$RunOnce
)

$ErrorActionPreference = 'Stop'

# Force UTF-8 everywhere so Vietnamese filenames do not get mojibake'd
# when traveling between PowerShell and git on Windows.
# Without this, "Việt Nam.md" turns into octal escapes like \341\273\207
# and git cannot find the file.
try {
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [Console]::OutputEncoding = $utf8NoBom
    [Console]::InputEncoding  = $utf8NoBom
    $OutputEncoding           = $utf8NoBom
} catch { }

# ----- Paths -----
$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ConfigPath = Join-Path $ScriptDir 'config.json'

if (-not (Test-Path $ConfigPath)) {
    Write-Host "ERROR: Khong tim thay config.json o $ConfigPath" -ForegroundColor Red
    exit 1
}

$cfg = Get-Content $ConfigPath -Raw -Encoding utf8 | ConvertFrom-Json

# Required keys
foreach ($k in 'RepoPath','RemoteName','RemoteUrl','IntervalSeconds') {
    if (-not $cfg.PSObject.Properties[$k]) {
        Write-Host "ERROR: config.json thieu khoa: $k" -ForegroundColor Red
        exit 1
    }
}

$RepoPath      = $cfg.RepoPath
$LogDir        = Join-Path $RepoPath 'logs'
$LogPath       = Join-Path $LogDir   'auto-sync.log'
$StatusPath    = Join-Path $LogDir   'status.json'
$LockPath      = Join-Path $LogDir   'auto-sync.lock'
$DashboardDir  = Join-Path $RepoPath 'outputs'
$DashboardPath = Join-Path $DashboardDir 'sync-dashboard.html'

if (-not (Test-Path $LogDir))       { New-Item -ItemType Directory -Force -Path $LogDir       | Out-Null }
if (-not (Test-Path $DashboardDir)) { New-Item -ItemType Directory -Force -Path $DashboardDir | Out-Null }

# Dashboard template - dollar-quoted (single-quote here-string), no PS interpolation.
# Placeholder __SYNC_STATUS_JSON__ se duoc thay bang JSON state moi cycle.
$DashboardTemplate = @'
<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<title>Auto-sync Dashboard</title>
<meta http-equiv="refresh" content="10">
<style>
:root{color-scheme:dark}
body{font-family:'Segoe UI',Tahoma,sans-serif;background:#0e1116;color:#e6edf3;padding:24px;max-width:920px;margin:auto}
h1{margin:0 0 6px 0}.sub{color:#8b949e;margin-bottom:18px}
.card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px 18px;margin-bottom:16px}
.row{display:flex;justify-content:space-between;gap:12px;padding:4px 0;border-bottom:1px dashed #21262d}
.row:last-child{border-bottom:none}.label{color:#8b949e}
.mono{font-family:Consolas,'Courier New',monospace;font-size:13px;word-break:break-all}
table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:6px 8px;border-bottom:1px solid #21262d;font-size:13px}
th{color:#8b949e;font-weight:600}
.pill{display:inline-block;padding:2px 10px;border-radius:12px;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.3px}
.pill.success{background:#1f3a25;color:#3fb950}.pill.no-change{background:#1f2a3a;color:#58a6ff}
.pill.error{background:#3a1f1f;color:#f85149}.pill.warn{background:#3a2f1f;color:#d29922}
.pill.running{background:#2f2f3a;color:#bbb}.pill.init{background:#2f2f3a;color:#bbb}
h3{margin:0 0 10px 0;font-size:14px;color:#8b949e;text-transform:uppercase;letter-spacing:.5px}
</style>
</head>
<body>
<h1>Auto-sync GitHub</h1>
<div class="sub">Auto-refresh moi 10 giay. Du lieu nhung truc tiep boi auto-sync.ps1.</div>
<div class="card" id="overview"></div>
<div class="card">
<h3>Recent events</h3>
<table id="events"><thead><tr><th>Thoi gian</th><th>Status</th><th>Changes</th><th>Message</th></tr></thead><tbody></tbody></table>
</div>
<script>
window.SYNC_STATUS = __SYNC_STATUS_JSON__;
function esc(s){return String(s==null?'':s).replace(/[&<>]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c];});}
(function render(){
  var s=window.SYNC_STATUS||{};var st=s.LastStatus||'init';
  var pill='<span class="pill '+esc(st)+'">'+esc(st)+'</span>';
  var rows=[
    ['Status',pill,false],
    ['Branch',esc(s.Branch||'-'),true],
    ['Remote',esc(s.RemoteUrl||'-'),true],
    ['Repo',esc(s.RepoPath||'-'),true],
    ['Last attempt',esc(s.LastAttemptAt||'-'),false],
    ['Last success',esc(s.LastSuccessAt||'-'),false],
    ['Last failure',esc(s.LastFailureAt||'-'),false],
    ['Total commits',esc(s.TotalCommits),false],
    ['Total failures',esc(s.TotalFailures),false],
    ['Consecutive fails',esc(s.ConsecutiveFails),false],
    ['PID',esc(s.PID),true],
    ['Last message',esc(s.LastMessage),true]
  ];
  document.getElementById('overview').innerHTML=rows.map(function(r){
    return '<div class="row"><span class="label">'+r[0]+'</span><span'+(r[2]?' class="mono"':'')+'>'+r[1]+'</span></div>';
  }).join('');
  var ev=(s.Recent||[]).map(function(e){
    return '<tr><td class="mono">'+esc(e.ts)+'</td><td><span class="pill '+esc(e.status)+'">'+esc(e.status)+'</span></td><td>'+esc(e.changes)+'</td><td class="mono">'+esc(e.message)+'</td></tr>';
  }).join('');
  document.querySelector('#events tbody').innerHTML=ev||'<tr><td colspan="4" class="label">Chua co event nao.</td></tr>';
})();
</script>
</body>
</html>
'@

# ----- Helpers: read config with default -----
function Get-Cfg($key, $default) {
    if ($cfg.PSObject.Properties[$key]) {
        $v = $cfg.$key
        if ($null -ne $v -and $v -ne '') { return $v }
    }
    return $default
}

$WatchPath     = Get-Cfg 'WatchPath' 'raw'
$FilePattern   = Get-Cfg 'FilePattern' '*.md'
$MaxLogMB      = [int](Get-Cfg 'MaxLogSizeMB' 10)
$PullBefore    = [bool](Get-Cfg 'PullBeforePush' $true)
$CommitTmpl    = Get-Cfg 'CommitMessageTemplate' 'Auto-sync {timestamp} ({changes} files)'
$QuietNoChange = [bool](Get-Cfg 'QuietWhenNoChanges' $true)
$NetHost       = Get-Cfg 'NetworkTestHost' 'github.com'
$MaxRetries    = [int](Get-Cfg 'MaxRetries' 5)
$RetryBase     = [int](Get-Cfg 'RetryBaseDelaySeconds' 5)
$Interval      = [int](Get-Cfg 'IntervalSeconds' 60)

# ----- State -----
$script:State = @{
    StartedAt        = (Get-Date).ToString('o')
    Branch           = $null
    LastStatus       = 'init'
    LastMessage      = ''
    LastAttemptAt    = $null
    LastSuccessAt    = $null
    LastFailureAt    = $null
    TotalCommits     = 0
    TotalFailures    = 0
    ConsecutiveFails = 0
    LastChanges      = 0
    Recent           = @()
    RepoPath         = $RepoPath
    RemoteUrl        = $cfg.RemoteUrl
    PID              = $PID
}

# ----- Logging -----
function Write-Log {
    param(
        [Parameter(Mandatory)][string]$Message,
        [ValidateSet('INFO','WARN','ERROR','DEBUG')][string]$Level = 'INFO'
    )
    $ts   = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    $line = "[$ts] [$Level] $Message"

    try {
        if (Test-Path $LogPath) {
            $sizeMB = (Get-Item $LogPath).Length / 1MB
            if ($sizeMB -gt $MaxLogMB) {
                $bak = "$LogPath.1"
                if (Test-Path $bak) { Remove-Item $bak -Force }
                Move-Item $LogPath $bak -Force
            }
        }
    } catch { }

    Add-Content -Path $LogPath -Value $line -Encoding utf8
    if ($Level -ne 'DEBUG') {
        Write-Host $line
    } elseif ($VerbosePreference -ne 'SilentlyContinue') {
        Write-Host $line -ForegroundColor DarkGray
    }
}

# ----- Status snapshot -----
function Save-Status {
    param(
        [string]$Status,
        [string]$Message = '',
        [int]$Changes = 0
    )
    $script:State.LastStatus    = $Status
    $script:State.LastMessage   = $Message
    $script:State.LastAttemptAt = (Get-Date).ToString('o')
    $script:State.LastChanges   = $Changes

    if ($Status -eq 'success' -or $Status -eq 'no-change') {
        $script:State.LastSuccessAt    = $script:State.LastAttemptAt
        $script:State.ConsecutiveFails = 0
        if ($Status -eq 'success') { $script:State.TotalCommits++ }
    } elseif ($Status -eq 'error' -or $Status -eq 'warn') {
        $script:State.LastFailureAt    = $script:State.LastAttemptAt
        $script:State.ConsecutiveFails++
        $script:State.TotalFailures++
    }

    $entry = @{ ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss'); status = $Status; message = $Message; changes = $Changes }
    $tail  = @($script:State.Recent | Select-Object -First 19)
    $script:State.Recent = @($entry) + $tail

    try {
        $script:State | ConvertTo-Json -Depth 6 | Set-Content -Path $StatusPath -Encoding utf8
    } catch {
        Write-Log "Khong ghi duoc status.json: $_" 'WARN'
    }

    # Cung viet luon dashboard HTML voi du lieu nhung san - tranh CORS file://
    try {
        $compact = $script:State | ConvertTo-Json -Depth 6 -Compress
        # Escape any </ that could prematurely close <script>
        $compact = $compact -replace '</', '<\/'
        $html = $DashboardTemplate.Replace('__SYNC_STATUS_JSON__', $compact)
        Set-Content -Path $DashboardPath -Value $html -Encoding utf8
    } catch {
        Write-Log "Khong ghi duoc dashboard: $_" 'WARN'
    }
}

# ----- Lock (single instance) -----
function Acquire-Lock {
    if (Test-Path $LockPath) {
        $oldPid = (Get-Content $LockPath -ErrorAction SilentlyContinue | Select-Object -First 1)
        if ($oldPid -and ($oldPid -as [int])) {
            $proc = Get-Process -Id ([int]$oldPid) -ErrorAction SilentlyContinue
            if ($proc) {
                throw "Da co instance khac dang chay (PID=$oldPid). Chay stop-sync.bat truoc, hoac dung -RunOnce."
            }
        }
        Remove-Item $LockPath -Force -ErrorAction SilentlyContinue
    }
    $PID | Out-File -FilePath $LockPath -Encoding ascii -Force
}

function Release-Lock {
    if (Test-Path $LockPath) {
        try { Remove-Item $LockPath -Force -ErrorAction SilentlyContinue } catch { }
    }
}

# ----- Safe git invocation -----
# Wraps git so that:
#  1) stderr from git (which carries normal info like "From <url>") never
#     bubbles up as a terminating error under $ErrorActionPreference='Stop'.
#  2) Output is always plain strings, never ErrorRecord objects.
function Invoke-Git {
    [CmdletBinding()]
    param([Parameter(Mandatory, Position=0)][string[]]$GitArgs)

    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $raw   = & git -C $RepoPath @GitArgs 2>&1
        $code  = $LASTEXITCODE
        $lines = @($raw | ForEach-Object { "$_" })
        return @{ Output = ($lines -join "`n"); ExitCode = $code }
    }
    finally {
        $ErrorActionPreference = $prev
    }
}

function Test-Network {
    if (-not $NetHost) { return $true }
    try {
        return [bool](Test-Connection -ComputerName $NetHost -Count 1 -Quiet -ErrorAction SilentlyContinue)
    } catch { return $false }
}

function Resolve-Branch {
    if ($cfg.PSObject.Properties['Branch'] -and $cfg.Branch) { return $cfg.Branch }
    $r = Invoke-Git 'rev-parse','--abbrev-ref','HEAD'
    if ($r.ExitCode -ne 0) {
        throw "Khong xac dinh duoc branch: $($r.Output)"
    }
    return $r.Output.Trim()
}

# ----- One sync cycle -----
function Invoke-SyncCycle {
    Save-Status -Status 'running' -Message 'Bat dau cycle'

    # 1) Status, scoped to WatchPath
    $r = Invoke-Git 'status','--porcelain','--untracked-files=all','--',$WatchPath
    if ($r.ExitCode -ne 0) {
        throw "git status loi: $($r.Output)"
    }

    # 2) Filter to FilePattern (default *.md)
    $ext = ($FilePattern -replace '^\*','').ToLower()  # ".md"
    $changed = New-Object System.Collections.Generic.List[string]
    foreach ($line in ($r.Output -split "[\r\n]+")) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        if ($line.Length -lt 3) { continue }
        $path = $line.Substring(3).Trim()
        if ($path -match '->') { $path = ($path -split '->')[-1].Trim() }
        if ($path.StartsWith('"') -and $path.EndsWith('"')) {
            $path = $path.Substring(1, $path.Length - 2)
        }
        if ($path.ToLower().EndsWith($ext)) {
            [void]$changed.Add($path)
        }
    }

    if ($changed.Count -eq 0) {
        if (-not $QuietNoChange) {
            Write-Log "Khong co thay doi $FilePattern trong $WatchPath/. Bo qua." 'INFO'
        }
        Save-Status -Status 'no-change' -Message 'Khong co thay doi'
        return
    }

    Write-Log "Phat hien $($changed.Count) thay doi $FilePattern trong $WatchPath/" 'INFO'

    # 3) Add each matching file
    foreach ($f in $changed) {
        $r = Invoke-Git 'add','--',$f
        if ($r.ExitCode -ne 0) {
            Write-Log ("git add loi cho {0}: {1}" -f $f, $r.Output) 'WARN'
        }
    }

    # 4) Verify something is staged
    $r = Invoke-Git 'diff','--cached','--name-only'
    $stagedCount = (@($r.Output -split "[\r\n]+" | Where-Object { $_ })).Count
    if ($stagedCount -eq 0) {
        Write-Log "Khong co gi de commit sau khi add. Bo qua." 'INFO'
        Save-Status -Status 'no-change' -Message 'Khong co gi de commit'
        return
    }

    # 5) Commit
    $msg = $CommitTmpl `
        -replace '\{timestamp\}', (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') `
        -replace '\{changes\}',   $stagedCount

    $r = Invoke-Git 'commit','-m',$msg
    if ($r.ExitCode -ne 0) {
        if ($r.Output -match 'nothing to commit') {
            Save-Status -Status 'no-change' -Message 'nothing to commit'
            return
        }
        throw "git commit loi: $($r.Output)"
    }
    Write-Log "Commit thanh cong: $stagedCount files" 'INFO'

    # 6) Network gate
    if (-not (Test-Network)) {
        Write-Log "Khong co mang. Se thu push lan sau." 'WARN'
        Save-Status -Status 'warn' -Message 'Khong co mang' -Changes $stagedCount
        return
    }

    # 7) Pull --rebase --autostash (optional)
    if ($PullBefore) {
        $r = Invoke-Git 'pull','--rebase','--autostash',$cfg.RemoteName,$script:State.Branch
        if ($r.ExitCode -ne 0) {
            # NOTE: stderr from a successful pull is captured in $r.Output too.
            # We only treat non-zero exit as a real warning.
            Write-Log ("git pull warn (exit {0}): {1}" -f $r.ExitCode, $r.Output) 'WARN'
        } else {
            Write-Log "Pull OK" 'INFO'
        }
    }

    # 8) Push with retry + exponential backoff. On non-fast-forward we re-pull
    #    before each retry so the next push sits on top of the latest origin tip
    #    (otherwise we just re-attempt the same stale push and burn retries).
    $pushOk = $false
    for ($i = 1; $i -le $MaxRetries; $i++) {
        $r = Invoke-Git 'push',$cfg.RemoteName,$script:State.Branch
        if ($r.ExitCode -eq 0) {
            Write-Log "Push thanh cong (lan $i)" 'INFO'
            $pushOk = $true
            break
        }
        $delay = [int]($RetryBase * [Math]::Pow(2, $i - 1))
        $isNonFF = ($r.Output -match 'non-fast-forward|rejected|fetch first')
        if ($isNonFF) {
            Write-Log ("Push reject non-fast-forward (lan {0}/{1}). Pull --rebase, thu lai sau {2}s." -f $i, $MaxRetries, $delay) 'WARN'
            $pull = Invoke-Git 'pull','--rebase','--autostash',$cfg.RemoteName,$script:State.Branch
            if ($pull.ExitCode -ne 0) {
                Write-Log ("Re-pull that bai (exit {0}): {1}" -f $pull.ExitCode, $pull.Output) 'WARN'
            }
        } else {
            Write-Log ("Push that bai (lan {0}/{1}). Thu lai sau {2}s. Output: {3}" -f $i, $MaxRetries, $delay, $r.Output) 'WARN'
        }
        if ($i -lt $MaxRetries) { Start-Sleep -Seconds $delay }
    }

    if (-not $pushOk) {
        throw "Push that bai sau $MaxRetries lan."
    }

    Save-Status -Status 'success' -Message "Sync OK: $stagedCount files" -Changes $stagedCount
    Write-Log "Sync thanh cong: $stagedCount files" 'INFO'
}

# =============================================================
# Main entry
# =============================================================
try {
    Acquire-Lock
    Write-Log ("================ Auto-sync khoi dong (PID=$PID) ================") 'INFO'
    Write-Log "Repo: $RepoPath" 'INFO'
    Write-Log "Interval: ${Interval}s | Retries: $MaxRetries | Watch: $WatchPath ($FilePattern)" 'INFO'

    # Sanity check: is this a git repo?
    $r = Invoke-Git 'rev-parse','--is-inside-work-tree'
    if ($r.ExitCode -ne 0 -or ($r.Output.Trim() -ne 'true')) {
        throw "RepoPath ($RepoPath) khong phai git repo. Chay first-time-setup.ps1 truoc."
    }

    $script:State.Branch = Resolve-Branch
    Write-Log "Branch: $($script:State.Branch) | Remote: $($cfg.RemoteUrl)" 'INFO'

    if ($RunOnce) {
        Invoke-SyncCycle
    } else {
        # Long-running loop. Cycle errors are caught locally so the loop survives.
        while ($true) {
            try {
                Invoke-SyncCycle
            } catch {
                $msg = "$_" -replace "[\r\n]+", ' '
                Write-Log "Cycle loi (khong fatal): $msg" 'ERROR'
                Save-Status -Status 'error' -Message $msg
            }
            Start-Sleep -Seconds $Interval
        }
    }
}
catch {
    $msg = "$_" -replace "[\r\n]+", ' '
    Write-Log "FATAL: $msg" 'ERROR'
    Save-Status -Status 'error' -Message "FATAL: $msg"
    Release-Lock
    exit 1
}
finally {
    if ($RunOnce) { Release-Lock }
}
