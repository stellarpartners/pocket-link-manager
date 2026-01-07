@echo off
title Pocket Link Manager
color 0A

echo ========================================
echo  Pocket Link Manager - Starting...
echo ========================================
echo.

REM Change to script directory FIRST (critical for relative paths)
cd /d "%~dp0"
echo Working directory: %CD%
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed!
    echo.
    echo Please install Python 3.12+ from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [1/3] Python found ✓
echo.

REM Check if database already exists and has data FIRST (before installing dependencies)
echo [2/3] Checking database...
python -c "from database.init_db import is_setup_complete; import sys; sys.exit(0 if is_setup_complete() else 1)" 2>nul
if errorlevel 1 (
    REM Database doesn't exist or is empty - need to install dependencies and initialize
    echo [2/3] Database not found, installing dependencies...
    pip install -e .
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        echo.
        pause
        exit /b 1
    )
    echo [2/3] Dependencies installed ✓
    echo.
    echo [2/3] Initializing database...
    python -c "from database.init_db import init_database; init_database()"
    if errorlevel 1 (
        echo ERROR: Database initialization failed!
        echo.
        pause
        exit /b 1
    )
    echo [2/3] Database initialized ✓
) else (
    echo [2/3] Database already set up ✓
)
echo.

REM Start server and open browser
echo [3/3] Starting web server...
echo.
echo ========================================
echo  Server starting at http://127.0.0.1:5000
echo  Browser will open automatically...
echo  Press Ctrl+C to stop the server
echo ========================================
echo.

REM Open browser after short delay (gives server time to start)
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:5000"

REM Start Flask server (this will block until Ctrl+C)
echo Starting Flask server...
python run.py

REM If we get here, server stopped
echo.
echo Server stopped.
pause
