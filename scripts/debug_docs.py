# -*- coding: utf-8 -*-
"""测试飞书云文档创建能力"""
import os, json
from pathlib import Path
import requests
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parents[1]
load_dotenv(project_root / ".env")

app_id = os.getenv("FEISHU_APP_ID")
app_secret = os.getenv("FEISHU_APP_SECRET")

r = requests.post(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    json={"app_id": app_id, "app_secret": app_secret},
)
token = r.json()["tenant_access_token"]
print(f"Token: OK")

# 方式 1：创建空白文档
print("\n--- 测试 1：创建空白文档 ---")
url1 = "https://open.feishu.cn/open-apis/docx/v1/documents"
body1 = {
    "title": "测试文档 - 周报上传测试",
    "folder_token": "",
}
r1 = requests.post(
    url1,
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    json=body1,
)
print(f"Status: {r1.status_code}")
data1 = r1.json()
print(f"code={data1.get('code')}, msg={data1.get('msg')}")
if data1.get("code") == 0:
    doc = data1.get("data", {}).get("document", {})
    doc_id = doc.get("document_id", "")
    doc_title = doc.get("title", "")
    print(f"文档创建成功！")
    print(f"  document_id: {doc_id}")
    print(f"  title: {doc_title}")
    print(f"  链接: https://acnacq48u535.feishu.cn/docx/{doc_id}")

    # 方式 2：往文档里写内容（测试一个简单的文本块）
    print("\n--- 测试 2：往文档里插入文本块 ---")
    url2 = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children"
    body2 = {
        "index": 0,
        "children": [
            {
                "block_type": 2,  # 文本
                "text": {
                    "elements": [
                        {
                            "text_run": {
                                "content": "这是一段测试文本，来自 Python 脚本。",
                                "text_element_style": {},
                            }
                        }
                    ],
                    "style": {},
                }
            }
        ]
    }
    r2 = requests.post(
        url2,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=body2,
    )
    print(f"Status: {r2.status_code}")
    data2 = r2.json()
    print(f"code={data2.get('code')}, msg={data2.get('msg')}")
    if data2.get("code") == 0:
        print("内容写入成功！")
    else:
        print(json.dumps(data2, indent=2, ensure_ascii=False)[:800])
else:
    print(json.dumps(data1, indent=2, ensure_ascii=False)[:800])