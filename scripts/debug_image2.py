# -*- coding: utf-8 -*-
"""调试图片插入多种方式测试"""

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


def upload_image_way1(image_bytes, file_name, doc_id, token):
    """方式1：docx_image + doc_id 作为 parent_node"""
    url = "https://open.feishu.cn/open-apis/drive/v1/medias/upload_all"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "file_name": file_name,
        "parent_type": "docx_image",
        "parent_node": doc_id,
        "size": len(image_bytes),
    }
    files = {"file": (file_name, io.BytesIO(image_bytes), "image/png")}
    resp = requests.post(url, headers=headers, data=data, files=files, timeout=30)
    result = resp.json()
    if result.get("code") == 0:
        return result.get("data", {}).get("file_token")
    print(f"  方式1上传失败：{result.get('msg')}")
    return None


def upload_image_way2(image_bytes, file_name, token):
    """方式2：explorer + 空 parent_node（上传到云盘根目录）"""
    url = "https://open.feishu.cn/open-apis/drive/v1/medias/upload_all"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "file_name": file_name,
        "parent_type": "explorer",
        "parent_node": "",
        "size": len(image_bytes),
    }
    files = {"file": (file_name, io.BytesIO(image_bytes), "image/png")}
    resp = requests.post(url, headers=headers, data=data, files=files, timeout=30)
    result = resp.json()
    if result.get("code") == 0:
        return result.get("data", {}).get("file_token")
    print(f"  方式2上传失败：{result.get('msg')}")
    return None


def insert_image(doc_id, block_id, token, image_token, way_name, block_type, image_field):
    """插入图片的通用方法"""
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{block_id}/children"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    block = {
        "block_type": block_type,
        "image": image_field,
    }
    resp = requests.post(url, headers=headers, json={"children": [block], "index": 0}, timeout=30)
    result = resp.json()
    status = "✅" if result.get("code") == 0 else "❌"
    print(f"  {status} {way_name}: code={result.get('code')}, msg={result.get('msg')}")
    return result.get("code") == 0


def main():
    from dotenv import load_dotenv
    load_dotenv()

    token = get_tenant_access_token()
    if not token:
        print("❌ 获取 token 失败")
        return

    # 创建测试文档
    print("📄 创建测试文档...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    resp = requests.post(
        "https://open.feishu.cn/open-apis/docx/v1/documents",
        headers=headers,
        json={"title": "图片插入测试-多种方式"},
        timeout=30,
    )
    doc_id = resp.json()["data"]["document"]["document_id"]
    print(f"✅ 文档：{doc_id}")

    # 生成测试图片
    img_bytes = generate_category_pie(["体验", "运营", "安全"], [5, 3, 2], "测试饼图")

    # 方式1上传
    print("\n📤 方式1上传 (docx_image + doc_id)...")
    token1 = upload_image_way1(img_bytes, "test1.png", doc_id, token)
    if token1:
        print(f"  ✅ 上传成功: {token1}")

    # 方式2上传
    print("\n📤 方式2上传 (explorer + 空)...")
    token2 = upload_image_way2(img_bytes, "test2.png", token)
    if token2:
        print(f"  ✅ 上传成功: {token2}")

    # 测试各种插入方式
    print("\n📌 测试插入方式：")

    # 测试1: block_type=27, image_token (方式1上传的)
    if token1:
        insert_image(doc_id, doc_id, token, token1,
                      "27+image_token(方式1上传)", 27, {"image_token": token1})

    # 测试2: block_type=27, token
    if token1:
        insert_image(doc_id, doc_id, token, token1,
                      "27+token(方式1上传)", 27, {"token": token1})

    # 测试3: block_type=27, image_token (方式2上传的)
    if token2:
        insert_image(doc_id, doc_id, token, token2,
                      "27+image_token(方式2上传)", 27, {"image_token": token2})

    # 测试4: block_type=27, token (方式2上传的)
    if token2:
        insert_image(doc_id, doc_id, token, token2,
                      "27+token(方式2上传)", 27, {"token": token2})

    print(f"\n📄 文档链接：https://acnacq48u535.feishu.cn/docx/{doc_id}")
    print("请打开文档看看哪张图片能正常显示")


if __name__ == "__main__":
    main()
