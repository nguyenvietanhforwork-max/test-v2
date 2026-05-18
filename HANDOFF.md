# Auto-sync GitHub Project - Handoff Summary

## Goal
Tao he thong auto-sync chay tren Windows 11 hoat dong giong Dropbox nhung dung GitHub.
Theo doi folder `E:\Application downloads\Value`, tu dong commit + push len repo
`https://github.com/nguyenvietanhforwork-max/test-v2` moi 60 giay khi co thay doi.

## Yeu cau ban dau
- Windows 11 native, KHONG Docker, KHONG WSL, KHONG Node.js
- Uu tien BAT hoac PowerShell
- Chay nen 24/7, auto-start cung Windows, an cua so terminal
- Chi commit khi co thay doi thuc su (khong tao commit rac)
- Co log, retry network, dashboard
- Toi uu cho Obsidian/Web Clipper workflow

## User context
- User: nguyenvietanhforwork-max (email: nguyenvietanhforwork@gmail.com)
- Trinh do: nguoi khong chuyen ky thuat (lop 10)
- Da tu lam toi buoc: cai Git, dang nhap GitHub via browser, doi remote URL
- Folder Value/ co san .git folder (truoc do tro toi repo cu Test-dashboard.git)

## Cau truc folder hien tai
```
E:\Application downloads\Value\
├── .git\                          (da setup, remote = test-v2.git, branch = main)
├── .gitignore                     (da cap nhat, ignore logs/, sync-dashboard.html, *.lock)
├── .gitattributes                 (CRLF cho .bat, LF cho .ps1/.md)
├── raw\, wiki\, outputs\, etc.    (noi dung cua user - rat nhieu file .md)
├── logs\                          (sinh ra khi script chay)
│   ├── auto-sync.log
│   ├── status.json
│   └── auto-sync.lock
├── outputs\sync-dashboard.html    (dashboard - tu refresh moi 10s)
├── scripts\
│   ├── config.json                (cau hinh: interval, retries, remote URL...)
│   ├── auto-sync.ps1              (main engine - PowerShell, ~420 dong)
│   ├── auto-sync.bat              (BAT version don gian)
│   ├── run-hidden.vbs             (hidden launcher)
│   ├── start-sync.bat
│   ├── stop-sync.bat
│   ├── check-status.bat
│   ├── first-time-setup.ps1       (da chay thanh cong)
│   ├── install-task.ps1           (chua chay)
│   └── uninstall-task.ps1
├── SETUP-GUIDE.md                 (huong dan day du 16 muc)
└── HANDOFF.md                     (file nay)
```

## Cau hinh hien tai (config.json)
```json
{
  "RepoPath": "E:\\Application downloads\\Value",
  "RemoteName": "origin",
  "RemoteUrl": "https://github.com/nguyenvietanhforwork-max/test-v2.git",
  "Branch": "",
  "IntervalSeconds": 60,
  "MaxRetries": 5,
  "RetryBaseDelaySeconds": 5,
  "MaxLogSizeMB": 10,
  "PullBeforePush": true,
  "CommitMessageTemplate": "Auto-sync {timestamp} ({changes} files)",
  "QuietWhenNoChanges": true,
  "NetworkTestHost": "github.com"
}
```

## Cac buoc da hoan thanh
1. Cai Git 2.54.0.windows.1 - OK
2. Tao repo test-v2 tren GitHub (co the da tick "Add README" nen co commit dau tien)
3. Chay first-time-setup.ps1 - OK (BUOC 1-6 deu xanh, "SETUP HOAN TAT")
4. Doi remote URL tu Test-dashboard.git -> test-v2.git - OK
5. Login GitHub qua browser (Git Credential Manager) - OK
6. Doi local branch master -> main + force push len test-v2 - OK
   Lenh da chay: `git branch -m master main; git fetch origin; git push -u origin main --force`
7. Tren GitHub test-v2, da thay file (gia su lenh push force da work)

## VAN DE HIEN TAI - DANG STUCK
Khi chay `powershell -ExecutionPolicy Bypass -File auto-sync.ps1 -RunOnce -Verbose`:
- Dashboard hien: status FAIL, Tong that bai = 1
- LastMessage trong status: `FATAL: From https://github.com/nguyenvietanhforwork-max/test-v2`
- (Message bi cat ngan o "From ..." - day la output cua git fetch/pull, khong phai loi rieng)

Branch info hien tai (theo dashboard):
- Repo: E:\Application downloads\Value
- Remote: https://github.com/nguyenvietanhforwork-max/test-v2.git
- Branch: main

## Cac bug TRUOC do da fix
1. Lo dung ky tu tieng Viet co dau trong .ps1 file -> PowerShell 5.1 doc UTF-8 nhu ANSI -> parser error.
   Da fix: rewrite auto-sync.ps1 voi ASCII-only (transliterate, khong dau).

2. Bug parameter binding trong function Invoke-Git:
   Ban dau: `param([Parameter(ValueFromRemainingArguments=$true)][string[]]$GitArgs)`
   Khi goi `Invoke-Git 'rev-parse','--abbrev-ref','HEAD'`, PowerShell wrap them mot lan
   array roi join thanh string => git nhan "rev-parse --abbrev-ref HEAD" la 1 lenh sai.
   Da fix thanh: `param([Parameter(Mandatory, Position=0)][string[]]$GitArgs)`

## Code main loop auto-sync.ps1 (rut gon)
```powershell
function Invoke-Git {
    param([Parameter(Mandatory, Position=0)][string[]]$GitArgs)
    $output = & git -C $RepoPath @GitArgs 2>&1
    return @{ Output = ($output -join "`n"); ExitCode = $LASTEXITCODE }
}

# Main loop wrapped in try/catch:
try {
    Acquire-Lock
    ...
    while ($true) {
        Invoke-SyncCycle
        Start-Sleep -Seconds $cfg.IntervalSeconds
    }
}
catch {
    Write-Log "FATAL: $_" 'ERROR'
    Save-Status -Status 'error' -Message "FATAL: $_"
    Release-Lock
    exit 1
}

# Inside Invoke-SyncCycle:
$r = Invoke-Git 'status','--porcelain'   # check changes
$r = Invoke-Git 'add','--all'
$r = Invoke-Git 'diff','--cached','--name-only'
$r = Invoke-Git 'commit','-m',$msg
if ($cfg.PullBeforePush) {
    $r = Invoke-Git 'pull','--rebase','--autostash',$cfg.RemoteName,$script:State.Branch
    # Log WARN if fail, continue to push
}
# Push with retry loop:
for ($i = 1; $i -le $cfg.MaxRetries; $i++) {
    $r = Invoke-Git 'push',$cfg.RemoteName,$script:State.Branch
    ...
}
```

## Gia thuyet ve loi hien tai
Message "FATAL: From https://github.com/..." chinh la output binh thuong cua `git fetch`
hoac `git pull` (dong "From <url>" la ban dau remote info, khong phai loi). Co the:

1. `$ErrorActionPreference = 'Stop'` + native command stderr (`2>&1`) khien output stderr
   binh thuong cua git bi treat nhu exception.

2. Co the `Set-StrictMode -Version Latest` khien access vao truong nao do cua $r.Output bi loi
   khi git print message info ra stderr.

3. Co the exception thuc su xay ra trong vong loop khong duoc handle, bi catch boi main try/catch
   o ngoai cung => "FATAL: <truncated git output>".

## Can ho tro
1. Debug tai sao auto-sync.ps1 -RunOnce -Verbose bi FATAL.
2. Co the can:
   - Wrap moi Invoke-Git trong try/catch rieng
   - Hoac doi 2>&1 thanh redirect stderr ra null hoac chuyen sang error stream
   - Hoac doi `$ErrorActionPreference = 'Continue'` thay vi 'Stop' o auto-sync.ps1
3. Sau khi debug, can:
   - Test `auto-sync.ps1 -RunOnce -Verbose` chay sach
   - Chay `.\start-sync.bat` de bat nen
   - Chay `install-task.ps1` de auto-start cung Windows
   - Verify dashboard hien xanh "success" hoac "no-change"

## Lenh test
```powershell
cd "E:\Application downloads\Value\scripts"
powershell -ExecutionPolicy Bypass -File auto-sync.ps1 -RunOnce -Verbose
```

## File log day du
Doc bang: `Get-Content "E:\Application downloads\Value\logs\auto-sync.log" -Tail 50`
