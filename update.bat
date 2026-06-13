@echo off
cd /d C:\ai_erp_itac

echo === Git Pull ===
git pull

echo === Python Packages ===
if exist requirements.txt (
    pip install -r requirements.txt
)

echo === Frontend Build ===
if exist package.json (
    call npm install
    call npm run build
)

if exist frontend\package.json (
    cd frontend
    call npm install
    call npm run build
    cd ..
)

echo === Done ===
pause