@echo off
echo Starting AI Mentor Application...
cd /d "%~dp0"
call .\backend\.venv\Scripts\python.exe launch_dev.py
echo.
echo Application started!
echo Frontend: http://127.0.0.1:5173/
echo Backend:  http://127.0.0.1:8000/health
pause
