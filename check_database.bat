@echo off
cd /d "%~dp0backend"
call "venv\Scripts\activate.bat"
python ..\scripts\check_database.py
pause
