import os
import json
from pathlib import Path

import requests
from dotenv import load_dotenv


def main():
    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env")

    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")

    print("=" * 60)
    print("飞书鉴权详细调试")
    print("=" * 60)
    
    # 打印当前配置
    print("\n【当前配置】")
    print(f"FEISHU_APP_ID: {app_id}")
    print(f"FEISHU_APP_ID 长度: {len(app_id) if app_id else 0} (标准应为 20)")
    print(f"FEISHU_APP_SECRET: {app_secret[:8]}***{app_secret[-4:]}") if app_secret else print("FEISHU_APP_SECRET: None")
    print(f"FEISHU_APP_SECRET 长度: {len(app_secret) if app_secret else 0} (标准应为 32)")
    
    # 验证格式
    print("\n【格式验证】")
    if app_id and app_id.startswith("cli_"):
        print("✓ App ID 格式正确（以 cli_ 开头）")
    else:
        print("✗ App ID 格式不正确（应以 cli_ 开头）")
    
    if app_id and len(app_id) == 20:
        print("✓ App ID 长度正确（20个字符）")
    else:
        print(f"✗ App ID 长度不正确，期望 20，实际 {len(app_id) if app_id else 0}")
    
    if app_secret and len(app_secret) == 32:
        print("✓ App Secret 长度正确（32个字符）")
    else:
        print(f"✗ App Secret 长度不正确，期望 32，实际 {len(app_secret) if app_secret else 0}")

    # 发送请求
    print("\n【发送请求】")
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": app_id,
        "app_secret": app_secret
    }
    
    print(f"请求 URL: {url}")
    print(f"请求方法: POST")
    print(f"请求体: {{'app_id': '{app_id}', 'app_secret': '{app_secret[:8]}***{app_secret[-4:]}'}}")
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        print(f"\n【响应信息】")
        print(f"HTTP 状态码: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        
        try:
            result = response.json()
            print(f"\n【响应 JSON】")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            code = result.get("code")
            msg = result.get("msg")
            
            print(f"\n【错误分析】")
            error_codes = {
                0: "成功",
                10003: "无效参数 - 检查App ID格式是否正确",
                10014: "App Secret无效 - 可能原因: 1)Secret错误 2)应用未发布 3)应用类型不支持",
                99991663: "应用未授权 - 需要配置权限",
                99991665: "Token过期",
                100011: "应用不存在或已删除",
            }
            
            if code in error_codes:
                print(f"错误码 {code}: {error_codes[code]}")
            else:
                print(f"未知错误码 {code}: {msg}")
                
            if code == 10014:
                print("\n【10014 错误排查建议】")
                print("1. 确认应用类型是『企业自建应用』")
                print("2. 确认应用已发布（状态显示『已启用』）")
                print("3. 在飞书开放平台重新生成并复制 App Secret")
                print("4. 确认 App ID 和 App Secret 来自同一个应用")
                
        except ValueError:
            print(f"\n【响应内容】")
            print(response.text[:500] if len(response.text) > 500 else response.text)
            
    except requests.RequestException as e:
        print(f"\n【请求失败】")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        print("\n【排查建议】")
        print("1. 检查网络连接是否正常")
        print("2. 检查是否需要代理配置")
        print("3. 尝试直接访问 https://open.feishu.cn")


if __name__ == "__main__":
    main()