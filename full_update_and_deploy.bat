@echo off
chcp 65001 >nul
title 无人机资讯完整更新部署

echo ========================================
echo    🚁 无人机资讯完整更新部署
echo    （含数据采集 + 静态网站生成 + 部署）
echo ========================================
echo.
echo ⚠️  此脚本将运行数据采集程序，可能需要较长时间
echo.
pause

echo.
echo [1/5] 运行数据采集程序...
python drone_scout.py
if errorlevel 1 (
    echo ❌ 数据采集失败
    pause
    exit /b 1
)
echo ✅ 数据采集完成

echo.
echo [2/5] 生成静态网站...
python static_site_generator.py
if errorlevel 1 (
    echo ❌ 静态网站生成失败
    pause
    exit /b 1
)

echo.
echo [3/5] 检查 Git 状态...
git status
if errorlevel 1 (
    echo ❌ Git 未安装或未初始化仓库
    pause
    exit /b 1
)

echo.
echo [4/5] 提交更新...
git add static_site/
git diff --staged --quiet
if errorlevel 1 (
    for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
    set "datestr=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%"
    git commit -m "chore: 更新资讯 [%datestr%]"
    echo ✅ 已提交更新
) else (
    echo ℹ️  没有需要更新的内容
)

echo.
echo [5/5] 推送到 GitHub...
git push
if errorlevel 1 (
    echo ⚠️  推送可能失败，请检查网络连接
) else (
    echo ✅ 已推送到 GitHub
)

echo.
echo ========================================
echo    ✅ 完整部署流程完成！
echo ========================================
echo.
echo Cloudflare Pages 将在 1-2 分钟内自动重新部署
echo 访问地址: https://drone-information.pages.dev/
echo.
pause
