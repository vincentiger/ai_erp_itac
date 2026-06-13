@echo off
chcp 65001 > nul
title AI ERP - Install Backend

set "ROOT=%~dp0.."
for %%I in ("%ROOT%") do set "ROOT=%%~fI"
set "BE=%ROOT%\backend"
set PY310=C:\Users\vince\AppData\Local\Programs\Python\Python310\python.exe
set VENV=%BE%\venv
set "PY_CMD="

echo ==========================================
echo   AI ERP Backend - Install
echo ==========================================

if exist "%PY310%" (
  set "PY_CMD=%PY310%"
)
if not defined PY_CMD (
  py -3.11 -V >nul 2>&1
  if not errorlevel 1 set "PY_CMD=py -3.11"
)
if not defined PY_CMD (
  py -3.10 -V >nul 2>&1
  if not errorlevel 1 set "PY_CMD=py -3.10"
)
if not defined PY_CMD (
  echo [ERROR] Python not found.
  echo Checked:
  echo   %PY310%
  echo   py -3.11
  echo   py -3.10
  pause
  exit /b 1
)

if not exist "%BE%\server.py" (
  echo [ERROR] Backend folder not found or server.py missing:
  echo %BE%
  pause
  exit /b 1
)

echo [1/3] Creating venv...
%PY_CMD% -m venv "%VENV%"
if errorlevel 1 goto :ERROR

echo [2/3] Upgrading pip...
"%VENV%\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :ERROR

echo [3/3] Installing backend dependencies...
"%VENV%\Scripts\python.exe" -m pip install -r "%ROOT%\requirements.txt"
if errorlevel 1 goto :ERROR

echo.
echo ==========================================
echo   Backend installed SUCCESS
echo ==========================================
pause
exit /b 0

:ERROR
echo.
echo [ERROR] Backend install failed. See messages above.
pause
exit /b 1
