@echo off
REM Khoi dong auto-sync.ps1 trong cua so an (qua VBS launcher).
setlocal
set "SCRIPTDIR=%~dp0"
set "LOCK=%SCRIPTDIR%..\logs\auto-sync.lock"

if exist "%LOCK%" (
    echo [WARN] Co lock file: %LOCK%
    echo Co the auto-sync da chay roi. Chay check-status.bat de kiem tra.
    echo Neu chac chan no khong chay, xoa lock file roi thu lai.
    pause
    exit /b 1
)

echo Khoi dong auto-sync (an)...
wscript.exe "%SCRIPTDIR%run-hidden.vbs"
timeout /t 2 /nobreak >nul

if exist "%LOCK%" (
    echo [OK] Da khoi dong. Lock file: %LOCK%
    type "%LOCK%"
    echo.
    echo Xem log:        type "%SCRIPTDIR%..\logs\auto-sync.log"
    echo Xem dashboard:  start "" "%SCRIPTDIR%..\outputs\sync-dashboard.html"
    echo Dung:           "%SCRIPTDIR%stop-sync.bat"
) else (
    echo [WARN] Khong tao duoc lock file. Co the script chet ngay. Kiem tra log:
    echo   type "%SCRIPTDIR%..\logs\auto-sync.log"
)

pause
