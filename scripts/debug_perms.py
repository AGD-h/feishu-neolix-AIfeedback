# -*- coding: utf-8 -*-
"""检查自建应用的权限范围和状态"""
import os, json
from pathlib import Path
import requests
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parents[1]
load_dotenv(project_root / ".env")

app_id = os.getenv("FEISHU_APP_ID")
app_secret = os.getenv("FEISHU_APP_SECRET")

# 1. 获取 token
r = requests.post(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    json={"app_id": app_id, "app_secret": app_secret},
)
token = r.json()["tenant_access_token"]
print(f"✅ Token 获取成功")

# 2. 查看应用已授权的权限范围
url = f"https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal"
r2 = requests.post(url, json={"app_id": app_id, "app_secret": app_secret})
print(f"\napp_access_token 接口: code={r2.json().get('code')}, msg={r2.json().get('msg')}")

# 3. 尝试用 app_access_token 访问 bitable
app_token_resp = r2.json()
if app_token_resp.get("code") == 0:
    app_token = app_token_resp.get("app_access_token")
    bitable_token = os.getenv("BITABLE_APP_TOKEN")
    url3 = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{bitable_token}/tables"
    r3 = requests.get(url3, headers={"Authorization": f"Bearer {app_token}"})
    print(f"\n用 app_access_token 访问 bitable:")
    print(f"  Status: {r3.status_code}")
    print(f"  Body: {r3.text[:500]}")

# 4. 检查 scopes - 看看应用有哪些权限
print("\n" + "=" * 50)
print("关键检查清单（请确认 2号 已完成）：")
print("=" * 50)
print("1. open.feishu.cn 开发者后台 → 权限管理 → bitable:table:readonly 已开通且审批通过")
print("2. 多维表格 → 分享 → 已添加自建应用为协作者（可阅读）")
print("3. 多维表格 URL 中 /base/ 后面的 token 确实是 lotubQjiOavmzessY3fcEBRvnNh")