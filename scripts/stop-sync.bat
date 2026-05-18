@echo off
REM Dung auto-sync dang chay nen.
setlocal
set "SCRIPTDIR=%~dp0"
set "LOCK=%SCRIPTDIR%..\logs\auto-sync.lock"

if not exist "%LOCK%" (
    echo [INFO] Khong tim thay lock file. Co the script khong chay.
    pause
    exit /b 0
)

set /p PID=<"%LOCK%"
echo Dang dung PID %PID% ...
taskkill /F /PID %PID% >nul 2>&1
if errorlevel 1 (
    echo [WARN] Khong kill duoc PID %PID%. Co the no da chet roi.
)
del "%LOCK%" >nul 2>&1
echo [OK] Da dung.
pause
