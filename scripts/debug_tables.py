# -*- coding: utf-8 -*-
"""列出多维表格中所有子表"""
import os, json
from pathlib import Path
import requests
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parents[1]
load_dotenv(project_root / ".env")

app_id = os.getenv("FEISHU_APP_ID")
app_secret = os.getenv("FEISHU_APP_SECRET")
app_token = os.getenv("BITABLE_APP_TOKEN")

r = requests.post(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    json={"app_id": app_id, "app_secret": app_secret},
)
token = r.json()["tenant_access_token"]

# 列出所有子表
url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables"
r2 = requests.get(url, headers={"Authorization": f"Bearer {token}"})
print(f"Status: {r2.status_code}")
data = r2.json()
print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])