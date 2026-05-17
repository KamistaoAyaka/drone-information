@echo off
chcp 65001 >nul
echo ========================================================
echo 📦 初始化Git仓库 - 准备部署
echo ========================================================
echo.

REM 检查是否已有.git目录
if exist .git (
    echo ⚠️  警告：.git目录已存在，可能已经初始化过。
    echo.
    set /p confirm="是否继续？(y/n): "
    if /i not "%confirm%"=="y" (
        echo 已取消。
        pause
        exit /b 0
    )
)

echo.
echo 正在检查Git是否安装...
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Git未安装！请先安装Git: https://git-scm.com/download/win
    pause
    exit /b 1
)
echo ✅ Git已安装
echo.

REM 创建.gitignore文件
if not exist .gitignore (
    echo 创建 .gitignore 文件...
    (
        echo # Python
        echo __pycache__/
        echo *.pyc
        echo *.pyo
        echo.
        echo # 数据库
        echo data/*.db
        echo.
        echo # IDE
        echo .vscode/
        echo .idea/
        echo.
        echo # 临时文件
        echo *.tmp
        echo *.log
    ) > .gitignore
)

REM 初始化Git仓库
if not exist .git (
    echo 正在初始化Git仓库...
    git init
)

echo.
echo ========================================================
echo ✅ 准备就绪！
echo ========================================================
echo.
echo 请按以下步骤操作：
echo.
echo 1. 在GitHub上创建仓库
echo 2. 运行: git add static_site/
echo 3. 运行: git commit -m "初始化"
echo 4. 运行: git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
echo 5. 运行: git branch -M main
echo 6. 运行: git push -u origin main
echo.
echo 详细步骤请查看 部署指南.md
echo.
echo 访问 GitHub: https://github.com/new
echo.
start https://github.com/new
echo.
pause
