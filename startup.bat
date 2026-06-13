@echo off
setlocal EnableExtensions EnableDelayedExpansion
title AI ERP ITAC

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
set "NGINX=%ROOT%\nginx"
set "BACKEND=%ROOT%\backend"
set "STATIC=%NGINX%\html\ai"

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

taskkill /f /im nginx.exe /t >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8080" ^| findstr "LISTENING"') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":81" ^| findstr "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

echo [1/2] Starting nginx...
start "" "%NGINX%\nginx.exe" -p "%NGINX%\" -c conf\nginx.conf

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
start "" "http://127.0.0.1:81/ai/#/login"
endlocal
