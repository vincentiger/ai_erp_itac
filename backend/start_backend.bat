@echo off
setlocal EnableExtensions EnableDelayedExpansion
title AI ERP Backend Watchdog

set "ROOT=%~dp0.."
for %%I in ("%ROOT%") do set "ROOT=%%~fI"
set "BE=%ROOT%\backend"
set "PY_EXE="
set "PY_MODE="
set "PY_LABEL="

call :PICK_PYTHON "%ROOT%\.venv_local\Scripts\python.exe"
call :PICK_PYTHON "%ROOT%\.venv\Scripts\python.exe"
call :PICK_PYTHON "%BE%\venv\Scripts\python.exe"
call :PICK_PYTHON "%ROOT%\venv\Scripts\python.exe"
call :PICK_PY_LAUNCHER

echo ==========================================
echo   AI ERP Backend Watchdog
echo ==========================================
echo [INFO] Run this file as Administrator if SQL access fails.

if not defined PY_MODE (
  echo [ERROR] Python environment not found or unusable.
  echo Checked:
  echo   %ROOT%\.venv_local\Scripts\python.exe
  echo   %ROOT%\.venv\Scripts\python.exe
  echo   %BE%\venv\Scripts\python.exe
  echo   %ROOT%\venv\Scripts\python.exe
  echo   py -3.10
  pause
  exit /b 1
)

echo [OK] Using Python: %PY_LABEL%
cd /d "%ROOT%"
set /a RESTART_COUNT=0

:RUN_BACKEND
set /a RESTART_COUNT+=1
echo.
echo [WATCHDOG] Launch #%RESTART_COUNT% at %DATE% %TIME%
set "PYTHONPATH=%ROOT%\backend"
set "USE_SOCKETIO=0"
set "HTTP_PORT=8080"
if /I "%PY_MODE%"=="exe" (
  "%PY_EXE%" backend\server.py
) else (
  py -3.10 backend\server.py
)
set "EXIT_CODE=%ERRORLEVEL%"

echo [WATCHDOG] Backend exited with code %EXIT_CODE% at %DATE% %TIME%
echo [WATCHDOG] Restarting in 5 seconds. Press Ctrl+C to stop this window.
timeout /t 5 >nul
goto RUN_BACKEND

:PICK_PYTHON
if defined PY_MODE goto :eof
if not exist "%~1" goto :eof
"%~1" -c "import dotenv" >nul 2>&1
if errorlevel 1 goto :eof
"%~1" -c "import sys; sys.path.insert(0, r'%BE%'); import server" >nul 2>&1
if errorlevel 1 goto :eof
set "PY_EXE=%~1"
set "PY_MODE=exe"
set "PY_LABEL=%~1"
goto :eof

:PICK_PY_LAUNCHER
if defined PY_MODE goto :eof
py -3.10 -c "import dotenv" >nul 2>&1
if errorlevel 1 goto :eof
py -3.10 -c "import sys; sys.path.insert(0, r'%BE%'); import server" >nul 2>&1
if errorlevel 1 goto :eof
set "PY_MODE=launcher"
set "PY_LABEL=py -3.10"
goto :eof
