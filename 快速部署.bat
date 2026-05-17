@echo off
chcp 65001 >nul
echo ========================================================
echo 🚁 无人机资讯静态网站 - 快速启动工具
echo ========================================================
echo.

echo [1] 生成静态网站
echo [2] 本地预览网站
echo [3] 部署到GitHub
echo.
echo [4] 查看部署指南
echo [0] 退出
echo.

set /p choice="请选择操作 (0-4):

if "%choice%"=="1" goto generate
if "%choice%"=="2" goto preview
if "%choice%"=="3" goto deploy
if "%choice%"=="4" goto guide
if "%choice%"=="0" goto end
goto invalid

:generate
echo.
echo ========================================================
echo 🔄 正在生成静态网站...
echo ========================================================
python static_site_generator.py
if %errorlevel% neq 0 (
    echo ❌ 生成失败！
    pause
    exit /b 1
)
echo.
echo ✅ 静态网站生成成功！
echo 📁 位置: static_site\
echo.
pause
goto end

:preview
echo.
echo ========================================================
echo 🌐 正在启动本地预览...
echo ========================================================
echo 网站将在 http://localhost:8000 打开
echo 按 Ctrl+C 停止
echo.

cd static_site
start http://localhost:8000
python -m http.server 8000
cd ..
goto end

:deploy
echo.
echo ========================================================
echo 📦 部署到GitHub
echo ========================================================
echo.
echo 首先，请确保：
echo   1. 已有GitHub账号
echo   2. 已安装Git
echo   3. 已创建GitHub仓库
echo.
echo 详细步骤请查看 部署指南.md
echo.
pause

:guide
echo.
echo ========================================================
echo 📖 正在打开部署指南...
echo ========================================================
start "" "部署指南.md"
goto end

:invalid
echo.
echo ❌ 无效的选择！
echo.
pause
goto end

:end
echo.
echo 感谢使用！
echo.
