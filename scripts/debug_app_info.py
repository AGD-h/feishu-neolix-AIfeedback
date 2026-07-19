# -*- coding: utf-8 -*-
"""查看当前 App ID 对应的应用名称，确认是不是同一个应用"""
import os, json
from pathlib import Path
import requests
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parents[1]
load_dotenv(project_root / ".env")

app_id = os.getenv("FEISHU_APP_ID")
app_secret = os.getenv("FEISHU_APP_SECRET")

# 获取 tenant_access_token
r = requests.post(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    json={"app_id": app_id, "app_secret": app_secret},
)
token = r.json()["tenant_access_token"]

# 调用应用信息接口看看应用名称
# 注意：没有直接查应用名的开放接口，但我们可以通过通讯录应用列表试试
# 换个思路：直接列出应用能访问的所有多维表格，看看有哪些
url = "https://open.feishu.cn/open-apis/drive/v1/files"
r2 = requests.get(
    url,
    headers={"Authorization": f"Bearer {token}"},
    params={"page_size": 20},
)
print("云空间文件列表：")
print(f"Status: {r2.status_code}")
data = r2.json()
print(json.dumps(data, indent=2, ensure_ascii=False)[:1500])

print("\n" + "=" * 50)
print(f"当前 App ID: {app_id}")
print("请确认：这个 App ID 对应的应用名称是不是「新石器反馈闭环数据接入助手」？")
print("如果不确定，去 open.feishu.cn → 开发者后台 → 点进应用 → 凭证与基础信息 → 看 App ID")