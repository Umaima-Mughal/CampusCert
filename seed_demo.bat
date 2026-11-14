@echo off
cd /d "%~dp0backend"
call "venv\Scripts\activate.bat"
python ..\scripts\seed_demo_data.py
pause
