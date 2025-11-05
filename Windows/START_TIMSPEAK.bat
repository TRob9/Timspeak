@echo off
REM Timspeak Windows Launcher
REM Double-click this file to start Timspeak

REM Change to the directory where this script is located
cd /d "%~dp0"

echo ============================================================
echo Timspeak - AI-Powered Dictation System (Windows)
echo ============================================================
echo.
echo Current directory: %CD%
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    echo.
    pause
    exit /b 1
)

echo Python detected:
python --version
echo.

REM Check if config.yaml exists
if not exist "config.yaml" (
    echo WARNING: config.yaml not found
    echo Creating from config.yaml.example...
    copy config.yaml.example config.yaml >nul
    echo.
    echo IMPORTANT: Edit config.yaml and add your API keys before using Timspeak!
    echo.
    echo Opening config.yaml in notepad...
    start notepad config.yaml
    echo.
    echo Press any key after you have configured your API keys...
    pause
)

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install/update dependencies
echo Checking dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo WARNING: Some dependencies failed to install
    echo You may need to install them manually
    echo.
)

echo.
echo ============================================================
echo Starting Timspeak...
echo ============================================================
echo.

REM Start the application
python main.py

REM If the application exits, wait before closing
echo.
echo Timspeak has stopped.
pause
