#!/bin/bash

# Custom Metadata Server Starter for Linux/macOS
# This script starts the example custom metadata server

echo "========================================"
echo "Custom Metadata Server Starter"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.6 or later"
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "WARNING: pip3 is not installed"
    echo "Attempting to use python3 -m pip..."
    PIP_CMD="python3 -m pip"
else
    PIP_CMD="pip3"
fi

# Check if Flask is installed
if ! python3 -c "import flask" &> /dev/null; then
    echo "Flask is not installed. Installing..."
    $PIP_CMD install flask
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install Flask"
        echo "Please install Flask manually: $PIP_CMD install flask"
        exit 1
    fi
    echo "Flask installed successfully."
    echo ""
fi

# Check if requests is installed (for test script)
if ! python3 -c "import requests" &> /dev/null; then
    echo "Requests is not installed. Installing..."
    $PIP_CMD install requests
    if [ $? -ne 0 ]; then
        echo "WARNING: Failed to install requests"
        echo "Test script may not work properly"
    fi
    echo ""
fi

echo "Starting Custom Metadata Server..."
echo ""
echo "Server Information:"
echo "  URL: http://localhost:5000"
echo "  Health Check: http://localhost:5000/health"
echo "  Main Endpoint: POST http://localhost:5000/metadata"
echo "  Auth Token: Bearer test-token-123"
echo ""
echo "Calibre Plugin Configuration:"
echo "  Custom metadata server URL: http://localhost:5000/metadata"
echo "  Custom metadata auth token: Bearer test-token-123"
echo ""
echo "Press Ctrl+C to stop the server"
echo "========================================"
echo ""

# Start the server
python3 custom_metadata_server_example.py

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Failed to start server"
    echo "Possible issues:"
    echo "  1. Port 5000 is already in use"
    echo "  2. Python script has syntax errors"
    echo "  3. Missing dependencies"
    echo ""
    echo "Try running: python3 custom_metadata_server_example.py"
    exit 1
fi