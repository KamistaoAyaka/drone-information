@echo off
chcp 65001 >nul
echo ========================================================
echo  Git Repository Initialization
echo ========================================================
echo.

REM Check if .git directory exists
if exist .git (
    echo Warning: .git directory already exists.
    echo.
    set /p confirm=Continue? (y/n): 
    if /i not "!confirm!"=="y" (
        echo Cancelled.
        pause
        exit /b 0
    )
)

echo.
echo Checking Git installation...
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Git is not installed!
    echo Please install Git from: https://git-scm.com/download/win
    pause
    exit /b 1
)
echo OK: Git is installed
echo.

REM Create .gitignore file
if not exist .gitignore (
    echo Creating .gitignore file...
    (
        echo # Python
        echo __pycache____/
        echo *.pyc
        echo *.pyo
        echo.
        echo # Database
        echo data/*.db
        echo.
        echo # IDE
        echo .vscode__/
        echo .idea__/
        echo.
        echo # Temp files
        echo *.tmp
        echo *.log
    ) > .gitignore
)

REM Initialize Git repository
if not exist .git (
    echo Initializing Git repository...
    git init
)

echo.
echo ========================================================
echo  Setup Complete!
echo ========================================================
echo.
echo Next steps:
echo.
echo 1. Create GitHub repository at: https://github.com/new
echo 2. Run: git add static_site__/
echo 3. Run: git commit -m "Initial commit"
echo 4. Run: git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
echo 5. Run: git branch -M main
echo 6. Run: git push -u origin main
echo.
echo Please visit: https://github.com/new
echo.
start https://github.com/new
echo.
pause
