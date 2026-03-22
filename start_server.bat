@echo off
REM Custom Metadata Server Starter for Windows
REM This batch file starts the example custom metadata server

echo ========================================
echo Custom Metadata Server Starter
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.6 or later
    pause
    exit /b 1
)

REM Check if Flask is installed
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo Flask is not installed. Installing...
    pip install flask
    if errorlevel 1 (
        echo ERROR: Failed to install Flask
        echo Please install Flask manually: pip install flask
        pause
        exit /b 1
    )
    echo Flask installed successfully.
    echo.
)

REM Check if requests is installed (for test script)
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo Requests is not installed. Installing...
    pip install requests
    if errorlevel 1 (
        echo WARNING: Failed to install requests
        echo Test script may not work properly
    )
    echo.
)

echo Starting Custom Metadata Server...
echo.
echo Server Information:
echo   URL: http://localhost:5000
echo   Health Check: http://localhost:5000/health
echo   Main Endpoint: POST http://localhost:5000/metadata
echo   Auth Token: Bearer test-token-123
echo.
echo Calibre Plugin Configuration:
echo   Custom metadata server URL: http://localhost:5000/metadata
echo   Custom metadata auth token: Bearer test-token-123
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

REM Start the server
python custom_metadata_server_example.py

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start server
    echo Possible issues:
    echo   1. Port 5000 is already in use
    echo   2. Python script has syntax errors
    echo   3. Missing dependencies
    echo.
    echo Try running: python custom_metadata_server_example.py
    pause
    exit /b 1
)