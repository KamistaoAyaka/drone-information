@echo off
title Update and Deploy

echo ========================================
echo    Update and Deploy
echo ========================================
echo.
echo [1/4] Checking Git status...
git status
if errorlevel 1 (
    echo ERROR: Git not installed or not a repo
    pause
    exit /b 1
)

echo.
echo [2/4] Generating static site...
python static_site_generator.py
if errorlevel 1 (
    echo ERROR: Static site generation failed
    pause
    exit /b 1
)

echo.
echo [3/4] Committing changes...
git add static_site/
git add .github/
git add *.bat
git add *.md
git add static_site_generator.py
git status
git diff --staged --quiet
if errorlevel 1 (
    for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
    set "datestr=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%"
    git commit -m "chore: update site [%datestr%]"
    echo SUCCESS: Committed changes
) else (
    echo INFO: No changes to commit
)

echo.
echo [4/4] Pushing to GitHub...
git push origin main
if errorlevel 1 (
    echo WARNING: Push may have failed
) else (
    echo SUCCESS: Pushed to GitHub
)

echo.
echo ========================================
echo    Deployment Complete!
echo ========================================
echo.
echo Cloudflare Pages will auto-deploy in 1-2 minutes
echo Visit: https://drone-information.pages.dev/
echo.
pause
