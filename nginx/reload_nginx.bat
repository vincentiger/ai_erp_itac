@echo off
set "NGINX_DIR=%~dp0"
if "%NGINX_DIR:~-1%"=="\" set "NGINX_DIR=%NGINX_DIR:~0,-1%"
cd /d "%NGINX_DIR%"

echo Testing config...
nginx.exe -t -c "%NGINX_DIR%\conf\nginx.conf"

if %errorlevel% neq 0 (
    echo Config test FAILED!
    pause
    exit /b 1
)

echo Reloading Nginx...
nginx.exe -s reload

echo Reload complete.
pause
