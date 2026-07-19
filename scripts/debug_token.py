# -*- coding: utf-8 -*-
"""尝试用多种方式验证 bitable app token 是否正确"""
import os, json
from pathlib import Path
import requests
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parents[1]
load_dotenv(project_root / ".env")

app_id = os.getenv("FEISHU_APP_ID")
app_secret = os.getenv("FEISHU_APP_SECRET")
bitable_token = os.getenv("BITABLE_APP_TOKEN")

r = requests.post(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    json={"app_id": app_id, "app_secret": app_secret},
)
token = r.json()["tenant_access_token"]

print(f"Token: OK")
print(f"Bitable App Token: {bitable_token}")
print()

# 方式 1：直接列子表
print("=" * 50)
print("方式 1：直接 GET /tables")
url1 = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{bitable_token}/tables"
r1 = requests.get(url1, headers={"Authorization": f"Bearer {token}"})
print(f"  code={r1.json().get('code')}, msg={r1.json().get('msg')}")

# 方式 2：获取多维表格元信息
print()
print("=" * 50)
print("方式 2：获取多维表格元信息")
url2 = f"https://open.feishu.cn/open-apis/drive/v1/files/{bitable_token}"
r2 = requests.get(url2, headers={"Authorization": f"Bearer {token}"})
print(f"  code={r2.json().get('code')}, msg={r2.json().get('msg')}")
if r2.json().get("code") == 0:
    print(json.dumps(r2.json().get("data", {}), indent=2, ensure_ascii=False)[:500])

# 方式 3：用 docx 接口试试（如果不是 bitable 而是文档）
print()
print("=" * 50)
print("方式 3：用 docx 接口检查（排除是文档的可能）")
url3 = f"https://open.feishu.cn/open-apis/docx/v1/documents/{bitable_token}"
r3 = requests.get(url3, headers={"Authorization": f"Bearer {token}"})
print(f"  code={r3.json().get('code')}, msg={r3.json().get('msg')}")

print()
print("=" * 50)
print("排查建议：")
print("1. 如果方式 2 返回 0（成功），说明 token 是对的但不是多维表格")
print("2. 如果方式 3 返回 0，说明这是一个 docx 文档，不是 bitable")
print("3. 如果都返回 NOTEXIST，说明 token 错了，或者应用真的没权限")
print("4. 让 2号 重新打开多维表格，从地址栏重新复制 /base/ 后面的 token")