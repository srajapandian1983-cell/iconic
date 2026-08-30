@echo off
cd /d "%~dp0"
echo.
echo   ============================================================
echo    SAM ICONIC Development  -  Project Upload
echo   ============================================================
echo.
echo    Your browser will open this page in a few seconds:
echo        http://127.0.0.1:5000/upload
echo.
echo    KEEP THIS WINDOW OPEN while uploading. Close it when done.
echo   ============================================================
echo.
start "" cmd /c "timeout /t 6 >nul & start http://127.0.0.1:5000/upload"
python app.py
echo.
echo   Server stopped. You can close this window now.
pause
