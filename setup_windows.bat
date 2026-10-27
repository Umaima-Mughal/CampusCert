@echo off
setlocal
cd /d "%~dp0"
echo ===== CampusCert one-time setup =====
echo.
if not exist "backend\.env" goto noenv

echo [1/4] Python virtual environment
if not exist "backend\venv\Scripts\python.exe" goto makevenv
"backend\venv\Scripts\python.exe" -c "import sys" >nul 2>&1
if not errorlevel 1 goto venvok
echo The existing venv was copied from another computer and is broken. Removing it...
rmdir /s /q "backend\venv"
:makevenv
python -m venv "backend\venv"
if errorlevel 1 goto nopython
:venvok

echo.
echo [2/4] Installing backend packages. This can take a few minutes.
call "backend\venv\Scripts\activate.bat"
python -m pip install --upgrade pip --quiet
pip install -r "backend\requirements.txt" pytest
if errorlevel 1 goto pipfail

echo.
echo [3/4] Installing frontend packages
cd frontend
call npm install
if errorlevel 1 goto npmfail
cd ..

echo.
echo [4/4] Checking the database
cd backend
python ..\scripts\check_database.py
cd ..
echo.
echo Setup finished. Next steps are in docs\RUN_GUIDE.md
echo   run_migrations.bat    only if the check above reports missing tables
echo   run_backend.bat       keep this window open
echo   run_frontend.bat      in a second window
pause
exit /b 0

:noenv
echo ERROR: backend\.env was not found.
echo Copy .env.example to backend\.env, then fill in DATABASE_URL and JWT_SECRET_KEY.
pause
exit /b 1

:nopython
echo ERROR: Python was not found or the venv could not be created.
echo Install Python 3.11 or newer from python.org and tick Add python.exe to PATH, then run this again.
pause
exit /b 1

:pipfail
echo ERROR: installing the backend packages failed. Read the message above.
pause
exit /b 1

:npmfail
echo ERROR: npm install failed. Install Node.js 18 or newer from nodejs.org, restart VS Code, and run this again.
pause
exit /b 1
