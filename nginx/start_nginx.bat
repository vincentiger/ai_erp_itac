@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

set "NGINX_DIR=%~dp0"
if "%NGINX_DIR:~-1%"=="\" set "NGINX_DIR=%NGINX_DIR:~0,-1%"
set "NGINX_EXE=%NGINX_DIR%\nginx.exe"
set "NGINX_CONF=%NGINX_DIR%\conf\nginx.conf"
set "ERR_LOG=%NGINX_DIR%\logs\error.log"
set "ACC_LOG=%NGINX_DIR%\logs\access.log"

if not exist "%NGINX_EXE%" (
  echo [ERROR] nginx.exe not found: %NGINX_EXE%
  pause
  exit /b 1
)

cd /d "%NGINX_DIR%"

set "CMD=%~1"
if "%CMD%"=="" set "CMD=start"

if /I "%CMD%"=="start" goto :START
if /I "%CMD%"=="stop"  goto :STOP
if /I "%CMD%"=="reload" goto :RELOAD
if /I "%CMD%"=="test"  goto :TEST
if /I "%CMD%"=="status" goto :STATUS
if /I "%CMD%"=="logs"  goto :LOGS
if /I "%CMD%"=="help"  goto :HELP

echo [ERROR] Unknown command: %CMD%
goto :HELP


:TEST
echo.
echo ===============================
echo [TEST] nginx config
echo ===============================
"%NGINX_EXE%" -t -c "%NGINX_CONF%"
echo.
pause
exit /b


:STATUS
echo.
echo ===============================
echo [STATUS] nginx.exe processes
echo ===============================
tasklist /FI "IMAGENAME eq nginx.exe"
echo.
echo [LISTEN] :81
netstat -ano | findstr ":81 " | findstr LISTENING
echo.
pause
exit /b


:STOP
echo.
echo ===============================
echo [STOP] nginx
echo ===============================
tasklist /FI "IMAGENAME eq nginx.exe" | findstr /I "nginx.exe" >nul
if errorlevel 1 (
  echo [OK] nginx is not running.
  pause
  exit /b 0
)

REM graceful stop first
"%NGINX_EXE%" -s quit 2>nul

REM wait a moment then force kill if still running
timeout /t 2 /nobreak >nul
tasklist /FI "IMAGENAME eq nginx.exe" | findstr /I "nginx.exe" >nul
if not errorlevel 1 (
  echo [WARN] nginx still running, force kill...
  taskkill /F /IM nginx.exe >nul 2>&1
)

echo [OK] nginx stopped.
echo.
pause
exit /b


:RELOAD
echo.
echo ===============================
echo [RELOAD] nginx
echo ===============================

REM config test before reload
"%NGINX_EXE%" -t -c "%NGINX_CONF%"
if errorlevel 1 (
  echo [ERROR] Config test failed. Not reloading.
  echo See: %ERR_LOG%
  echo.
  pause
  exit /b 1
)

REM if nginx not running, start it
tasklist /FI "IMAGENAME eq nginx.exe" | findstr /I "nginx.exe" >nul
if errorlevel 1 (
  echo [INFO] nginx not running, starting...
  start "" "%NGINX_EXE%" -c "%NGINX_CONF%"
  timeout /t 1 /nobreak >nul
  goto :STATUS
)

"%NGINX_EXE%" -s reload
if errorlevel 1 (
  echo [WARN] reload failed. You may need to restart nginx.
  echo See: %ERR_LOG%
) else (
  echo [OK] reload signal sent.
)

echo.
pause
exit /b


:START
echo.
echo ===============================
echo [START] nginx
echo ===============================

REM config test before start
"%NGINX_EXE%" -t -c "%NGINX_CONF%"
if errorlevel 1 (
  echo [ERROR] Config test failed. Not starting.
  echo See: %ERR_LOG%
  echo.
  pause
  exit /b 1
)

REM avoid duplicate start
tasklist /FI "IMAGENAME eq nginx.exe" | findstr /I "nginx.exe" >nul
if not errorlevel 1 (
  echo [OK] nginx is already running.
  goto :STATUS
)

start "" "%NGINX_EXE%" -c "%NGINX_CONF%"
timeout /t 1 /nobreak >nul

goto :STATUS


:LOGS
echo.
echo ===============================
echo [LOGS] error.log (last 80 lines)
echo ===============================
if not exist "%ERR_LOG%" (
  echo [WARN] error.log not found: %ERR_LOG%
  pause
  exit /b 0
)
powershell -NoProfile -Command "Get-Content -Path '%ERR_LOG%' -Tail 80"
echo.
pause
exit /b


:HELP
echo.
echo Usage:
echo   start_nginx.bat start   ^(default^)
echo   start_nginx.bat reload
echo   start_nginx.bat stop
echo   start_nginx.bat test
echo   start_nginx.bat status
echo   start_nginx.bat logs
echo.
pause
exit /b
