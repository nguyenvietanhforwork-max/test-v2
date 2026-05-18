@echo off
REM Kiem tra trang thai auto-sync.
setlocal
set "SCRIPTDIR=%~dp0"
set "LOCK=%SCRIPTDIR%..\logs\auto-sync.lock"
set "STATUS=%SCRIPTDIR%..\logs\status.json"
set "LOG=%SCRIPTDIR%..\logs\auto-sync.log"

echo ============================================================
echo  Auto-sync status check
echo ============================================================

if exist "%LOCK%" (
    set /p PID=<"%LOCK%"
    tasklist /FI "PID eq !PID!" 2>nul | findstr /I "powershell" >nul
    if errorlevel 1 (
        echo [TRANG THAI]  Co lock PID=!PID! nhung process da chet. Chay stop-sync.bat de don.
    ) else (
        echo [TRANG THAI]  Dang chay - PID=!PID!
    )
) else (
    echo [TRANG THAI]  Khong chay.
)
echo.

if exist "%STATUS%" (
    echo === status.json ===
    type "%STATUS%"
) else (
    echo Khong co status.json. Script co the chua chay lan nao.
)

echo.
if exist "%LOG%" (
    echo === 20 dong log gan nhat ===
    powershell -NoProfile -Command "Get-Content -Path '%LOG%' -Tail 20"
)

echo.
pause
