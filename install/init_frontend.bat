@echo off
chcp 65001 > nul
title AI ERP - Init Frontend

set "ROOT=%~dp0.."
for %%I in ("%ROOT%") do set "ROOT=%%~fI"
set "FE=%ROOT%\frontend"

echo ==========================================
echo   AI ERP - Initialize Frontend (Vue)
echo ==========================================

REM 1. 檢查 npm 是否存在
where npm >nul 2>nul
if errorlevel 1 (
  echo [ERROR] npm not found. Please install Node.js first.
  pause
  exit /b 1
)

REM 2. 如果前端已存在就不要重建
if exist "%FE%\package.json" (
  echo [INFO] Frontend already exists:
  echo %FE%
  pause
  exit /b 0
)

REM 3. 建立專案
cd /d "%ROOT%"
echo [1/2] Creating Vite + Vue project...
npm create vite@latest frontend -- --template vue

REM 4. 安裝 Vite 預設套件
cd /d "%FE%"
echo [2/2] Installing default dependencies...
npm install

echo ==========================================
echo   Frontend initialized successfully
echo ==========================================
echo Next step: run install_frontend.bat
pause

