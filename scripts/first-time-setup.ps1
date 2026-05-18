# ============================================================
# first-time-setup.ps1
# Kiem tra & cau hinh moi truong truoc khi chay auto-sync.
#   1. Git da cai
#   2. user.name + user.email
#   3. Repo path ton tai
#   4. .git da init
#   5. Remote URL khop config
#   6. ls-remote OK (test auth)
#   7. Branch dung
#   8. Folder raw/ ton tai, .gitignore co cac entry can
# ============================================================
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'

# Force UTF-8 between PowerShell and git for Vietnamese filenames
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

$cfg  = Get-Content $ConfigPath -Raw -Encoding utf8 | ConvertFrom-Json
$Repo = $cfg.RepoPath

function Step($n, $msg) { Write-Host "`n[BUOC $n] $msg" -ForegroundColor Cyan }
function OK($msg)       { Write-Host "  [OK]  $msg" -ForegroundColor Green }
function Bad($msg)      { Write-Host "  [LOI] $msg" -ForegroundColor Red }
function Info($msg)     { Write-Host "        $msg" -ForegroundColor Gray }

# ----- 1. Git -----
Step 1 "Kiem tra git"
try {
    $v = (& git --version) 2>&1
    if ($LASTEXITCODE -ne 0) { throw "git --version exit $LASTEXITCODE" }
    OK "Git: $v"
} catch {
    Bad "Khong tim thay git."
    Info "Cai tu: https://git-scm.com/download/win  (chon Standalone Installer 64-bit)"
    Info "Sau khi cai xong, MO LAI cua so PowerShell roi chay lai script nay."
    exit 1
}

# ----- 2. Git user -----
Step 2 "Kiem tra git user"
$name  = (& git config --global user.name)
$email = (& git config --global user.email)
if (-not $name -or -not $email) {
    Bad "Chua cau hinh user.name/user.email."
    Info 'Chay 2 lenh nay (thay ten + email):'
    Info '  git config --global user.name "Nguyen Viet Anh"'
    Info '  git config --global user.email "nguyenvietanhforwork@gmail.com"'
    exit 1
}
OK "user.name=$name | user.email=$email"

# ----- 3. Repo path -----
Step 3 "Kiem tra repo path"
if (-not (Test-Path $Repo)) {
    Bad "RepoPath khong ton tai: $Repo"
    exit 1
}
OK $Repo

# ----- 4. git init -----
Step 4 "Kiem tra .git"
$dotGit = Join-Path $Repo '.git'
if (-not (Test-Path $dotGit)) {
    Info "Chua co .git, dang khoi tao..."
    & git -C $Repo init | Out-Null
    & git -C $Repo checkout -b main 2>$null | Out-Null
    OK "Da git init va tao branch main"
} else {
    OK "Da co .git"
}

# ----- 4b. Git config quan trong cho file Viet Nam + long paths -----
Step "4b" "Cau hinh git: UTF-8 cho ten file + long paths"
& git -C $Repo config core.quotepath false       | Out-Null
& git -C $Repo config core.longpaths true        | Out-Null
& git -C $Repo config core.precomposeunicode true | Out-Null
OK "Da set core.quotepath=false, core.longpaths=true, core.precomposeunicode=true"

# ----- 5. Remote -----
Step 5 "Cau hinh remote '$($cfg.RemoteName)'"
$remotes = @(& git -C $Repo remote)
if ($remotes -contains $cfg.RemoteName) {
    $currentUrl = (& git -C $Repo remote get-url $cfg.RemoteName).Trim()
    if ($currentUrl -ne $cfg.RemoteUrl) {
        Info "Doi remote URL: $currentUrl -> $($cfg.RemoteUrl)"
        & git -C $Repo remote set-url $cfg.RemoteName $cfg.RemoteUrl | Out-Null
    }
    OK "Remote $($cfg.RemoteName) -> $($cfg.RemoteUrl)"
} else {
    & git -C $Repo remote add $cfg.RemoteName $cfg.RemoteUrl | Out-Null
    OK "Da them remote $($cfg.RemoteName)"
}

# ----- 6. ls-remote (test auth + connectivity) -----
Step 6 "Test ket noi den GitHub (git ls-remote)"
$out = (& git -C $Repo ls-remote $cfg.RemoteName 2>&1) -join "`n"
if ($LASTEXITCODE -ne 0) {
    Bad "Khong fetch duoc tu remote."
    Info "Output: $out"
    Info ""
    Info "Cach fix:"
    Info "  - Lan dau push se mo trinh duyet de dang nhap GitHub (Git Credential Manager)."
    Info "  - Hoac dung Personal Access Token:"
    Info "      https://github.com/settings/tokens  -> Generate new token (classic) -> repo scope"
    Info "      Khi git hoi password, dan TOKEN vao thay vi password."
    Info "  - Hoac SSH: doi RemoteUrl thanh git@github.com:USER/REPO.git roi"
    Info "      ssh-keygen -t ed25519 -C 'email'  va paste public key vao GitHub Settings > SSH keys."
    exit 1
}
OK "Ket noi remote OK"

# ----- 7. Branch -----
Step 7 "Kiem tra branch"
$branch = (& git -C $Repo rev-parse --abbrev-ref HEAD 2>$null)
if (-not $branch) {
    Info "Chua co commit nao. Tao commit dau tien..."
    $marker = Join-Path $Repo '.gitkeep-autosync'
    Set-Content -Path $marker -Value '' -Encoding ascii
    & git -C $Repo add .gitkeep-autosync | Out-Null
    & git -C $Repo commit -m "Initial commit from auto-sync setup" | Out-Null
    & git -C $Repo branch -M main | Out-Null
    OK "Da tao commit dau tien tren branch main"
} elseif ($branch -ne $cfg.Branch -and $cfg.Branch) {
    Info "Branch hien tai = $branch, doi sang $($cfg.Branch)..."
    & git -C $Repo branch -m $cfg.Branch | Out-Null
    OK "Doi sang branch $($cfg.Branch)"
} else {
    OK "Branch: $branch"
}

# ----- 8. raw/ folder + .gitignore -----
Step 8 "Kiem tra folder raw/ va .gitignore"
$rawDir = Join-Path $Repo 'raw'
if (-not (Test-Path $rawDir)) {
    New-Item -ItemType Directory -Force -Path $rawDir | Out-Null
    OK "Da tao folder raw/"
} else {
    OK "raw/ da ton tai"
}

$giPath = Join-Path $Repo '.gitignore'
$wantedEntries = @('logs/','*.lock','outputs/sync-dashboard.html')
$existing = @()
if (Test-Path $giPath) {
    $existing = Get-Content $giPath -Encoding utf8
} else {
    New-Item -ItemType File -Path $giPath | Out-Null
}
$toAdd = $wantedEntries | Where-Object { $existing -notcontains $_ }
if ($toAdd.Count -gt 0) {
    Add-Content -Path $giPath -Value $toAdd -Encoding utf8
    OK "Da them vao .gitignore: $($toAdd -join ', ')"
} else {
    OK ".gitignore da co cac entry can thiet"
}

Write-Host "`n=========== SETUP HOAN TAT ===========" -ForegroundColor Green
Write-Host "Buoc tiep theo:" -ForegroundColor Yellow
Write-Host "  1) Test mot lan:    powershell -ExecutionPolicy Bypass -File auto-sync.ps1 -RunOnce -Verbose"
Write-Host "  2) Chay nen:        .\start-sync.bat"
Write-Host "  3) Auto-start:      powershell -ExecutionPolicy Bypass -File install-task.ps1"
Write-Host "  4) Dashboard:       outputs\sync-dashboard.html"
