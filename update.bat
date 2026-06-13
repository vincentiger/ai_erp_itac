@echo off
setlocal EnableExtensions EnableDelayedExpansion
title ITAC Project Update and Startup
color 0A

set "ROOT=C:\ai_erp_itac"
set "NGINX_DIR=%ROOT%\nginx"
set "BACKEND_DIR=%ROOT%\backend"
set "FRONTEND_DIR=%ROOT%\frontend"

echo ==================================
echo ITAC Project Update and Startup
echo ==================================
echo.

cd /d "%ROOT%" || (
    echo [ERROR] Cannot enter %ROOT%
    pause
    exit /b 1
)

echo [1/7] Pull latest source...
git pull
if errorlevel 1 (
    echo.
    echo [ERROR] Git pull failed
    pause
    exit /b 1
)

echo.
echo [2/7] Remove .py files replaced by .pyd...
for /r "%ROOT%\backend" %%F in (*.pyd) do (
    set "PYFILE=%%~dpnF.py"
    if exist "!PYFILE!" (
        echo Removing !PYFILE!
        del /f /q "!PYFILE!"
    )
)

echo.
echo [3/7] Update Python packages...
if exist "%ROOT%\requirements.txt" (
    py -3.10 -m pip install -r "%ROOT%\requirements.txt"
    if errorlevel 1 (
        echo [ERROR] pip install failed
        pause
        exit /b 1
    )
) else (
    echo [WARN] requirements.txt not found, skip.
)

echo.
echo [4/7] Update Frontend...
if exist "%FRONTEND_DIR%\package.json" (
    cd /d "%FRONTEND_DIR%" || exit /b 1
    call npm install
    if errorlevel 1 (
        echo [ERROR] npm install failed
        pause
        exit /b 1
    )
    call npm run build
    if errorlevel 1 (
        echo [ERROR] npm run build failed
        pause
        exit /b 1
    )
    cd /d "%ROOT%"
) else (
    echo [WARN] frontend\package.json not found, skip.
)

echo.
echo [4.5/7] Deploy Frontend to nginx html folder...
if exist "%FRONTEND_DIR%\dist\index.html" (
    robocopy "%FRONTEND_DIR%\dist" "%NGINX_DIR%\html\ai" /E /MIR /R:1 /W:1 >nul
) else (
    echo [WARN] frontend dist not found, skip deploy.
)

echo.
echo [5/7] Latest Commit:
git log --oneline -1

echo.
echo.
echo [6/7] Restart services...

echo Stop backend on port 8080...
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":8080" ^| findstr "LISTENING"') do (
    echo Killing backend PID %%P
    taskkill /f /pid %%P >nul 2>&1
)

timeout /t 2 >nul

echo Start nginx...
if exist "%NGINX_DIR%\start_nginx.bat" (
    start "" /min cmd /c ""%NGINX_DIR%\start_nginx.bat" start"
) else if exist "%NGINX_DIR%\nginx.exe" (
    start "" "%NGINX_DIR%\nginx.exe" -c "%NGINX_DIR%\conf\nginx.conf"
) else (
    echo [WARN] nginx start script not found.
)

timeout /t 3 >nul

echo Start backend server...
if exist "%BACKEND_DIR%\start_backend.bat" (
    start "ITAC Backend" /min cmd /c ""%BACKEND_DIR%\start_backend.bat""
) else (
    start "ITAC Backend" /min cmd /c "cd /d %BACKEND_DIR% && py -3.10 server.py"
)

timeout /t 5 >nul

echo Check backend port 8080...
netstat -ano | findstr ":8080"
echo Check nginx port 81...
netstat -ano | findstr ":81"

echo.
echo [7/7] Update and startup complete
echo Please verify the system in the browser.
echo.
echo ==================================
echo Finished
echo ==================================
pause
endlocal
