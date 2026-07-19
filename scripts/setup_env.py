# -*- coding: utf-8 -*-
"""
交互式 .env 配置向导（3号专用）
运行方式：在项目根目录执行 py scripts/setup_env.py
功能：引导你填写所有密钥，自动验证飞书鉴权，最后列出可用的群聊 chat_id
"""

import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv, set_key


TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
CHAT_LIST_URL = "https://open.feishu.cn/open-apis/im/v1/chats"
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"


def print_header(title: str) -> None:
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


def input_required(prompt: str, example: str = "") -> str:
    """要求用户输入非空值"""
    while True:
        if example:
            value = input(f"{prompt}\n  格式示例：{example}\n  > ").strip()
        else:
            value = input(f"{prompt}\n  > ").strip()
        if value:
            return value
        print("  ⚠️ 不能为空，请重新输入。")


def input_optional(prompt: str) -> str:
    """可选输入，允许跳过"""
    value = input(f"{prompt}\n  （可选，直接回车跳过）> ").strip()
    return value


def test_feishu_auth(app_id: str, app_secret: str) -> tuple[bool, str]:
    """测试飞书鉴权，返回 (是否成功, 错误信息)"""
    try:
        resp = requests.post(
            TOKEN_URL,
            json={"app_id": app_id, "app_secret": app_secret},
            timeout=10,
        )
        data = resp.json()
        code = data.get("code")
        if code == 0:
            return True, ""
        msg = data.get("msg", "未知错误")
        if code == 10014:
            return False, f"App Secret 无效（错误码 10014）。请检查是否复制完整（32位），或让 2号 重新生成。"
        if code == 99991663:
            return False, f"应用未授权（错误码 99991663）。请让 2号 在开放平台提交权限审批。"
        return False, f"飞书返回错误：code={code}, msg={msg}"
    except requests.RequestException as e:
        return False, f"网络请求失败：{e}\n请检查网络连接，或是否需要代理。"


def list_chats(token: str) -> list[dict]:
    """列出可用的群聊"""
    try:
        resp = requests.get(
            CHAT_LIST_URL,
            headers={"Authorization": f"Bearer {token}"},
            params={"page_size": 50},
            timeout=30,
        )
        data = resp.json()
        if data.get("code") != 0:
            return []
        return data.get("data", {}).get("items", [])
    except requests.RequestException:
        return []


def main() -> None:
    print_header("飞书周报模块 · 密钥配置向导")
    print()
    print("本脚本会引导你完成以下配置：")
    print("  1. DeepSeek API Key（你自己注册）")
    print("  2. 飞书 App ID / App Secret（向 2号 要，实时验证）")
    print("  3. 多维表格 token / table_id / 链接（向 2号 要）")
    print("  4. 飞书群 chat_id（自动列出供你选择）")
    print()
    print("所有密钥只写入你本地的 .env 文件，不会上传到任何地方。")
    print()

    # ---- 步骤 1：DeepSeek API Key ----
    print_header("步骤 1/4：DeepSeek API Key")
    print()
    print("用于 AI 聚类分析。如果你还没有：")
    print("  1. 打开 https://platform.deepseek.com")
    print("  2. 注册账号，充值 20 元（演示足够）")
    print("  3. 左侧菜单 → API Keys → 创建新的 API Key")
    print("  4. 复制 key（sk- 开头，只显示一次，请立即保存）")
    print()
    deepseek_key = input_required("请粘贴你的 DeepSeek API Key", "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    set_key(str(ENV_PATH), "DEEPSEEK_API_KEY", deepseek_key)
    print("  ✅ DeepSeek API Key 已写入 .env")

    # ---- 步骤 2：飞书 App ID + App Secret ----
    print_header("步骤 2/4：飞书自建应用凭证")
    print()
    print("这些需要向 2号 要。2号 的操作步骤：")
    print("  1. 打开 https://open.feishu.cn")
    print("  2. 开发者后台 → 自建应用 → 点击应用")
    print("  3. 左侧「凭证与基础信息」")
    print("  4. 复制 App ID（cli_ 开头，20位）和 App Secret（32位）")
    print("  5. 确保已开通「bitable:table:readonly」权限并审批通过")
    print()

    while True:
        app_id = input_required("请粘贴 FEISHU_APP_ID", "cli_xxxxxxxxxxxxxxxxxxxx")
        app_secret = input_required("请粘贴 FEISHU_APP_SECRET", "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")

        print()
        print("正在验证飞书鉴权...")
        ok, err = test_feishu_auth(app_id, app_secret)
        if ok:
            print("  ✅ 飞书鉴权成功！")
            break
        print(f"  ❌ {err}")
        print()
        retry = input("是否重新输入？(y/n，n 则跳过保存) > ").strip().lower()
        if retry != "y":
            print("  已跳过，稍后可以手动编辑 .env 文件。")
            return

    set_key(str(ENV_PATH), "FEISHU_APP_ID", app_id)
    set_key(str(ENV_PATH), "FEISHU_APP_SECRET", app_secret)
    print("  ✅ 飞书凭证已写入 .env")

    # 获取 token 用于后续步骤
    token_resp = requests.post(
        TOKEN_URL,
        json={"app_id": app_id, "app_secret": app_secret},
        timeout=10,
    )
    tenant_token = token_resp.json().get("tenant_access_token", "")

    # ---- 步骤 3：多维表格配置 ----
    print_header("步骤 3/4：多维表格配置")
    print()
    print("这些也需要向 2号 要。2号 的操作步骤：")
    print()
    print("  【BITABLE_APP_TOKEN 获取方法】")
    print("  1. 打开多维表格「无人配送反馈工单池」")
    print("  2. 看浏览器地址栏，URL 格式：")
    print("     https://xxx.feishu.cn/base/XXXXXXXXXXXXX?table=YYYYY")
    print("  3. /base/ 后面那段就是 APP_TOKEN（如 lotubQjiOavmzessY3fcEBRvnnNh）")
    print()
    print("  【BITABLE_TABLE_ID 获取方法】")
    print("  1. 在多维表格右上角点击「...」")
    print("  2. 选择「开发者模式」")
    print("  3. 按 F12 打开浏览器控制台")
    print("  4. 输入 console.log(window.currentTableId) 回车")
    print("  5. 复制输出的字符串（tbl 开头）")
    print()

    bitable_token = input_required("请粘贴 BITABLE_APP_TOKEN", "lotubQjiOavmzessY3fcEBRvnnNh")
    table_id = input_required("请粘贴 BITABLE_TABLE_ID", "tblDHNG89YyRCO72")

    set_key(str(ENV_PATH), "BITABLE_APP_TOKEN", bitable_token)
    set_key(str(ENV_PATH), "BITABLE_TABLE_ID", table_id)
    print("  ✅ 多维表格配置已写入 .env")

    # 多维表格完整链接（用于周报中引导 AI 问数）
    print()
    bitable_url = input_optional(
        "【BITABLE_URL】多维表格完整链接\n"
        "  让 2号 打开多维表格，把浏览器地址栏的完整 URL 复制给你"
    )
    if bitable_url:
        set_key(str(ENV_PATH), "BITABLE_URL", bitable_url)
        print("  ✅ BITABLE_URL 已写入 .env")
    else:
        print("  ⚠️ 已跳过，周报中将自动拼接链接（可能不准确）")

    # ---- 步骤 4：飞书群 chat_id（可选） ----
    print_header("步骤 4/4：飞书群配置（可选）")
    print()
    print("正在查询你的飞书群列表...")

    chats = list_chats(tenant_token)
    if not chats:
        print("  ⚠️ 未获取到群聊列表。")
        print("  可能原因：应用未开通 im:message 权限，或你不在任何群中。")
        print("  跳过此步骤，稍后可以手动填入。")
    else:
        print(f"\n  共找到 {len(chats)} 个群聊：")
        print("  " + "-" * 50)
        for i, chat in enumerate(chats, 1):
            name = chat.get("name", "未命名群")
            cid = chat.get("chat_id", "")
            print(f"  [{i}] {name}")
            print(f"      chat_id: {cid}")
        print("  " + "-" * 50)
        print()
        choice = input("请输入要推送周报的群序号（直接回车跳过）> ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(chats):
            chat_id = chats[int(choice) - 1]["chat_id"]
            set_key(str(ENV_PATH), "FEISHU_CHAT_ID", chat_id)
            print(f"  ✅ FEISHU_CHAT_ID 已写入 .env：{chat_id}")
        else:
            print("  已跳过。")

    # ---- 完成 ----
    print_header("配置完成！")
    print()
    print("你的 .env 文件已包含以下配置：")
    load_dotenv(ENV_PATH)
    for key in ["DEEPSEEK_API_KEY", "FEISHU_APP_ID", "FEISHU_APP_SECRET",
                "BITABLE_APP_TOKEN", "BITABLE_TABLE_ID", "BITABLE_URL", "FEISHU_CHAT_ID"]:
        val = os.getenv(key)
        if val:
            masked = val[:8] + "***" + val[-4:] if len(val) > 12 else "***"
            print(f"  ✅ {key}={masked}")
        else:
            print(f"  ⚠️ {key}=（未配置）")
    print()
    print("下一步：")
    print("  py report/weekly_report.py          # 在线模式生成周报")
    print("  py report/weekly_report.py --offline # 离线模式（用本地CSV测试）")


if __name__ == "__main__":
    main()