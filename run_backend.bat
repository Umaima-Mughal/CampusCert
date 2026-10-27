@echo off
cd /d "%~dp0backend"
call "venv\Scripts\activate.bat"
echo Backend:   http://localhost:8000
echo API docs:  http://localhost:8000/docs
echo Health:    http://localhost:8000/health
echo Press Ctrl+C to stop.
echo.
uvicorn app.main:app --reload
pause
