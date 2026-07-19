# -*- coding: utf-8 -*-
"""调试群消息推送失败原因"""
import os, json
from pathlib import Path
import requests
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parents[1]
load_dotenv(project_root / ".env")

app_id = os.getenv("FEISHU_APP_ID")
app_secret = os.getenv("FEISHU_APP_SECRET")
chat_id = os.getenv("FEISHU_CHAT_ID")

r = requests.post(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    json={"app_id": app_id, "app_secret": app_secret},
)
token = r.json()["tenant_access_token"]

url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
body = {
    "receive_id": chat_id,
    "content": json.dumps({"text": "测试消息：周报推送测试"}),
    "msg_type": "text",
}

r2 = requests.post(
    url,
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    json=body,
)
print(f"Status: {r2.status_code}")
print(f"Body: {r2.text[:1000]}")