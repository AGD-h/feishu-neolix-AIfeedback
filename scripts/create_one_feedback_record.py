import json
import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
RECORD_FIELDS = {
    "channel": "车身扫码",
    "user_tier": "校园用户",
    "vehicle_id": "NX-TEST-001",
    "city": "北京",
    "content_raw": "测试反馈：车辆在校园东门斑马线附近急停，用户担心存在行人安全风险，请尽快排查车辆感知与刹停策略。",
    "status": "待处理",
    "contact_name": "测试用户",
    "contact_phone": "13800000000",
    "contact_allowed": "是",
}
SENSITIVE_KEYWORDS = ("secret", "token", "authorization")


def redact_sensitive_data(value: Any) -> Any:
    """递归脱敏响应内容，避免误把 token 或 secret 打印到终端。"""
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            if any(keyword in str(key).lower() for keyword in SENSITIVE_KEYWORDS):
                redacted[key] = "***"
            else:
                redacted[key] = redact_sensitive_data(item)
        return redacted

    if isinstance(value, list):
        return [redact_sensitive_data(item) for item in value]

    return value


def print_redacted_json(value: Any) -> None:
    redacted_value = redact_sensitive_data(value)
    print(json.dumps(redacted_value, ensure_ascii=False, indent=2))


def get_required_env() -> dict[str, str] | None:
    env_names = [
        "FEISHU_APP_ID",
        "FEISHU_APP_SECRET",
        "BITABLE_APP_TOKEN",
        "BITABLE_TABLE_ID",
    ]
    values = {name: os.getenv(name) for name in env_names}
    missing_vars = [name for name, value in values.items() if not value]

    if missing_vars:
        print("写入失败")
        print("原因：本地 .env 缺少以下变量：")
        for var_name in missing_vars:
            print(f"- {var_name}")
        print("请检查项目根目录的 .env 是否已填写对应值。")
        return None

    return {name: value for name, value in values.items() if value}


def get_tenant_access_token(app_id: str, app_secret: str) -> str | None:
    try:
        response = requests.post(
            TOKEN_URL,
            json={
                "app_id": app_id,
                "app_secret": app_secret,
            },
            timeout=10,
        )
    except requests.RequestException as exc:
        print("写入失败")
        print(f"原因：请求飞书鉴权接口失败：{exc}")
        print("请检查网络连接、代理设置，或稍后重试。")
        return None

    try:
        result = response.json()
    except ValueError:
        print("写入失败")
        print("原因：飞书鉴权接口返回内容不是合法 JSON。")
        print(f"HTTP 状态码：{response.status_code}")
        return None

    if result.get("code") != 0:
        print("写入失败")
        print(f"飞书返回 code：{result.get('code')}")
        print(f"飞书返回 msg：{result.get('msg')}")
        print("脱敏后的响应 JSON：")
        print_redacted_json(result)
        return None

    tenant_access_token = result.get("tenant_access_token")
    if not tenant_access_token:
        print("写入失败")
        print("原因：飞书返回成功，但响应中没有 tenant_access_token。")
        print("脱敏后的响应 JSON：")
        print_redacted_json(result)
        return None

    return tenant_access_token


def create_one_record(
    app_token: str,
    table_id: str,
    tenant_access_token: str,
) -> dict[str, Any] | None:
    records_url = (
        f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}"
        f"/tables/{table_id}/records"
    )

    try:
        response = requests.post(
            records_url,
            headers={
                "Authorization": f"Bearer {tenant_access_token}",
                "Content-Type": "application/json",
            },
            json={"fields": RECORD_FIELDS},
            timeout=10,
        )
    except requests.RequestException as exc:
        print("写入失败")
        print(f"原因：请求新增多维表格记录接口失败：{exc}")
        print("请检查 app_token、table_id、字段名称、字段类型和应用权限。")
        return None

    try:
        result = response.json()
    except ValueError:
        print("写入失败")
        print("原因：新增记录接口返回内容不是合法 JSON。")
        print(f"HTTP 状态码：{response.status_code}")
        return None

    if result.get("code") != 0:
        print("写入失败")
        print(f"飞书返回 code：{result.get('code')}")
        print(f"飞书返回 msg：{result.get('msg')}")
        print("脱敏后的响应 JSON：")
        print_redacted_json(result)
        return None

    return result


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env")

    env = get_required_env()
    if env is None:
        return

    tenant_access_token = get_tenant_access_token(
        env["FEISHU_APP_ID"],
        env["FEISHU_APP_SECRET"],
    )
    if tenant_access_token is None:
        return

    result = create_one_record(
        env["BITABLE_APP_TOKEN"],
        env["BITABLE_TABLE_ID"],
        tenant_access_token,
    )
    if result is None:
        return

    record_id = result.get("data", {}).get("record", {}).get("record_id")
    print("写入成功")
    print(f"record_id：{record_id}")
    print("本次写入的字段名列表：")
    for field_name in RECORD_FIELDS:
        print(f"- {field_name}")


if __name__ == "__main__":
    main()
