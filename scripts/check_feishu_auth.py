import os
from pathlib import Path

import requests
from dotenv import load_dotenv


TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"


def mask_token(token: str) -> str:
    """只展示 token 的少量首尾字符，避免泄露完整凭证。"""
    if len(token) <= 12:
        return "***"
    return f"{token[:8]}***{token[-4:]}"


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env")

    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")

    missing_vars = []
    if not app_id:
        missing_vars.append("FEISHU_APP_ID")
    if not app_secret:
        missing_vars.append("FEISHU_APP_SECRET")

    if missing_vars:
        print("鉴权失败")
        print("原因：本地 .env 缺少以下变量：")
        for var_name in missing_vars:
            print(f"- {var_name}")
        print("请检查项目根目录的 .env 是否已填写对应值。")
        return

    try:
        response = requests.post(
            TOKEN_URL,
            json={
                "app_id": app_id,
                "app_secret": app_secret,
            },
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        print("鉴权失败")
        print(f"原因：请求飞书鉴权接口失败：{exc}")
        print("请检查网络连接、代理设置，或稍后重试。")
        return

    print(f"HTTP 状态码：{response.status_code}")
    print(f"响应头：{response.headers}")
    
    try:
        result = response.json()
        print(f"完整响应：{result}")
    except ValueError:
        print("鉴权失败")
        print("原因：飞书返回内容不是合法 JSON。")
        print(f"响应内容：{response.text}")
        return

    code = result.get("code")
    msg = result.get("msg")

    if code == 0:
        tenant_access_token = result.get("tenant_access_token", "")
        expire = result.get("expire")
        print("鉴权成功")
        print(f"token 有效期 expire：{expire}")
        print(f"tenant_access_token：{mask_token(tenant_access_token)}")
        return

    print("鉴权失败")
    print(f"飞书返回的 code：{code}")
    print(f"飞书返回的 msg：{msg}")
    print("\n可能的原因：")
    print("- App ID 或 App Secret 不正确")
    print("- 应用未正确发布")
    print("- 应用类型不支持 tenant_access_token 接口")
    print("- 需要在飞书开放平台配置权限")


if __name__ == "__main__":
    main()
