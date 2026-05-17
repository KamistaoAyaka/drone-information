@echo off
title DroneScout - Restart Server

echo ================================================
echo   DroneScout - Clean Cache and Restart
echo ================================================
echo.

echo [Step 1] Stopping any running Python processes...
taskkill /f /im python.exe 2>NUL
taskkill /f /im pythonw.exe 2>NUL
echo [OK] Processes stopped

echo.
echo [Step 2] Cleaning cache files...
rmdir /s /q __pycache__ 2>NUL
rmdir /s /q api\__pycache__ 2>NUL
rmdir /s /q database\__pycache__ 2>NUL
rmdir /s /q scraper\__pycache__ 2>NUL
rmdir /s /q config\__pycache__ 2>NUL
del /f /q *.pyc 2>NUL
echo [OK] Cache cleaned

echo.
echo [Step 3] Starting server...
echo.
python drone_scout.py web --port 5000

pause