# -*- coding: utf-8 -*-
"""调试：查看飞书多维表格读取记录时的具体错误"""
import os
from pathlib import Path
import requests
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parents[1]
load_dotenv(project_root / ".env")

app_id = os.getenv("FEISHU_APP_ID")
app_secret = os.getenv("FEISHU_APP_SECRET")
app_token = os.getenv("BITABLE_APP_TOKEN")
table_id = os.getenv("BITABLE_TABLE_ID")

# 1. 获取 token
r = requests.post(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    json={"app_id": app_id, "app_secret": app_secret},
)
token = r.json()["tenant_access_token"]
print(f"Token: {token[:10]}...")

# 2. 读取记录，看详细错误
url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
print(f"URL: {url}")

r2 = requests.get(
    url,
    headers={"Authorization": f"Bearer {token}"},
    params={"page_size": 10},
)
print(f"Status: {r2.status_code}")
print(f"Body: {r2.text[:1000]}")