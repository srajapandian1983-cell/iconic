@echo off
title SAM ICONIC - Project Upload  (keep this window open)
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo.
  echo   Python was not found on this PC. Install Python 3, then run this again.
  echo.
  pause
  exit /b 1
)

echo.
echo   ============================================================
echo    SAM ICONIC Development  -  Project Upload
echo   ============================================================
echo.
echo    The upload page will open in your browser in a few seconds:
echo        http://127.0.0.1:5000/upload
echo.
echo    KEEP THIS WINDOW OPEN while you upload projects.
echo    Close this window when you are finished.
echo.
echo   ============================================================
echo.

start "" /min powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep 5; Start-Process 'http://127.0.0.1:5000/upload'"

python app.py

echo.
echo   Server stopped. You can close this window.
pause
