@echo off
setlocal EnableExtensions EnableDelayedExpansion
title AI ERP ITAC

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
set "NGINX_DIR=%ROOT%\nginx"
set "BACKEND=%ROOT%\backend"
set "STATIC=%NGINX_DIR%\html\ai"
set "VERSION_FILE=%ROOT%\release\version.txt"
set "STARTUP_LOG=%ROOT%\logs\startup.log"

REM NGINX is reserved by nginx.exe for inherited socket descriptors.
set "NGINX="

if not exist "%ROOT%\.env" (
  echo [ERROR] Missing %ROOT%\.env
  echo Copy .env.example to .env and update the database settings first.
  pause
  exit /b 1
)

if not exist "%STATIC%\index.html" (
  echo [ERROR] Frontend files are missing: %STATIC%\index.html
  pause
  exit /b 1
)

if not exist "%ROOT%\logs" mkdir "%ROOT%\logs"
for /f "usebackq delims=" %%H in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "(Get-FileHash -Algorithm SHA256 '%~f0').Hash"`) do set "STARTUP_BAT_HASH=%%H"
echo [VERSION] startup.bat sha256=!STARTUP_BAT_HASH!
>> "%STARTUP_LOG%" echo [%DATE% %TIME%] startup.bat sha256=!STARTUP_BAT_HASH!
if exist "%VERSION_FILE%" (
  echo [VERSION] release stamp: %VERSION_FILE%
  >> "%STARTUP_LOG%" echo [STAMP] %VERSION_FILE%
  type "%VERSION_FILE%" >> "%STARTUP_LOG%"
  type "%VERSION_FILE%"
) else (
  echo [VERSION] release stamp not found: %VERSION_FILE%
  >> "%STARTUP_LOG%" echo [STAMP] missing %VERSION_FILE%
)

if exist "%ROOT%\backend\routes\realtime.cp310-win_amd64.pyd" (
  del /f /q "%ROOT%\backend\routes\realtime.cp310-win_amd64.pyd" >nul 2>&1
  >> "%STARTUP_LOG%" echo removed stale backend\routes\realtime.cp310-win_amd64.pyd
)
if exist "%ROOT%\backend\routes\__pycache__\realtime.cpython-310.pyc" (
  del /f /q "%ROOT%\backend\routes\__pycache__\realtime.cpython-310.pyc" >nul 2>&1
  >> "%STARTUP_LOG%" echo removed stale backend\routes\__pycache__\realtime.cpython-310.pyc
)
if exist "%ROOT%\backend\routes\__pycache__\realtime*.pyc" (
  del /f /q "%ROOT%\backend\routes\__pycache__\realtime*.pyc" >nul 2>&1
  >> "%STARTUP_LOG%" echo removed stale backend\routes\__pycache__\realtime*.pyc
)

taskkill /f /im nginx.exe /t >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8080" ^| findstr "LISTENING"') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":81" ^| findstr "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

echo [1/2] Starting nginx...
"%NGINX_DIR%\nginx.exe" -t -p "%NGINX_DIR%" -c "conf\nginx.conf"
if errorlevel 1 (
  echo [ERROR] nginx configuration test failed.
  pause
  exit /b 1
)
start "" "%NGINX_DIR%\nginx.exe" -p "%NGINX_DIR%" -c "conf\nginx.conf"

echo [2/2] Starting backend...
start "AI ERP Backend" cmd /k ""%BACKEND%\start_backend.bat""

echo [WAIT] Waiting for backend port 8080...
set /a BACKEND_WAIT=0
:WAIT_BACKEND
netstat -ano | findstr ":8080" | findstr "LISTENING" >nul
if %errorlevel% equ 0 goto BACKEND_READY
set /a BACKEND_WAIT+=1
if !BACKEND_WAIT! geq 30 (
  echo [ERROR] Backend did not start within 30 seconds.
  echo [ERROR] Check the AI ERP Backend window for the actual error.
  pause
  exit /b 1
)
timeout /t 1 >nul
goto WAIT_BACKEND

:BACKEND_READY
echo [OK] Backend port 8080 is ready.
set "CHROME_EXE="
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "CHROME_EXE=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not defined CHROME_EXE if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "CHROME_EXE=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if not defined CHROME_EXE if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" set "CHROME_EXE=%LocalAppData%\Google\Chrome\Application\chrome.exe"
if defined CHROME_EXE (
  start "" "%CHROME_EXE%" --new-window "http://127.0.0.1:81/ai/#/login?account=sys&password=1120"
) else (
  start "" "http://127.0.0.1:81/ai/#/login?account=sys&password=1120"
)
endlocal
