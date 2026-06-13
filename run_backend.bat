@echo off
setlocal

cd /d "%~dp0"
echo [INFO] Starting backend watchdog...
call "%CD%\backend\start_backend.bat"
endlocal


