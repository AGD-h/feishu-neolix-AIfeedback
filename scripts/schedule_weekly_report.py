# -*- coding: utf-8 -*-
"""
周报自动发布调度脚本

支持两种模式：
1. Windows 计划任务：创建每周一 09:00 自动执行的任务
2. 手动运行：直接执行一次周报生成

使用方法：
    # 创建 Windows 计划任务
    python scripts/schedule_weekly_report.py --create-task
    
    # 删除计划任务
    python scripts/schedule_weekly_report.py --delete-task
    
    # 查看当前任务状态
    python scripts/schedule_weekly_report.py --status
    
    # 手动执行一次（调试用）
    python scripts/schedule_weekly_report.py --run-now
"""

import argparse
import subprocess
import sys
import os
import ctypes
from pathlib import Path


TASK_NAME = "无人配送反馈周报自动发布"


def is_admin():
    """检查当前是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def elevate_privileges():
    """用 Windows API 直接触发 UAC 提权（最可靠方式）
    
    通过 ctypes 调用 ShellExecuteW，runas 动词会弹出标准 UAC 对话框。
    不依赖 PowerShell 或外部脚本文件。
    """
    print("🔒 需要管理员权限来创建计划任务")
    print("   正在请求 UAC 提权，请点击「是」...")

    script_path = Path(__file__).resolve()
    args = " ".join(sys.argv[1:])
    params = f'"{script_path}" {args}'

    try:
        # ShellExecuteW 参数: (父窗口, 动词, 文件, 参数, 目录, 窗口模式)
        # "runas" 动词触发 UAC 提权
        # 返回值大于 32 表示成功
        ret = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, params, None, 1
        )
        if ret > 32:
            return True
        else:
            print(f"❌ UAC 提权被拒绝或失败（返回码: {ret}）")
            return False
    except Exception as e:
        print(f"❌ 提权失败: {e}")
        return False


def run_weekly_report():
    """直接运行周报生成"""
    project_root = Path(__file__).resolve().parents[1]
    os.chdir(project_root)
    
    script_path = project_root / "report" / "weekly_report.py"
    result = subprocess.run(
        [sys.executable, "-m", "report.weekly_report"],
        capture_output=True,
        text=True,
        cwd=project_root
    )
    
    print("=== 周报执行结果 ===")
    print("STDOUT:")
    print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    print(f"返回码: {result.returncode}")
    
    return result.returncode == 0


def create_windows_task():
    """创建 Windows 计划任务：每周一 09:00 执行
    
    使用当前用户权限创建任务，不需要管理员权限。
    周报生成只是调用 Python 脚本和 HTTP API，不需要最高权限。
    """
    project_root = Path(__file__).resolve().parents[1]
    python_path = sys.executable
    
    # 检查脚本文件是否存在
    if not (project_root / "report" / "weekly_report.py").exists():
        print(f"❌ 脚本文件不存在: {project_root / 'report' / 'weekly_report.py'}")
        return False
    
    print(f"正在创建计划任务: {TASK_NAME}")
    print(f"执行命令: {python_path} -m report.weekly_report")
    print(f"工作目录: {project_root}")
    
    try:
        # 使用 schtasks 创建任务（不用 /rl highest，普通用户权限即可）
        # /ru 用当前用户，不用 SYSTEM
        result = subprocess.run(
            ["schtasks", "/create", "/tn", TASK_NAME,
             "/tr", f'"{python_path}" -m report.weekly_report',
             "/sc", "weekly", "/d", "MON", "/st", "09:00:00",
             "/f"],
            capture_output=True,
            text=True,
            cwd=project_root,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            print("✅ 计划任务创建成功！")
            print(f"   任务名称: {TASK_NAME}")
            print(f"   执行时间: 每周一 09:00")
            print(f"   执行命令: {python_path} -m report.weekly_report")
            return True
        else:
            error_msg = result.stderr.strip()
            if "拒绝访问" in error_msg:
                print("❌ 创建失败：权限不足")
                print("   请以管理员身份运行此脚本")
                return False
            print(f"❌ 计划任务创建失败")
            print(f"   错误信息: {error_msg}")
            return False
            
    except Exception as e:
        print(f"❌ 创建任务时发生异常: {e}")
        return False


def delete_windows_task():
    """删除 Windows 计划任务"""
    print(f"正在删除计划任务: {TASK_NAME}")
    
    try:
        result = subprocess.run(
            ['schtasks', '/delete', '/tn', TASK_NAME, '/f'],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            print("✅ 计划任务删除成功")
            return True
        else:
            error_msg = result.stderr.strip()
            if "拒绝访问" in error_msg:
                print("❌ 删除失败：权限不足，请以管理员身份运行")
            elif "找不到任务" in error_msg or "not found" in error_msg.lower():
                print("⚠️ 任务不存在，无需删除")
            else:
                print(f"❌ 计划任务删除失败: {error_msg}")
            return False
            
    except Exception as e:
        print(f"❌ 删除任务时发生异常: {e}")
        return False


def check_task_status():
    """检查计划任务状态"""
    print(f"正在查询任务状态: {TASK_NAME}")
    
    try:
        result = subprocess.run(
            ['schtasks', '/query', '/tn', TASK_NAME, '/fo', 'LIST'],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            print("✅ 任务存在")
            print(result.stdout)
            return True
        else:
            print("❌ 任务不存在")
            return False
            
    except Exception as e:
        print(f"❌ 查询任务时发生异常: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="周报自动发布调度")
    parser.add_argument("--create-task", action="store_true", help="创建 Windows 计划任务")
    parser.add_argument("--delete-task", action="store_true", help="删除 Windows 计划任务")
    parser.add_argument("--status", action="store_true", help="查看任务状态")
    parser.add_argument("--run-now", action="store_true", help="立即执行一次周报生成")
    
    args = parser.parse_args()
    
    # 创建/删除任务使用当前用户权限，不需要管理员权限
    # 周报生成只调用 Python 脚本和 HTTP API，普通权限即可
    if args.create_task:
        create_windows_task()
    elif args.delete_task:
        delete_windows_task()
    elif args.status:
        check_task_status()
    elif args.run_now:
        run_weekly_report()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
