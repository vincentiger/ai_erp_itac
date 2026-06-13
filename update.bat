@echo off
setlocal EnableExtensions EnableDelayedExpansion
title ITAC Project Update and Startup
color 0A

set "ROOT=C:\ai_erp_itac"

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
if exist "%ROOT%\frontend\package.json" (
    cd /d "%ROOT%\frontend" || exit /b 1
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
echo [5/7] Latest Commit:
git log --oneline -1

echo.
echo [6/7] Restart services...
taskkill /f /im nginx.exe /t >nul 2>&1
for /f %%I in ('netstat -aon ^| findstr ":8080" ^| findstr "LISTENING"') do (
    for /f "tokens=5" %%P in ("%%I") do taskkill /f /pid %%P >nul 2>&1
)

if exist "%ROOT%\startup.bat" (
    start "" /min cmd /c ""%ROOT%\startup.bat""
) else (
    echo [WARN] startup.bat not found, services not restarted automatically.
)

echo.
echo [7/7] Update and startup complete
echo Please verify the system in the browser.
echo.
echo ==================================
echo Finished
echo ==================================
pause
endlocal
