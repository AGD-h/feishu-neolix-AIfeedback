@echo off
chcp 65001 >nul
echo ========================================
echo  无人配送反馈周报 · 自动发布脚本
echo ========================================
echo.

cd /d "%~dp0"
python -m report.weekly_report

echo.
echo 周报发布完成，按任意键退出...
pause >nul
