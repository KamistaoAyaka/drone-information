@echo off
title DroneScout - Web Server

echo ================================================
echo   Starting DroneScout Web Server
echo ================================================
echo.

echo [INFO] Web interface will be available at:
echo.
echo     http://localhost:5000
echo.
echo [INFO] Press Ctrl+C to stop the server
echo.

python drone_scout.py web --port 5000

echo.
echo [INFO] Server stopped.
pause
