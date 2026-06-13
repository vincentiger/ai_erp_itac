@echo off
chcp 65001 > nul
title AI ERP - Install Frontend Dependencies

set "ROOT=%~dp0.."
for %%I in ("%ROOT%") do set "ROOT=%%~fI"
set "FE=%ROOT%\frontend"

if not exist "%FE%\package.json" (
  echo [ERROR] Frontend not found: %FE%
  echo Please run init_frontend.bat first.
  pause
  exit /b 1
)

cd /d "%FE%"

echo ==========================================
echo   Installing Frontend Dependencies
echo ==========================================
echo Frontend Path: %FE%
echo.

echo [1/4] Installing vue-router@4 ...
npm install vue-router@4
if errorlevel 1 goto :ERROR

echo [2/4] Installing element-plus ...
npm install element-plus
if errorlevel 1 goto :ERROR

echo [3/4] Installing axios ...
npm install axios
if errorlevel 1 goto :ERROR

echo [4/4] Installing TailwindCSS stack (with CLI) ...
npm install -D tailwindcss @tailwindcss/cli postcss autoprefixer
if errorlevel 1 goto :ERROR

echo.
echo ==========================================
echo   Frontend dependencies installed SUCCESS
echo ==========================================
echo.
echo Next step (run once):
echo   .\node_modules\.bin\tailwindcss init -p
echo.
pause
exit /b 0

:ERROR
echo.
echo ==========================================
echo   ERROR occurred during installation
echo ==========================================
echo Please check the messages above.
pause
exit /b 1
