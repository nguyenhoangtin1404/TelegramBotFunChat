@echo off
setlocal enabledelayedexpansion

rem Change to project directory (the folder containing this script)
cd /d "%~dp0"

rem Activate virtual environment if present
if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
)

echo Starting Telegram Fun Chat bot in polling mode...
py polling_bot.py

if errorlevel 1 (
    echo Bot exited with error code %errorlevel%.
) else (
    echo Bot stopped.
)

pause
