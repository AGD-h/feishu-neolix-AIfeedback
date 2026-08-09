# -*- coding: utf-8 -*-
"""
设置飞书文档完全开放权限
将文档设置为：互联网上获得链接的人可编辑、可评论、可复制
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# API配置
TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
PERMISSION_PUBLIC_URL = "https://open.feishu.cn/open-apis/drive/v1/permissions/{token}/public"

# 凭证
APP_ID = os.getenv("FEISHU_APP_ID")
APP_SECRET = os.getenv("FEISHU_APP_SECRET")

# 要设置权限的文档列表
DOCS_TO_UPDATE = [
    {
        "token": "FBeDdP2cpo9y8ZxWSUdcY8bxn4g",
        "type": "docx",
        "name": "教练沟通材料（飞书文档）"
    }
]


def get_token():
    """获取tenant_access_token"""
    resp = requests.post(TOKEN_URL, json={
        "app_id": APP_ID,
        "app_secret": APP_SECRET
    }, timeout=30)
    data = resp.json()
    if data.get("code") == 0:
        return data["tenant_access_token"]
    print(f"❌ 获取token失败: {data}")
    return None


def set_public_permission(token, doc_token, doc_type, doc_name):
    """设置文档为完全开放权限"""
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    url = PERMISSION_PUBLIC_URL.format(token=doc_token)
    params = {"type": doc_type}
    
    # 完全开放权限配置
    # external_access=true: 允许组织外访问
    # link_share_entity=anyone_editable: 获得链接的任何人可编辑
    # comment_entity=anyone_can_view: 任何人可评论
    # share_entity=anyone: 任何人可添加协作者
    # security_entity=anyone_can_view: 任何人可复制/打印/导出
    # invite_external=true: 允许邀请外部参与者
    permission_data = {
        "external_access": True,
        "link_share_entity": "anyone_editable",
        "comment_entity": "anyone_can_view",
        "share_entity": "anyone",
        "security_entity": "anyone_can_view",
        "invite_external": True
    }
    
    print(f"\n📄 正在设置文档: {doc_name}")
    print(f"   Token: {doc_token}")
    print(f"   权限配置: {permission_data}")
    
    resp = requests.patch(url, headers=headers, params=params, json=permission_data, timeout=30)
    result = resp.json()
    
    if result.get("code") == 0:
        print(f"✅ 权限设置成功！")
        data = result.get("data", {}).get("permission_public", {})
        print(f"   - 外部访问: {'✅ 开启' if data.get('external_access') else '❌ 关闭'}")
        print(f"   - 链接分享: {data.get('link_share_entity')}")
        print(f"   - 评论权限: {data.get('comment_entity')}")
        print(f"   - 协作者管理: {data.get('share_entity')}")
        print(f"   - 安全设置: {data.get('security_entity')}")
        return True
    else:
        print(f"❌ 权限设置失败: {result}")
        # 如果anyone_editable失败，尝试先设置tenant_editable
        if result.get("code") == 1063003:
            print("   企业可能限制了外部访问，尝试设置为组织内可编辑...")
            permission_data["external_access"] = False
            permission_data["link_share_entity"] = "tenant_editable"
            resp2 = requests.patch(url, headers=headers, params=params, json=permission_data, timeout=30)
            result2 = resp2.json()
            if result2.get("code") == 0:
                print(f"✅ 组织内可编辑权限设置成功！")
                return True
            else:
                print(f"❌ 组织内权限设置也失败: {result2}")
        return False


def main():
    print("=" * 60)
    print("🔓 设置飞书文档完全开放权限")
    print("=" * 60)
    
    if not APP_ID or not APP_SECRET:
        print("❌ 请在.env中配置FEISHU_APP_ID和FEISHU_APP_SECRET")
        return
    
    # 获取token
    print("\n🔑 获取访问令牌...")
    token = get_token()
    if not token:
        return
    print("✅ 获取成功")
    
    # 设置所有文档权限
    success_count = 0
    for doc in DOCS_TO_UPDATE:
        if set_public_permission(token, doc["token"], doc["type"], doc["name"]):
            success_count += 1
    
    # 总结
    print("\n" + "=" * 60)
    print(f"🎉 完成！成功设置 {success_count}/{len(DOCS_TO_UPDATE)} 个文档的权限")
    print("\n📋 已配置的文档链接：")
    for doc in DOCS_TO_UPDATE:
        if doc["type"] == "docx":
            url = f"https://acnacq48u535.feishu.cn/docx/{doc['token']}"
        elif doc["type"] == "bitable":
            url = f"https://acnacq48u535.feishu.cn/base/{doc['token']}"
        else:
            url = f"https://acnacq48u535.feishu.cn/{doc['type']}/{doc['token']}"
        print(f"   - {doc['name']}: {url}")
    print("=" * 60)
    print("\n💡 权限说明：")
    print("   - 互联网上获得链接的人：可查看、可编辑、可评论")
    print("   - 任何人：可复制、打印、导出内容")
    print("   - 任何人：可添加和管理协作者")
    print("   - 允许邀请外部参与者")


if __name__ == "__main__":
    main()
