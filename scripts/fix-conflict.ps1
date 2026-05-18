# ============================================================
# fix-conflict.ps1
# ONE-SHOT cleanup khi repo dang ket merge/rebase conflict.
#   1. Abort moi rebase/merge dang do
#   2. Set git config UTF-8 + long paths
#   3. Fetch remote
#   4. Lay ban remote cho cac file conflict
#   5. Commit ket qua resolve
# ============================================================
[CmdletBinding()]
param(
    [string[]]$ConflictFiles = @('news-dashboard-v2.html', 'news_database.json')
)
$ErrorActionPreference = 'Stop'

# Force UTF-8 console
try {
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [Console]::OutputEncoding = $utf8NoBom
    [Console]::InputEncoding  = $utf8NoBom
    $OutputEncoding           = $utf8NoBom
} catch { }

$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ConfigPath = Join-Path $ScriptDir 'config.json'
if (-not (Test-Path $ConfigPath)) {
    Write-Host "ERROR: Khong tim thay config.json" -ForegroundColor Red
    exit 1
}
$cfg    = Get-Content $ConfigPath -Raw -Encoding utf8 | ConvertFrom-Json
$Repo   = $cfg.RepoPath
$Remote = $cfg.RemoteName
$Branch = if ($cfg.Branch) { $cfg.Branch } else { 'main' }

function Step($n, $msg) { Write-Host "`n[$n] $msg" -ForegroundColor Cyan }
function OK($msg)       { Write-Host "  [OK]  $msg" -ForegroundColor Green }
function Bad($msg)      { Write-Host "  [LOI] $msg" -ForegroundColor Red }
function Info($msg)     { Write-Host "        $msg" -ForegroundColor Gray }

# IMPORTANT: param ten KHONG duoc la '$args' (bien tu dong cua PS).
function Git-Run {
    [CmdletBinding()]
    param([Parameter(Mandatory, Position=0)][string[]]$GitArgs)
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $raw  = & git -C $Repo @GitArgs 2>&1
        $code = $LASTEXITCODE
        $out  = (@($raw | ForEach-Object { "$_" }) -join "`n")
        return @{ Output = $out; ExitCode = $code }
    } finally {
        $ErrorActionPreference = $prev
    }
}

# ---------- 1. Abort rebase/merge ----------
Step 1 "Phat hien trang thai rebase/merge dang do"
$dotGit  = Join-Path $Repo '.git'
$aborted = $false
foreach ($sub in 'rebase-merge','rebase-apply') {
    if (Test-Path (Join-Path $dotGit $sub)) {
        Info "Co rebase dang do ($sub). Abort..."
        $r = Git-Run 'rebase','--abort'
        if ($r.ExitCode -eq 0) { $aborted = $true } else { Info "  Warning: $($r.Output)" }
    }
}
if (Test-Path (Join-Path $dotGit 'MERGE_HEAD')) {
    Info "Co merge dang do. Abort..."
    $r = Git-Run 'merge','--abort'
    if ($r.ExitCode -eq 0) { $aborted = $true } else { Info "  Warning: $($r.Output)" }
}
if ($aborted) { OK "Da abort" } else { OK "Khong co rebase/merge dang do (hoac da abort truoc do)" }

# ---------- 2. Git config ----------
Step 2 "Set git config UTF-8 + long paths"
$allOk = $true
foreach ($pair in @(
    @('core.quotepath','false'),
    @('core.longpaths','true'),
    @('core.precomposeunicode','true')
)) {
    $r = Git-Run 'config',$pair[0],$pair[1]
    if ($r.ExitCode -ne 0) {
        Bad "git config $($pair[0]) loi: $($r.Output)"
        $allOk = $false
    }
}
if (-not $allOk) { exit 1 }
OK "core.quotepath=false, core.longpaths=true, core.precomposeunicode=true"

# ---------- 3. Fetch ----------
Step 3 "Fetch tu $Remote"
$r = Git-Run 'fetch',$Remote
if ($r.ExitCode -ne 0) {
    Bad "git fetch loi: $($r.Output)"
    Info "Kiem tra mang + dang nhap GitHub."
    exit 1
}
OK "Fetch xong"

# ---------- 4. Liet ke unmerged ----------
Step 4 "Kiem tra cac file unmerged"
$r = Git-Run 'diff','--name-only','--diff-filter=U'
$unmerged = @($r.Output -split "[\r\n]+" | Where-Object { $_ })
if ($unmerged.Count -gt 0) {
    Info "Cac file dang unmerged:"
    foreach ($f in $unmerged) { Info "  - $f" }
} else {
    Info "Khong co file nao dang unmerged."
}

# ---------- 5. Resolve cac file conflict ----------
Step 5 "Lay ban tu $Remote/$Branch cho cac file conflict"
$remoteRef = "$Remote/$Branch"
$r = Git-Run 'rev-parse','--verify',$remoteRef
if ($r.ExitCode -ne 0) {
    Bad "Khong tim thay ref $remoteRef`: $($r.Output)"
    exit 1
}

$resolved = @()
foreach ($f in $ConflictFiles) {
    Info "Xu ly $f ..."
    $r = Git-Run 'checkout',$remoteRef,'--',$f
    if ($r.ExitCode -eq 0) {
        $stage = Git-Run 'add','--',$f
        if ($stage.ExitCode -eq 0) {
            $resolved += $f
            OK "  Resolved $f (lay ban remote)"
        } else {
            Bad "  Stage that bai: $($stage.Output)"
        }
    } else {
        if ($r.Output -match 'did not match' -or $r.Output -match 'pathspec' -or $r.Output -match 'does not exist') {
            Info "  $f khong co tren $remoteRef -> xoa khoi index"
            $rm = Git-Run 'rm','-f','--',$f
            if ($rm.ExitCode -eq 0) {
                $resolved += $f
                OK "  Da xoa $f"
            } else {
                Bad "  Khong xoa duoc $f`: $($rm.Output)"
            }
        } else {
            Bad "  Checkout that bai cho $f`: $($r.Output)"
        }
    }
}

# ---------- 6. Verify het conflict ----------
Step 6 "Kiem tra con file unmerged khac khong"
$r = Git-Run 'diff','--name-only','--diff-filter=U'
$still = @($r.Output -split "[\r\n]+" | Where-Object { $_ })
if ($still.Count -gt 0) {
    Bad "Van con file unmerged:"
    foreach ($f in $still) { Info "  - $f" }
    Info "Chay lai voi: -ConflictFiles 'file1','file2'..."
    exit 1
}
OK "Khong con file unmerged"

# ---------- 7. Commit ----------
Step 7 "Commit ket qua resolve"
$r = Git-Run 'status','--porcelain'
$hasStaged = @($r.Output -split "[\r\n]+" | Where-Object { $_ -and $_ -match '^[MADRCU]' }).Count -gt 0
if ($hasStaged) {
    $msg = "Resolve conflict: take remote version of " + ($resolved -join ', ')
    $c = Git-Run 'commit','-m',$msg
    if ($c.ExitCode -eq 0) {
        OK "Da commit: $msg"
    } else {
        Bad "Commit loi: $($c.Output)"
        exit 1
    }
} else {
    Info "Khong co gi de commit (working tree clean voi cac file conflict)."
}

# ---------- 8. Final status ----------
Step 8 "Trang thai cuoi"
$r = Git-Run 'status','--short'
if ([string]::IsNullOrWhiteSpace($r.Output)) {
    OK "Working tree clean. Repo san sang."
} else {
    Info "Working tree con thay doi (binh thuong, auto-sync se xu ly):"
    foreach ($l in ($r.Output -split "[\r\n]+" | Select-Object -First 10)) { Info "  $l" }
    $total = @($r.Output -split "[\r\n]+" | Where-Object { $_ }).Count
    if ($total -gt 10) { Info "  ... va $($total - 10) dong nua" }
}

$r = Git-Run 'log','--oneline','-1'
Info "HEAD: $($r.Output)"

Write-Host "`n=========== DA FIX XONG ===========" -ForegroundColor Green
Write-Host "Buoc tiep theo:" -ForegroundColor Yellow
Write-Host "  powershell -ExecutionPolicy Bypass -File auto-sync.ps1 -RunOnce -Verbose"
