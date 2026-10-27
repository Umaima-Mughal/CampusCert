@echo off
cd /d "%~dp0"
call "backend\venv\Scripts\activate.bat"
echo Bringing the database up to the latest version...
alembic upgrade head
if errorlevel 1 goto failed
echo.
echo The database is now on version:
alembic current
pause
exit /b 0
:failed
echo.
echo The migration failed. Read the message above, then see Troubleshooting in docs\RUN_GUIDE.md
pause
exit /b 1
