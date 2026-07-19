# -*- coding: utf-8 -*-
"""调试图片插入正确流程：先创建空图片block，再上传图片"""

import io
import os
import sys
import requests

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "report"))

from charts import generate_category_pie


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

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # 1. 创建测试文档
    print("📄 创建测试文档...")
    resp = requests.post(
        "https://open.feishu.cn/open-apis/docx/v1/documents",
        headers=headers,
        json={"title": "图片插入测试-正确流程"},
        timeout=30,
    )
    doc_id = resp.json()["data"]["document"]["document_id"]
    print(f"✅ 文档：{doc_id}")

    # 2. 生成测试图片
    img_bytes = generate_category_pie(["体验", "运营", "安全"], [5, 3, 2], "测试饼图")
    print(f"🖼️  图片生成成功，大小：{len(img_bytes)} 字节")

    # 3. 第一步：创建空图片 block
    print("\n📌 步骤1：创建空图片 block...")
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children"
    resp = requests.post(
        url,
        headers=headers,
        json={
            "children": [
                {
                    "block_type": 27,
                    "image": {},
                }
            ],
            "index": 0,
        },
        timeout=30,
    )
    result = resp.json()
    print(f"结果：code={result.get('code')}, msg={result.get('msg')}")
    if result.get("code") != 0:
        print(f"   完整响应：{result}")
        return

    children = result.get("data", {}).get("children", [])
    if not children:
        print("❌ 未获取到图片 block_id")
        return

    image_block_id = children[0]["block_id"]
    print(f"✅ 图片 block_id: {image_block_id}")

    # 4. 第二步：上传图片到这个图片 block
    print("\n📌 步骤2：上传图片到图片 block...")
    upload_url = "https://open.feishu.cn/open-apis/drive/v1/medias/upload_all"
    upload_headers = {"Authorization": f"Bearer {token}"}
    upload_data = {
        "file_name": "test_pie.png",
        "parent_type": "docx_image",
        "parent_node": image_block_id,  # 关键：传图片 block 的 id，不是 doc_id
        "size": len(img_bytes),
    }
    upload_files = {"file": ("test_pie.png", io.BytesIO(img_bytes), "image/png")}

    resp = requests.post(
        upload_url,
        headers=upload_headers,
        data=upload_data,
        files=upload_files,
        timeout=30,
    )
    result = resp.json()
    print(f"结果：code={result.get('code')}, msg={result.get('msg')}")
    if result.get("code") != 0:
        print(f"   完整响应：{result}")
        return

    file_token = result.get("data", {}).get("file_token")
    print(f"✅ 上传成功，file_token: {file_token}")

    # 5. 第三步（可选）：PATCH 更新图片 block 确认关联
    # 有些文档说需要这一步，有些说不需要。我们试试
    print("\n📌 步骤3：PATCH 更新图片 block（可选）...")
    patch_url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{image_block_id}"
    resp = requests.patch(
        patch_url,
        headers=headers,
        json={
            "replace_image": {
                "token": file_token,
            }
        },
        timeout=30,
    )
    result = resp.json()
    print(f"结果：code={result.get('code')}, msg={result.get('msg')}")
    if result.get("code") != 0:
        print(f"   完整响应：{result}")
        print("   （这一步可能不需要，继续看效果）")

    print(f"\n📄 文档链接：https://acnacq48u535.feishu.cn/docx/{doc_id}")
    print("请打开看看图片是否能正常显示")


if __name__ == "__main__":
    main()
