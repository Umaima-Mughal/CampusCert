@echo off
setlocal
cd /d "%~dp0"
set FAILED=0
call "backend\venv\Scripts\activate.bat"

echo ===== 1/4  Database: tables, columns, migrations =====
cd backend
python ..\scripts\check_database.py
if errorlevel 1 set FAILED=1

echo.
echo ===== 2/4  Backend tests =====
python -m pytest -q
if errorlevel 1 set FAILED=1

cd ..\frontend
echo.
echo ===== 3/4  Frontend tests =====
call npm test
if errorlevel 1 set FAILED=1

echo.
echo ===== 4/4  Frontend build =====
call npm run build
if errorlevel 1 set FAILED=1
cd ..

echo.
echo ============================================================
if "%FAILED%"=="0" goto passed
echo SOME CHECKS FAILED. Scroll up to the first FAIL or error message. See docs\RUN_GUIDE.md Troubleshooting.
goto end
:passed
echo ALL 4 CHECKS PASSED.
echo For the full login-to-result check on the running app, start run_backend.bat, then run live_check.bat
:end
echo ============================================================
pause
