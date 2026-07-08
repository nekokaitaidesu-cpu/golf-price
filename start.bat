@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo  Loading latest cloud data...
echo ============================================
REM Sync data updated daily by GitHub Actions. Continue even if offline.
git fetch origin data --depth 1 --quiet 2>nul
if not errorlevel 1 (
  git checkout origin/data -- history.db .cache 2>nul
  git reset --quiet 2>nul
  echo  Sync done. Showing latest prices/history.
) else (
  echo  [!] Sync skipped ^(offline or no data branch^). Using existing local data.
)
echo.

echo ============================================
echo  Golf Price App - starting server
echo ============================================
echo.
echo  Keep this window open. Open in your browser:
echo.
echo    PC     : http://localhost:8000
echo    Phone  : http://172.20.10.11:8000
echo.
echo  To stop: press Ctrl+C here or close this window.
echo ============================================
echo.

REM Open the browser only after the server responds (avoids connection-refused)
start "" powershell -NoProfile -WindowStyle Hidden -Command "for($i=0;$i -lt 60;$i++){try{if((Invoke-WebRequest 'http://localhost:8000' -UseBasicParsing -TimeoutSec 1).StatusCode -eq 200){Start-Process 'http://localhost:8000';break}}catch{Start-Sleep -Milliseconds 800}}"

python -m uvicorn app:app --host 0.0.0.0 --port 8000

echo.
echo Server stopped. Press any key to close.
pause >nul