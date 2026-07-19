import os
import requests
from pathlib import Path
from dotenv import load_dotenv

def test_auth(app_id, app_secret, label):
    """测试凭证是否有效"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": app_id,
        "app_secret": app_secret
    }
    
    print(f"\n{'='*60}")
    print(f"测试 {label}:")
    print(f"App ID: {app_id}")
    print(f"App Secret: {app_secret}")
    print(f"长度: {len(app_secret)}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") == 0:
            print("✅ 鉴权成功！")
            print(f"tenant_access_token: {data.get('tenant_access_token', '')[:20]}...")
            print(f"expire: {data.get('expire', '')}")
            return True
        else:
            print(f"❌ 鉴权失败")
            print(f"错误码: {data.get('code', '未知')}")
            print(f"错误信息: {data.get('msg', '未知')}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {str(e)}")
        return False

def main():
    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env")

    app_id = os.getenv("FEISHU_APP_ID")
    current_secret = os.getenv("FEISHU_APP_SECRET")
    
    print(f"当前配置的App ID: {app_id}")
    print(f"当前配置的App Secret: {current_secret}")
    print(f"当前长度: {len(current_secret)}")
    
    # 测试当前凭证（34位）
    test_auth(app_id, current_secret, "当前凭证 (34位)")
    
    # 测试去掉末尾2位的凭证（32位）
    secret_32 = current_secret[:32]
    test_auth(app_id, secret_32, "去掉末尾2位 (32位)")
    
    # 测试去掉开头2位的凭证（32位）
    secret_32_end = current_secret[2:]
    test_auth(app_id, secret_32_end, "去掉开头2位 (32位)")

if __name__ == "__main__":
    main()