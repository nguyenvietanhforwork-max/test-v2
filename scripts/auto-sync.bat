@echo off
REM ============================================================
REM auto-sync.bat - Simple loop fallback (BAT version).
REM Khac voi auto-sync.ps1, ban nay don gian hon, KHONG co:
REM   - filter theo *.md
REM   - retry exponential backoff
REM   - status.json + dashboard
REM   - lock single-instance
REM Dung khi muon mot version cuc minimal. Khuyen dung auto-sync.ps1.
REM ============================================================
setlocal enableextensions enabledelayedexpansion

set "REPO=E:\Application downloads\Value"
set "BRANCH=main"
set "INTERVAL=60"
set "LOGDIR=%REPO%\logs"
set "LOG=%LOGDIR%\auto-sync-bat.log"

if not exist "%LOGDIR%" mkdir "%LOGDIR%"
cd /d "%REPO%" || exit /b 1

echo [%date% %time%] BAT auto-sync khoi dong >> "%LOG%"

:loop
REM Chi check thay doi trong raw/
git status --porcelain -- raw/ > "%TEMP%\autosync-bat.tmp" 2>&1
for %%I in ("%TEMP%\autosync-bat.tmp") do set "SIZE=%%~zI"

if not "%SIZE%"=="0" (
    echo [%date% %time%] Phat hien thay doi trong raw/ >> "%LOG%"
    git add raw/ >> "%LOG%" 2>&1
    git commit -m "Auto-sync %date% %time%" >> "%LOG%" 2>&1
    git pull --rebase --autostash origin %BRANCH% >> "%LOG%" 2>&1
    git push origin %BRANCH% >> "%LOG%" 2>&1
    echo [%date% %time%] Sync xong >> "%LOG%"
)

del "%TEMP%\autosync-bat.tmp" >nul 2>&1
timeout /t %INTERVAL% /nobreak >nul
goto loop
