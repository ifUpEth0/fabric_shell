@echo off
REM AI Fabric Shell - Windows Batch Script
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if fabric_shell directory exists
if not exist "fabric_shell" (
    echo Error: fabric_shell directory not found
    echo Please ensure you have the correct directory structure
    pause
    exit /b 1
)

REM Run the application
echo Starting AI Fabric Shell...
python run.py
pause