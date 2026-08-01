@echo off
setlocal EnableExtensions EnableDelayedExpansion
title ITAC Client Update
color 0A

if not defined ITAC_UPDATE_ROOT set "ITAC_UPDATE_ROOT=%~dp0"
set "ROOT=%ITAC_UPDATE_ROOT%"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
set "RELEASE_ROOT=%ROOT%\release"
set "STAGING_DIR=%RELEASE_ROOT%\staging"
set "LOCAL_PACKAGE=%ROOT%\release.zip"
set "PACKAGE_URL=https://www.volx.com:2083/ai_erp/release.zip"
set "DOWNLOADED_ZIP=%RELEASE_ROOT%\release.download.zip"
set "LOG_FILE=%RELEASE_ROOT%\update.log"
set "VERSION_FILE=%RELEASE_ROOT%\version.txt"
set "RUNNING_COPY=%RELEASE_ROOT%\update.running.bat"

if /I not "%~f0"=="%RUNNING_COPY%" (
    if not exist "%RELEASE_ROOT%" mkdir "%RELEASE_ROOT%"
    copy /y "%~f0" "%RUNNING_COPY%" >nul
    set "ITAC_UPDATE_ROOT=%ROOT%"
    call "%RUNNING_COPY%"
    exit /b !ERRORLEVEL!
)

echo ==================================
echo ITAC Client Update
echo ==================================
echo.

if not exist "%RELEASE_ROOT%" mkdir "%RELEASE_ROOT%"
if exist "%STAGING_DIR%" rmdir /s /q "%STAGING_DIR%"
mkdir "%STAGING_DIR%"
if not exist "%ROOT%\nginx\logs" mkdir "%ROOT%\nginx\logs"
> "%LOG_FILE%" echo [%DATE% %TIME%] update started
>> "%LOG_FILE%" echo ROOT=%ROOT%
>> "%LOG_FILE%" echo RELEASE_ROOT=%RELEASE_ROOT%
>> "%LOG_FILE%" echo STAGING_DIR=%STAGING_DIR%

if exist "%LOCAL_PACKAGE%" (
    echo [1/5] Using local release package...
    copy /y "%LOCAL_PACKAGE%" "%DOWNLOADED_ZIP%" >nul
    >> "%LOG_FILE%" echo local release package copied
) else (
    echo [1/5] Download release package...
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri '%PACKAGE_URL%' -OutFile '%DOWNLOADED_ZIP%'"
    if errorlevel 1 (
        echo [ERROR] Failed to download release.zip
        pause
        exit /b 1
    )
    >> "%LOG_FILE%" echo release package downloaded
)
for %%I in ("%DOWNLOADED_ZIP%") do >> "%LOG_FILE%" echo zip path=%%~fI size=%%~zI
for /f "usebackq delims=" %%H in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "(Get-FileHash -Algorithm SHA256 '%DOWNLOADED_ZIP%').Hash"`) do set "PACKAGE_HASH=%%H"
for /f "usebackq delims=" %%H in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "(Get-FileHash -Algorithm SHA256 '%~f0').Hash"`) do set "UPDATE_BAT_HASH=%%H"
>> "%LOG_FILE%" echo package sha256=!PACKAGE_HASH!
>> "%LOG_FILE%" echo update.bat sha256=!UPDATE_BAT_HASH!
> "%VERSION_FILE%" (
    echo package_sha256=!PACKAGE_HASH!
    echo update_bat_sha256=!UPDATE_BAT_HASH!
    echo package_path=%DOWNLOADED_ZIP%
    echo update_time=%DATE% %TIME%
)

echo [2/5] Verify release package...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$src='%DOWNLOADED_ZIP%'; $log='%LOG_FILE%';" ^
    "try {" ^
    "  Add-Type -AssemblyName System.IO.Compression.FileSystem;" ^
    "  $zip=[System.IO.Compression.ZipFile]::OpenRead($src);" ^
    "  try { Add-Content -LiteralPath $log -Value ('zip verify ok entries=' + $zip.Entries.Count); }" ^
    "  finally { $zip.Dispose(); }" ^
    "  exit 0" ^
    "} catch {" ^
    "  Add-Content -LiteralPath $log -Value ('zip verify failed: release.zip is incomplete or corrupted. Please re-copy or re-download the package. ' + $_.Exception.ToString());" ^
    "  exit 1" ^
    "}"
if errorlevel 1 (
    echo [ERROR] release.zip is incomplete or corrupted.
    echo [ERROR] Please re-copy or re-download release.zip, then run update.bat again.
    echo [ERROR] Please open log: "%LOG_FILE%"
    pause
    exit /b 1
)

echo [2/5] Extract release package using safe extractor...
where tar.exe >nul 2>&1
if not errorlevel 1 (
    echo [2/5] Extract with Windows tar...
    >> "%LOG_FILE%" echo extract using tar.exe
    tar.exe -xf "%DOWNLOADED_ZIP%" -C "%STAGING_DIR%" >> "%LOG_FILE%" 2>&1
    if not errorlevel 1 (
        for /f %%C in ('powershell -NoProfile -ExecutionPolicy Bypass -Command "(Get-ChildItem -LiteralPath ''%STAGING_DIR%'' -Recurse -File | Measure-Object).Count"') do set "EXTRACT_COUNT=%%C"
        >> "%LOG_FILE%" echo extract ok files=!EXTRACT_COUNT!
        goto EXTRACT_DONE
    )
    >> "%LOG_FILE%" echo tar.exe extract failed, fallback to PowerShell stream extractor
) else (
    >> "%LOG_FILE%" echo tar.exe not found
)

set "PY_EXTRACT="
if exist "%ROOT%\.venv_local\Scripts\python.exe" set "PY_EXTRACT=%ROOT%\.venv_local\Scripts\python.exe"
if not defined PY_EXTRACT if exist "%ROOT%\.venv\Scripts\python.exe" set "PY_EXTRACT=%ROOT%\.venv\Scripts\python.exe"
if not defined PY_EXTRACT if exist "%ROOT%\backend\venv\Scripts\python.exe" set "PY_EXTRACT=%ROOT%\backend\venv\Scripts\python.exe"
if not defined PY_EXTRACT if exist "%ROOT%\venv\Scripts\python.exe" set "PY_EXTRACT=%ROOT%\venv\Scripts\python.exe"
if defined PY_EXTRACT (
    echo [2/5] Extract with Python zipfile...
    >> "%LOG_FILE%" echo extract using python "%PY_EXTRACT%"
    "%PY_EXTRACT%" -c "import os,sys,zipfile; src,dst=sys.argv[1],sys.argv[2]; z=zipfile.ZipFile(src); z.extractall(dst); z.close(); print('python extract ok files=' + str(sum(len(files) for _,_,files in os.walk(dst))))" "%DOWNLOADED_ZIP%" "%STAGING_DIR%" >> "%LOG_FILE%" 2>&1
    if not errorlevel 1 (
        for /f %%C in ('powershell -NoProfile -ExecutionPolicy Bypass -Command "(Get-ChildItem -LiteralPath ''%STAGING_DIR%'' -Recurse -File | Measure-Object).Count"') do set "EXTRACT_COUNT=%%C"
        >> "%LOG_FILE%" echo extract ok files=!EXTRACT_COUNT!
        goto EXTRACT_DONE
    )
    >> "%LOG_FILE%" echo python extract failed, fallback to PowerShell stream extractor
) else (
    >> "%LOG_FILE%" echo python extractor not found
)
py -3.10 -c "import zipfile" >nul 2>&1
if not errorlevel 1 (
    echo [2/5] Extract with py -3.10 zipfile...
    >> "%LOG_FILE%" echo extract using py -3.10
    py -3.10 -c "import os,sys,zipfile; src,dst=sys.argv[1],sys.argv[2]; z=zipfile.ZipFile(src); z.extractall(dst); z.close(); print('py launcher extract ok files=' + str(sum(len(files) for _,_,files in os.walk(dst))))" "%DOWNLOADED_ZIP%" "%STAGING_DIR%" >> "%LOG_FILE%" 2>&1
    if not errorlevel 1 (
        for /f %%C in ('powershell -NoProfile -ExecutionPolicy Bypass -Command "(Get-ChildItem -LiteralPath ''%STAGING_DIR%'' -Recurse -File | Measure-Object).Count"') do set "EXTRACT_COUNT=%%C"
        >> "%LOG_FILE%" echo extract ok files=!EXTRACT_COUNT!
        goto EXTRACT_DONE
    )
    >> "%LOG_FILE%" echo py -3.10 extract failed, fallback to python command
)
python -c "import zipfile" >nul 2>&1
if not errorlevel 1 (
    echo [2/5] Extract with python zipfile...
    >> "%LOG_FILE%" echo extract using python command
    python -c "import os,sys,zipfile; src,dst=sys.argv[1],sys.argv[2]; z=zipfile.ZipFile(src); z.extractall(dst); z.close(); print('python command extract ok files=' + str(sum(len(files) for _,_,files in os.walk(dst))))" "%DOWNLOADED_ZIP%" "%STAGING_DIR%" >> "%LOG_FILE%" 2>&1
    if not errorlevel 1 (
        for /f %%C in ('powershell -NoProfile -ExecutionPolicy Bypass -Command "(Get-ChildItem -LiteralPath ''%STAGING_DIR%'' -Recurse -File | Measure-Object).Count"') do set "EXTRACT_COUNT=%%C"
        >> "%LOG_FILE%" echo extract ok files=!EXTRACT_COUNT!
        goto EXTRACT_DONE
    )
    >> "%LOG_FILE%" echo python command extract failed, fallback to PowerShell stream extractor
)
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$src='%DOWNLOADED_ZIP%'; $dst='%STAGING_DIR%'; $log='%LOG_FILE%';" ^
    "try {" ^
    "  Add-Type -AssemblyName System.IO.Compression.FileSystem;" ^
    "  Add-Content -LiteralPath $log -Value 'extract prepare';" ^
    "  New-Item -ItemType Directory -Path $dst -Force | Out-Null;" ^
    "  Add-Content -LiteralPath $log -Value 'extract staging ready';" ^
    "  $dstFull=[System.IO.Path]::GetFullPath($dst);" ^
    "  if (-not $dstFull.EndsWith([System.IO.Path]::DirectorySeparatorChar)) { $dstFull += [System.IO.Path]::DirectorySeparatorChar };" ^
    "  $zip=[System.IO.Compression.ZipFile]::OpenRead($src);" ^
    "  Add-Content -LiteralPath $log -Value ('extract zip opened entries=' + $zip.Entries.Count);" ^
    "  $count=0;" ^
    "  try {" ^
    "    foreach ($entry in $zip.Entries) {" ^
    "      $name=$entry.FullName.Replace('\','/').TrimStart('/');" ^
    "      if ($name.StartsWith('./')) { $name=$name.Substring(2); }" ^
    "      if ([string]::IsNullOrWhiteSpace($name) -or $name.EndsWith('/')) { continue; }" ^
    "      $parts=$name.Split('/');" ^
    "      foreach ($part in $parts) {" ^
    "        if ([string]::IsNullOrWhiteSpace($part) -or $part -eq '.' -or $part -eq '..' -or $part.IndexOfAny([System.IO.Path]::GetInvalidFileNameChars()) -ge 0) { throw ('Blocked unsafe zip entry: ' + $entry.FullName); }" ^
    "      }" ^
    "      $relative=$parts -join [System.IO.Path]::DirectorySeparatorChar;" ^
    "      $target=[System.IO.Path]::Combine($dstFull, $relative);" ^
    "      $dir=[System.IO.Path]::GetDirectoryName($target);" ^
    "      if (-not [System.IO.Directory]::Exists($dir)) { [System.IO.Directory]::CreateDirectory($dir) | Out-Null; }" ^
    "      $in=$entry.Open();" ^
    "      try { $out=[System.IO.File]::Create($target); try { $in.CopyTo($out); } finally { $out.Dispose(); } }" ^
    "      finally { $in.Dispose(); }" ^
    "      $count++;" ^
    "      if (($count -le 10) -or (($count %% 25) -eq 0)) { Add-Content -LiteralPath $log -Value ('extract progress files=' + $count + ' last=' + $name); }" ^
    "    }" ^
    "  } finally { $zip.Dispose(); }" ^
    "  Add-Content -LiteralPath $log -Value ('extract ok files=' + $count);" ^
    "  exit 0" ^
    "} catch {" ^
    "  Add-Content -LiteralPath $log -Value ('extract failed: ' + $_.Exception.ToString());" ^
    "  exit 1" ^
    "}"
if errorlevel 1 (
    echo [ERROR] Failed to extract release.zip
    echo [ERROR] Please open log: "%LOG_FILE%"
    pause
    exit /b 1
)
:EXTRACT_DONE
>> "%LOG_FILE%" echo release package extracted

echo.
echo [3/5] Stop running app processes...
taskkill /f /im nginx.exe /t >nul 2>&1
taskkill /f /im python.exe /t >nul 2>&1
>> "%LOG_FILE%" echo processes stopped

echo.
echo [4/5] Deploy files to installed root...
robocopy "%STAGING_DIR%" "%ROOT%" /E /R:1 /W:1 ^
    /XD ".git" "release" "logs" "node_modules" "dist" "build" "__pycache__" ".venv" ".venv_local" "ssl" ^
    /XF ".env" "release.zip" "*.pyc" "*.pyo" "*.log" "*.bak" >nul
if errorlevel 8 (
    echo [ERROR] Deployment copy failed
    >> "%LOG_FILE%" echo deployment failed robocopy exit=%ERRORLEVEL%
    pause
    exit /b 1
)
>> "%LOG_FILE%" echo deployment copied

echo [4/5] Remove stale realtime compiled module...
if exist "%ROOT%\backend\routes\realtime.cp310-win_amd64.pyd" (
    del /f /q "%ROOT%\backend\routes\realtime.cp310-win_amd64.pyd" >nul 2>&1
    >> "%LOG_FILE%" echo removed stale backend\routes\realtime.cp310-win_amd64.pyd
)
if exist "%ROOT%\backend\routes\__pycache__\realtime.cpython-310.pyc" (
    del /f /q "%ROOT%\backend\routes\__pycache__\realtime.cpython-310.pyc" >nul 2>&1
    >> "%LOG_FILE%" echo removed stale backend\routes\__pycache__\realtime.cpython-310.pyc
)
if exist "%ROOT%\backend\routes\__pycache__\realtime*.pyc" (
    del /f /q "%ROOT%\backend\routes\__pycache__\realtime*.pyc" >nul 2>&1
    >> "%LOG_FILE%" echo removed stale backend\routes\__pycache__\realtime*.pyc
)

echo.
echo [4/5] Apply SQL migrations...
set "MIGRATION_PY="
if exist "%ROOT%\backend\venv\Scripts\python.exe" set "MIGRATION_PY=%ROOT%\backend\venv\Scripts\python.exe"
if not defined MIGRATION_PY if exist "%ROOT%\.venv_local\Scripts\python.exe" set "MIGRATION_PY=%ROOT%\.venv_local\Scripts\python.exe"
if not defined MIGRATION_PY if exist "%ROOT%\.venv\Scripts\python.exe" set "MIGRATION_PY=%ROOT%\.venv\Scripts\python.exe"
if not defined MIGRATION_PY if exist "%ROOT%\venv\Scripts\python.exe" set "MIGRATION_PY=%ROOT%\venv\Scripts\python.exe"
if not defined MIGRATION_PY (
    where py >nul 2>&1
    if not errorlevel 1 (
        set "MIGRATION_PY=py -3"
    )
)
if not defined MIGRATION_PY (
    where python >nul 2>&1
    if not errorlevel 1 (
        set "MIGRATION_PY=python"
    )
)
if not defined MIGRATION_PY (
    echo [ERROR] Python not found for SQL migrations.
    >> "%LOG_FILE%" echo sql migrations skipped: python not found
    pause
    exit /b 1
)
>> "%LOG_FILE%" echo apply migrations using !MIGRATION_PY!
call !MIGRATION_PY! "%ROOT%\backend\tools\apply_sql_updates.py"
if errorlevel 1 (
    echo [ERROR] SQL migrations failed.
    >> "%LOG_FILE%" echo sql migrations failed
    pause
    exit /b 1
)
>> "%LOG_FILE%" echo sql migrations complete

echo.
echo [5/5] Cleanup staging...
rmdir /s /q "%STAGING_DIR%" >nul 2>&1
del /f /q "%DOWNLOADED_ZIP%" >nul 2>&1
>> "%LOG_FILE%" echo staging cleaned

echo.
echo [5/5] Restart services...
taskkill /f /im nginx.exe /t >nul 2>&1
taskkill /f /im chrome.exe /t >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8080" ^| findstr "LISTENING"') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":81" ^| findstr "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

echo [0/5] Clearing Chrome cache...
for /d %%D in ("%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache" "%LOCALAPPDATA%\Google\Chrome\User Data\Default\Code Cache" "%LOCALAPPDATA%\Google\Chrome\User Data\Default\GPUCache" "%LOCALAPPDATA%\Google\Chrome\User Data\Default\Service Worker\CacheStorage" "%LOCALAPPDATA%\Google\Chrome\User Data\Default\Service Worker\ScriptCache") do (
    if exist "%%~D" rmdir /s /q "%%~D" >nul 2>&1
)
for /d %%D in ("%LOCALAPPDATA%\Google\Chrome\User Data\Default\Network\Cache") do (
    if exist "%%~D" rmdir /s /q "%%~D" >nul 2>&1
)

if not exist "%ROOT%\logs" mkdir "%ROOT%\logs"

echo [1/2] Starting nginx...
"%ROOT%\nginx\nginx.exe" -t -p "%ROOT%\nginx" -c "conf\nginx.conf"
if errorlevel 1 (
    echo [ERROR] nginx configuration test failed.
    pause
    exit /b 1
)
start "" /b "%ROOT%\nginx\nginx.exe" -p "%ROOT%\nginx" -c "conf\nginx.conf" >"%ROOT%\logs\nginx.update.log" 2>&1

echo [2/2] Starting backend...
start "" /b "%ROOT%\backend\start_backend.bat"
if errorlevel 1 (
    echo [ERROR] Backend start failed.
    pause
    exit /b 1
)

echo [WAIT] Waiting for backend port 8080...
set /a BACKEND_WAIT=0
:WAIT_BACKEND2
netstat -ano | findstr ":8080" | findstr "LISTENING" >nul
if %errorlevel% equ 0 goto BACKEND_READY2
set /a BACKEND_WAIT+=1
if !BACKEND_WAIT! geq 30 (
    echo [ERROR] Backend did not start within 30 seconds.
    echo [ERROR] Check the backend window or backend log for the actual error.
    >> "%LOG_FILE%" echo backend did not start within 30 seconds
    pause
    exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Sleep -Seconds 1" >nul 2>&1
goto WAIT_BACKEND2

:BACKEND_READY2
echo [OK] Backend port 8080 is ready.
>> "%LOG_FILE%" echo backend ready

echo.
echo [OK] Update complete.
>> "%LOG_FILE%" echo update complete
echo.
pause
endlocal & exit /b 0
