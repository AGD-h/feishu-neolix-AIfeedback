# -*- coding: utf-8 -*-
"""
上传PPTX到飞书云盘并发送到飞书群
"""

import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 配置
TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
UPLOAD_URL = "https://open.feishu.cn/open-apis/drive/v1/files/upload_all"
SEND_MSG_URL = "https://open.feishu.cn/open-apis/im/v1/messages"

APP_ID = os.getenv("FEISHU_APP_ID")
APP_SECRET = os.getenv("FEISHU_APP_SECRET")
CHAT_ID = os.getenv("FEISHU_CHAT_ID")

PPTX_PATH = Path(__file__).parent.parent / "docs" / "教练沟通材料.pptx"


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


def upload_file(token, file_path):
    """上传文件到飞书云盘"""
    file_name = file_path.name
    file_size = file_path.stat().st_size
    
    print(f"📤 正在上传文件: {file_name} ({file_size} bytes)")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    with open(file_path, "rb") as f:
        files = {
            "file": (file_name, f, "application/vnd.openxmlformats-officedocument.presentationml.presentation")
        }
        data = {
            "file_name": file_name,
            "parent_type": "explorer",
            "parent_node": ""  # 上传到根目录
        }
        
        resp = requests.post(UPLOAD_URL, headers=headers, data=data, files=files, timeout=60)
    
    result = resp.json()
    
    if result.get("code") == 0:
        file_token = result["data"]["file_token"]
        print(f"✅ 文件上传成功！file_token: {file_token}")
        return result["data"]
    else:
        print(f"❌ 文件上传失败: {result}")
        return None


def send_file_message(token, chat_id, file_token, file_name):
    """发送文件消息到飞书群"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    params = {
        "receive_id_type": "chat_id"
    }
    
    # 发送文件消息
    content = {
        "file_key": file_token
    }
    
    data = {
        "receive_id": chat_id,
        "msg_type": "file",
        "content": json.dumps(content)
    }
    
    resp = requests.post(SEND_MSG_URL, headers=headers, params=params, json=data, timeout=30)
    result = resp.json()
    
    if result.get("code") == 0:
        print(f"✅ 文件消息发送成功！")
        return result["data"]
    else:
        print(f"❌ 文件消息发送失败: {result}")
        
        # 如果文件消息发送失败，尝试发送文本消息告诉用户
        text_content = {
            "text": f"""📊 教练沟通材料PPT已生成！

📄 文件名称：{file_name}
📁 本地路径：{PPTX_PATH.absolute()}

👉 快速获取飞书幻灯片链接（30秒搞定）：
1. 打开飞书云盘：https://acnacq48u535.feishu.cn/drive/
2. 上传本地的「教练沟通材料.pptx」文件
3. 右键点击文件 → 选择「导入为飞书幻灯片」
4. 转换完成后即可获得分享链接

📋 同时可使用的材料：
- 飞书文档（详细版）：https://acnacq48u535.feishu.cn/docx/FBeDdP2cpo9y8ZxWSUdcY8bxn4g
- HTML演示版（浏览器可直接打开翻页）"""
        }
        
        data2 = {
            "receive_id": chat_id,
            "msg_type": "text",
            "content": json.dumps(text_content)
        }
        
        resp2 = requests.post(SEND_MSG_URL, headers=headers, params=params, json=data2, timeout=30)
        result2 = resp2.json()
        if result2.get("code") == 0:
            print(f"✅ 已发送文本提示消息")
        return None


def main():
    print("=" * 60)
    print("🚀 上传PPTX到飞书并发送到群")
    print("=" * 60)
    
    if not PPTX_PATH.exists():
        print(f"❌ 文件不存在: {PPTX_PATH}")
        print("请先运行 python scripts/create_pptx.py 生成PPTX文件")
        return
    
    if not APP_ID or not APP_SECRET:
        print("❌ 请配置FEISHU_APP_ID和FEISHU_APP_SECRET")
        return
    
    # 获取token
    print("\n🔑 获取访问令牌...")
    token = get_token()
    if not token:
        return
    print("✅ 获取成功")
    
    # 上传文件
    print("\n📤 上传文件到飞书云盘...")
    file_data = upload_file(token, PPTX_PATH)
    
    if file_data and CHAT_ID:
        print("\n💬 发送文件到飞书群...")
        file_token = file_data["file_token"]
        send_file_message(token, CHAT_ID, file_token, PPTX_PATH.name)
    
    print("\n" + "=" * 60)
    print("📁 本地文件路径:", PPTX_PATH.absolute())
    print("=" * 60)


if __name__ == "__main__":
    main()
