@echo off
chcp 65001 >nul
title 周报自动发布 · 调度管理

:: ============================================================
:: 周报自动发布调度管理（不需要管理员权限）
:: ============================================================

:main
cls
echo ========================================
echo  周报自动发布 · 调度管理
echo ========================================
echo.
echo 请选择操作：
echo.
echo  [1] 创建每周一 09:00 自动发布任务
echo  [2] 删除自动发布任务
echo  [3] 查看任务状态
echo  [4] 立即手动生成周报
echo  [5] 退出
echo.

set /p choice=请输入选项 (1-5): 

if "%choice%"=="1" (
    echo.
    echo 正在创建计划任务...
    python "%~dp0scripts\schedule_weekly_report.py" --create-task
    goto :end
)
if "%choice%"=="2" (
    echo.
    echo 正在删除计划任务...
    python "%~dp0scripts\schedule_weekly_report.py" --delete-task
    goto :end
)
if "%choice%"=="3" (
    echo.
    echo 正在查询任务状态...
    python "%~dp0scripts\schedule_weekly_report.py" --status
    goto :end
)
if "%choice%"=="4" (
    echo.
    echo 正在立即生成周报...
    python "%~dp0scripts\schedule_weekly_report.py" --run-now
    goto :end
)
if "%choice%"=="5" (
    echo.
    echo 退出...
    exit /b 0
)

echo.
echo ❌ 无效选项，请重新选择
pause >nul
goto :main

:end
echo.
echo 操作完成，按任意键退出...
pause >nul
