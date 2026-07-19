# -*- coding: utf-8 -*-
"""逐个测试 block 类型，找出校验失败的那个"""
import os, json, sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "report"))

import requests
from dotenv import load_dotenv
from md_to_feishu import markdown_to_feishu_blocks

load_dotenv(project_root / ".env")

app_id = os.getenv("FEISHU_APP_ID")
app_secret = os.getenv("FEISHU_APP_SECRET")

r = requests.post(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    json={"app_id": app_id, "app_secret": app_secret},
)
token = r.json()["tenant_access_token"]

# 读取周报内容
report_path = project_root / "report" / "output" / "weekly_report_20260717.md"
if not report_path.exists():
    print("报告文件不存在，先生成")
    sys.exit(1)

with open(report_path, "r", encoding="utf-8") as f:
    md_content = f.read()

blocks = markdown_to_feishu_blocks(md_content)
print(f"共生成 {len(blocks)} 个 blocks")

# 过滤掉嵌套列表（之前 append/extend 的问题）
flat_blocks = []
for b in blocks:
    if isinstance(b, list):
        flat_blocks.extend(b)
    else:
        flat_blocks.append(b)

print(f"展平后 {len(flat_blocks)} 个 blocks")

# 打印每种 block_type 的数量
from collections import Counter
type_counts = Counter(b.get("block_type") for b in flat_blocks)
print(f"\nBlock 类型分布：")
for bt, cnt in sorted(type_counts.items()):
    print(f"  block_type {bt}: {cnt} 个")

# 创建测试文档
print("\n--- 创建测试文档 ---")
r1 = requests.post(
    "https://open.feishu.cn/open-apis/docx/v1/documents",
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    json={"title": "Block 调试测试"},
)
data1 = r1.json()
if data1.get("code") != 0:
    print(f"创建文档失败: {data1}")
    sys.exit(1)

doc_id = data1["data"]["document"]["document_id"]
print(f"文档 ID: {doc_id}")

# 逐个发送 block，找到第一个失败的
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children"

for idx, block in enumerate(flat_blocks):
    bt = block.get("block_type")
    r2 = requests.post(
        url,
        headers=headers,
        json={"children": [block], "index": idx},
        timeout=30,
    )
    result = r2.json()
    if result.get("code") != 0:
        block_json = json.dumps(block, indent=2, ensure_ascii=False)
        print(f"\n❌ 第 {idx} 个 block 失败！block_type={bt}")
        print(f"   错误: code={result.get('code')}, msg={result.get('msg')}")
        print(f"   Block 内容:\n{block_json[:500]}")
    else:
        print(f"  ✅ [{idx}] block_type={bt} OK")

print("\n调试完成")