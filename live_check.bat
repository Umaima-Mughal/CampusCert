@echo off
cd /d "%~dp0backend"
call "venv\Scripts\activate.bat"
echo The backend must be running (run_backend.bat) and the demo data must exist (seed_demo.bat).
echo Add --wait-expiry to also test automatic submit when time runs out. It takes about 70 seconds.
echo.
python ..\scripts\smoke_test_live.py %*
pause
