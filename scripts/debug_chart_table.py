# -*- coding: utf-8 -*-
"""调试：飞书文档图片上传 + 表格 block"""
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

# ============ 测试 1：创建测试文档 ============
print("\n--- 测试 1：创建测试文档 ---")
r1 = requests.post(
    "https://open.feishu.cn/open-apis/docx/v1/documents",
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    json={"title": "图表+表格调试测试"},
)
d1 = r1.json()
doc_id = d1["data"]["document"]["document_id"]
print(f"文档 ID: {doc_id}")

# ============ 测试 2：生成一张饼图并上传 ============
print("\n--- 测试 2：生成饼图并上传 ---")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 找中文字体
font_path = None
for f in fm.fontManager.ttflist:
    if "Microsoft YaHei" in f.name or "SimHei" in f.name or "Noto Sans CJK" in f.name:
        font_path = f.fname
        print(f"找到中文字体: {f.name} ({f.fname})")
        break

if font_path:
    plt.rcParams["font.family"] = fm.FontProperties(fname=font_path).get_name()
plt.rcParams["axes.unicode_minus"] = False

# 生成饼图
labels = ["体验类", "运营类", "安全类"]
sizes = [60, 30, 10]
colors = ["#FF6B6B", "#4ECDC4", "#45B7D1"]

fig, ax = plt.subplots(figsize=(6, 4))
ax.pie(sizes, labels=labels, autopct="%1.1f%%", colors=colors, startangle=90)
ax.set_title("问题分类分布")

chart_path = project_root / "report" / "output" / "test_pie.png"
chart_path.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(chart_path, dpi=150, bbox_inches="tight")
plt.close()
print(f"饼图已生成: {chart_path}")

# 上传图片到飞书
print("上传图片到飞书...")
upload_url = "https://open.feishu.cn/open-apis/drive/v1/medias/upload_all"
with open(chart_path, "rb") as f:
    files = {"file": ("test_pie.png", f, "image/png")}
    data = {"file_name": "test_pie.png", "parent_type": "docx_image", "parent_node": doc_id, "size": os.path.getsize(chart_path)}
    r2 = requests.post(
        upload_url,
        headers={"Authorization": f"Bearer {token}"},
        files=files,
        data=data,
    )

d2 = r2.json()
print(f"上传结果: code={d2.get('code')}, msg={d2.get('msg')}")
if d2.get("code") == 0:
    file_token = d2["data"]["file_token"]
    print(f"file_token: {file_token}")

    # 插入图片 block（测试多种结构）
    print("\n--- 测试 3：插入图片 block ---")
    img_tests = [
        ("type=26, token", {"block_type": 26, "image": {"token": file_token}}),
        ("type=26, image_token", {"block_type": 26, "image": {"image_token": file_token}}),
        ("type=27, token", {"block_type": 27, "image": {"token": file_token}}),
        ("type=27, image_token", {"block_type": 27, "image": {"image_token": file_token}}),
    ]

    for name, img_block in img_tests:
        r3 = requests.post(
            f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"children": [img_block], "index": 0},
        )
        d3 = r3.json()
        status = "✅" if d3.get("code") == 0 else "❌"
        print(f"  {status} {name}: code={d3.get('code')}, msg={d3.get('msg')[:50]}")
        if d3.get("code") == 0:
            break
else:
    print(json.dumps(d2, indent=2, ensure_ascii=False)[:800])
    print("图片上传失败，跳过图片测试")

# ============ 测试 4：测试表格 block ============
print("\n--- 测试 4：测试表格 block ---")

# 尝试几种不同的 table block 结构
test_tables = [
    # 方案 A: block_type 31, cells 为二维数组
    {
        "name": "方案A (cells二维数组)",
        "block": {
            "block_type": 31,
            "table": {
                "rows": 3,
                "columns": 3,
                "cells": [
                    [
                        {"text_style": {"elements": [{"text_run": {"content": "A1"}}]}},
                        {"text_style": {"elements": [{"text_run": {"content": "B1"}}]}},
                        {"text_style": {"elements": [{"text_run": {"content": "C1"}}]}},
                    ],
                    [
                        {"text_style": {"elements": [{"text_run": {"content": "A2"}}]}},
                        {"text_style": {"elements": [{"text_run": {"content": "B2"}}]}},
                        {"text_style": {"elements": [{"text_run": {"content": "C2"}}]}},
                    ],
                    [
                        {"text_style": {"elements": [{"text_run": {"content": "A3"}}]}},
                        {"text_style": {"elements": [{"text_run": {"content": "B3"}}]}},
                        {"text_style": {"elements": [{"text_run": {"content": "C3"}}]}},
                    ],
                ],
                "property": {
                    "row_size": 3,
                    "column_size": 3,
                },
            },
        },
    },
    # 方案 B: block_type 31, 没有 cells, 用 row_size/column_size 建空表
    {
        "name": "方案B (空表,无cells)",
        "block": {
            "block_type": 31,
            "table": {
                "rows": 3,
                "columns": 3,
                "property": {
                    "row_size": 3,
                    "column_size": 3,
                },
            },
        },
    },
]

for test in test_tables:
    print(f"\n测试: {test['name']}")
    r4 = requests.post(
        f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"children": [test["block"]], "index": 100},
    )
    d4 = r4.json()
    status = "✅" if d4.get("code") == 0 else "❌"
    print(f"  {status} code={d4.get('code')}, msg={d4.get('msg')[:80]}")
    if d4.get("code") != 0:
        viols = d4.get("error", {}).get("field_violations", [])
        if viols:
            for v in viols:
                print(f"    - {v.get('field')}: {v.get('description')}")
        else:
            print(f"    {json.dumps(d4, indent=2, ensure_ascii=False)[:300]}")

print(f"\n调试完成，文档链接: https://acnacq48u535.feishu.cn/docx/{doc_id}")
