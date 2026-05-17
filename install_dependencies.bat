@echo off
title DroneScout - Install Dependencies

echo ================================================
echo   DroneScout - Dependency Installer
echo ================================================
echo.

echo [Step 1] Upgrading pip...
python -m pip install --upgrade pip

if errorlevel 1 (
    echo [ERROR] pip upgrade failed
    pause
    exit /b 1
)

echo.
echo [Step 2] Installing dependencies...
echo.

echo Installing: flask==2.3.3
pip install flask==2.3.3
if errorlevel 1 goto :install_failed

echo.
echo Installing: requests==2.31.0
pip install requests==2.31.0
if errorlevel 1 goto :install_failed

echo.
echo Installing: beautifulsoup4==4.12.2
pip install beautifulsoup4==4.12.2
if errorlevel 1 goto :install_failed

echo.
echo Installing: lxml...
echo NOTE: If lxml fails, you need Visual Studio Build Tools
pip install lxml
if errorlevel 1 (
    echo.
    echo [WARNING] lxml installation failed!
    echo.
    echo Please install Visual Studio Build Tools:
    echo   1. Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
    echo   2. Run installer, select "Desktop development with C++"
    echo   3. Then run this script again
    echo.
    set /p choice=Continue with other dependencies? (y/n):
    if /i "!choice!" neq "y" goto :end
)

echo.
echo Installing: jieba==0.42.1
pip install jieba==0.42.1
if errorlevel 1 goto :install_failed

echo.
echo Installing: simhash==2.1.2
pip install simhash==2.1.2
if errorlevel 1 goto :install_failed

echo.
echo Installing: APScheduler==3.10.4
pip install APScheduler==3.10.4
if errorlevel 1 goto :install_failed

echo.
echo ================================================
echo   Dependencies installed successfully!
echo ================================================
echo.
echo Verifying imports...

python -c "import flask; import requests; import bs4; import jieba; import simhash; import apscheduler; print('[OK] All dependencies imported successfully!')"

if errorlevel 1 (
    echo [ERROR] Import test failed
    echo Please check if lxml is installed correctly
    pause
    exit /b 1
)

echo.
echo [OK] Ready to run the main program!
echo Run: python drone_scout.py init
echo.

goto :done

:install_failed
echo.
echo ================================================
echo   [ERROR] Installation failed
echo ================================================
echo.
echo Please try:
echo 1. Run as Administrator
echo 2. Install Visual Studio Build Tools
echo    https://visualstudio.microsoft.com/visual-cpp-build-tools/
echo.
goto :end

:end
pause
exit /b 1

:done
pause
