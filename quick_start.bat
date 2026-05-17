@echo off
title DroneScout - Quick Start

echo ================================================
echo   DroneScout - UAV Intelligence Collection
echo ================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo Please install Python 3.8+ from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python is installed

python -c "import flask" 2>nul
if errorlevel 1 (
    echo [INFO] Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Dependency installation failed!
        echo Please run: install_dependencies.bat
        pause
        exit /b 1
    )
    echo [OK] Dependencies installed
) else (
    echo [OK] Dependencies already installed
)

if not exist "data" (
    mkdir data
    echo [OK] Data directory created
)

echo.
echo ================================================
echo   Select operation:
echo ================================================
echo   1. Initialize sample data
echo   2. Start Web interface
echo   3. Collect all data
echo   4. View statistics
echo   5. Export data (JSON)
echo   6. Test system
echo   7. Exit
echo.

set /p choice=Enter choice [1-7]:

if "%choice%"=="1" goto :init
if "%choice%"=="2" goto :web
if "%choice%"=="3" goto :collect
if "%choice%"=="4" goto :stats
if "%choice%"=="5" goto :export
if "%choice%"=="6" goto :test
if "%choice%"=="7" goto :end

:init
echo.
echo Initializing sample data...
python drone_scout.py init
goto :done

:web
echo.
echo Starting Web service...
echo Please open in browser: http://localhost:5000
echo Press Ctrl+C to stop
echo.
python drone_scout.py web --port 5000
goto :done

:collect
echo.
echo Collecting data...
python drone_scout.py collect --all
goto :done

:stats
echo.
python drone_scout.py stats
goto :done

:export
echo.
echo Exporting data...
python drone_scout.py export --format json --output drone_export.json
if exist drone_export.json (
    echo [OK] Data exported to: drone_export.json
)
goto :done

:test
echo.
python test_system.py
goto :done

:done
echo.
echo ================================================
echo   Operation completed!
echo ================================================
pause
exit /b 0

:end
echo.
echo Goodbye!
exit /b 0
