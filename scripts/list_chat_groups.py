# -*- coding: utf-8 -*-
"""
列出飞书群聊列表，帮助获取 FEISHU_CHAT_ID
运行方式：python list_chat_groups.py
"""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv

TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
CHAT_LIST_URL = "https://open.feishu.cn/open-apis/im/v1/chats"


def get_tenant_access_token(app_id: str, app_secret: str) -> str | None:
    try:
        response = requests.post(
            TOKEN_URL,
            json={"app_id": app_id, "app_secret": app_secret},
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"获取 Token 失败：{exc}")
        return None

    try:
        result = response.json()
    except ValueError:
        print("返回内容不是合法 JSON")
        return None

    if result.get("code") != 0:
        print(f"错误：code={result.get('code')}, msg={result.get('msg')}")
        return None

    return result.get("tenant_access_token")


def list_chats(tenant_access_token: str) -> list[dict] | None:
    headers = {"Authorization": f"Bearer {tenant_access_token}"}

    try:
        response = requests.get(
            CHAT_LIST_URL,
            headers=headers,
            params={"page_size": 50},
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"获取群列表失败：{exc}")
        return None

    try:
        result = response.json()
    except ValueError:
        print("返回内容不是合法 JSON")
        return None

    if result.get("code") != 0:
        print(f"错误：code={result.get('code')}, msg={result.get('msg')}")
        return None

    return result.get("data", {}).get("items", [])


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env")

    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")

    if not app_id or not app_secret:
        print("请先在 .env 中配置 FEISHU_APP_ID 和 FEISHU_APP_SECRET")
        return

    print("正在获取飞书访问令牌...")
    token = get_tenant_access_token(app_id, app_secret)
    if not token:
        return

    print("正在获取群聊列表...")
    chats = list_chats(token)
    if not chats:
        print("未获取到群聊列表")
        return

    print(f"\n共找到 {len(chats)} 个群聊：")
    print("-" * 80)
    for i, chat in enumerate(chats, 1):
        chat_id = chat.get("chat_id", "")
        name = chat.get("name", "")
        print(f"{i}. {name}")
        print(f"   chat_id: {chat_id}")
        print()


if __name__ == "__main__":
    main()