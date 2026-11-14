@echo off
cd /d "%~dp0frontend"
echo Frontend: http://localhost:5173   (the backend must be running too)
echo Press Ctrl+C to stop.
echo.
call npm run dev
pause
