@echo off
chcp 65001 >nul
echo ========================================================
echo  Static Site Generator - Quick Start
echo ========================================================
echo.

echo [1] Generate static site
echo [2] Preview locally
echo [3] Deploy to GitHub
echo.
echo [4] View deployment guide
echo [0] Exit
echo.

set /p choice="Select option (0-4): 

if "%choice%"=="1" goto generate
if "%choice%"=="2" goto preview
if "%choice%"=="3" goto deploy
if "%choice%"=="4" goto guide
if "%choice%"=="0" goto end
goto invalid

:generate
echo.
echo ========================================================
echo  Generating static site...
echo ========================================================
python static_site_generator.py
if %errorlevel% neq 0 (
    echo ERROR: Generation failed!
    pause
    exit /b 1
)
echo.
echo SUCCESS: Static site generated!
echo Location: static_site\
echo.
pause
goto end

:preview
echo.
echo ========================================================
echo  Starting local preview...
echo ========================================================
echo Site will open at: http://localhost:8000
echo Press Ctrl+C to stop
echo.

cd static_site
start http://localhost:8000
python -m http.server 8000
cd ..
goto end

:deploy
echo.
echo ========================================================
echo  Deploy to GitHub
echo ========================================================
echo.
echo Before deploying, make sure:
echo   1. Have a GitHub account
echo   2. Git is installed
echo   3. GitHub repository is created
echo.
echo For detailed steps, see: Deployment_Guide.md
echo.
pause

:guide
echo.
echo ========================================================
echo  Opening deployment guide...
echo ========================================================
start "" "Deployment_Guide.md"
goto end

:invalid
echo.
echo ERROR: Invalid option!
echo.
pause
goto end

:end
echo.
echo Thanks for using!
echo.
