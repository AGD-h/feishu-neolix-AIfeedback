# -*- coding: utf-8 -*-
"""测试 descendant API 创建表格"""
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

# 创建测试文档
r1 = requests.post(
    "https://open.feishu.cn/open-apis/docx/v1/documents",
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    json={"title": "Descendant表格测试"},
)
doc_id = r1.json()["data"]["document"]["document_id"]
print(f"文档 ID: {doc_id}")

# 用 descendant API 创建 2x2 表格
print("\n--- 创建 2x2 表格 ---")

descendants = []
cell_ids = []
text_ids = []

for row in range(2):
    for col in range(2):
        cell_id = f"cell_{row}_{col}"
        text_id = f"text_{row}_{col}"
        cell_ids.append(cell_id)
        text_ids.append(text_id)

        # 单元格 block
        descendants.append({
            "block_id": cell_id,
            "block_type": 32,
            "table_cell": {},
            "children": [text_id],
        })

        # 单元格内的文本 block
        text_content = f"表头{row+1}-{col+1}" if row == 0 else f"数据{row+1}-{col+1}"
        is_bold = row == 0
        descendants.append({
            "block_id": text_id,
            "block_type": 2,
            "text": {
                "elements": [
                    {
                        "text_run": {
                            "content": text_content,
                            "text_element_style": {"bold": is_bold},
                        }
                    }
                ],
                "style": {},
            },
            "children": [],
        })

# 表格 block
table_block_id = "table_1"
descendants.append({
    "block_id": table_block_id,
    "block_type": 31,
    "table": {
        "property": {
            "row_size": 2,
            "column_size": 2,
        }
    },
    "children": cell_ids,
})

url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/descendant"
payload = {
    "index": 0,
    "children_id": [table_block_id],
    "descendants": descendants,
}

r2 = requests.post(
    url,
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    json=payload,
)
d2 = r2.json()
print(f"code={d2.get('code')}, msg={d2.get('msg')}")
if d2.get("code") != 0:
    print(json.dumps(d2, indent=2, ensure_ascii=False)[:1000])
else:
    print("✅ 表格创建成功!")

print(f"\n文档链接: https://acnacq48u535.feishu.cn/docx/{doc_id}")
