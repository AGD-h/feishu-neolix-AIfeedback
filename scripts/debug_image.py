# -*- coding: utf-8 -*-
"""调试图片上传和插入"""

import io
import os
import sys
import requests

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "report"))

from charts import generate_category_pie, upload_image_to_feishu


def get_tenant_access_token():
    app_id = os.getenv("FEISHU_APP_ID", "")
    app_secret = os.getenv("FEISHU_APP_SECRET", "")
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": app_id, "app_secret": app_secret}, timeout=10)
    return resp.json().get("tenant_access_token")


def main():
    from dotenv import load_dotenv
    load_dotenv()

    token = get_tenant_access_token()
    if not token:
        print("❌ 获取 token 失败")
        return

    # 1. 先创建一个测试文档
    print("📄 创建测试文档...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    resp = requests.post(
        "https://open.feishu.cn/open-apis/docx/v1/documents",
        headers=headers,
        json={"title": "图片插入测试"},
        timeout=30,
    )
    result = resp.json()
    if result.get("code") != 0:
        print(f"❌ 创建文档失败：{result}")
        return
    doc_id = result["data"]["document"]["document_id"]
    print(f"✅ 文档创建成功：{doc_id}")

    # 2. 生成一张测试图片
    print("🖼️  生成测试图片...")
    img_bytes = generate_category_pie(["体验", "运营", "安全"], [5, 3, 2], "测试饼图")
    print(f"✅ 图片生成成功，大小：{len(img_bytes)} 字节")

    # 3. 上传图片
    print("⬆️  上传图片到飞书...")
    image_token = upload_image_to_feishu(img_bytes, "test_pie.png", doc_id, token)
    if not image_token:
        print("❌ 图片上传失败")
        return
    print(f"✅ 图片上传成功，image_token: {image_token}")

    # 4. 尝试用不同方式插入图片
    print("📌 插入图片（block_type=27, image_token）...")
    block_27 = {
        "block_type": 27,
        "image": {
            "image_token": image_token,
        },
    }
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children"
    resp = requests.post(
        url,
        headers=headers,
        json={"children": [block_27], "index": 0},
        timeout=30,
    )
    result = resp.json()
    print(f"结果：code={result.get('code')}, msg={result.get('msg')}")
    if result.get("code") != 0:
        print(f"   完整响应：{result}")

    # 5. 也试试 block_type=16（图片）
    print("\n📌 尝试 block_type=16...")
    block_16 = {
        "block_type": 16,
        "image": {
            "token": image_token,
        },
    }
    resp = requests.post(
        url,
        headers=headers,
        json={"children": [block_16], "index": 1},
        timeout=30,
    )
    result = resp.json()
    print(f"结果：code={result.get('code')}, msg={result.get('msg')}")
    if result.get("code") != 0:
        print(f"   完整响应：{result}")

    print(f"\n📄 文档链接：https://acnacq48u535.feishu.cn/docx/{doc_id}")


if __name__ == "__main__":
    main()
