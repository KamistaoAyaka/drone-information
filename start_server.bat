@echo off
title DroneScout - Web Server

echo ================================================
echo   Starting DroneScout Web Server
echo ================================================
echo.

echo [INFO] Server starting at: http://localhost:5000
echo [INFO] Press Ctrl+C to stop the server
echo.

cd /d "%~dp0"

python drone_scout.py web --port 5000

echo.
echo [INFO] Server stopped.
pause
