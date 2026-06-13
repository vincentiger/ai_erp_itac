@echo off
set "NGINX_DIR=%~dp0"
if "%NGINX_DIR:~-1%"=="\" set "NGINX_DIR=%NGINX_DIR:~0,-1%"
cd /d "%NGINX_DIR%"

echo Stopping Nginx...
nginx.exe -s quit

echo Nginx stopped.
pause
