@echo off
title Fix Git and Push

echo ========================================
echo    Fix Git and Push
echo ========================================
echo.
echo [1/3] Pulling remote updates...
git pull origin main --rebase
if errorlevel 1 (
    echo.
    echo ERROR: Pull failed
    echo.
    pause
    exit /b 1
)

echo.
echo [2/3] Pushing to remote...
git push
if errorlevel 1 (
    echo.
    echo ERROR: Push failed
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo    SUCCESS!
echo ========================================
echo.
pause
