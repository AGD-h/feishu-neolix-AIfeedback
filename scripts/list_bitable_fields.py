import os
from pathlib import Path

import requests
from dotenv import load_dotenv


TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
REQUIRED_RAW_FIELDS = [
    "channel",
    "user_tier",
    "vehicle_id",
    "city",
    "content_raw",
    "status",
    "contact_name",
    "contact_phone",
    "location_detail",
    "contact_allowed",
]
AUTO_FIELDS = [
    "feedback_id",
    "category",
    "priority",
    "content_summary",
    "created_at",
    "assigned_to",
    "closed_at",
    "csat_score",
]


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
        print("读取字段失败")
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
        response.raise_for_status()
    except requests.RequestException as exc:
        print("获取 tenant_access_token 失败")
        print(f"原因：请求飞书鉴权接口失败：{exc}")
        print("请检查网络连接、代理设置，或稍后重试。")
        return None

    try:
        result = response.json()
    except ValueError:
        print("获取 tenant_access_token 失败")
        print("原因：飞书鉴权接口返回内容不是合法 JSON。")
        print(f"HTTP 状态码：{response.status_code}")
        return None

    if result.get("code") != 0:
        print("获取 tenant_access_token 失败")
        print(f"飞书返回的 code：{result.get('code')}")
        print(f"飞书返回的 msg：{result.get('msg')}")
        return None

    token = result.get("tenant_access_token")
    if not token:
        print("获取 tenant_access_token 失败")
        print("原因：飞书返回成功，但响应中没有 tenant_access_token。")
        return None

    return token


def list_fields(app_token: str, table_id: str, tenant_access_token: str) -> list[dict] | None:
    fields_url = (
        f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}"
        f"/tables/{table_id}/fields"
    )

    try:
        response = requests.get(
            fields_url,
            headers={"Authorization": f"Bearer {tenant_access_token}"},
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        print("读取字段失败")
        print(f"原因：请求多维表格字段列表接口失败：{exc}")
        print("请检查 app_token、table_id、应用权限，或网络连接。")
        return None

    try:
        result = response.json()
    except ValueError:
        print("读取字段失败")
        print("原因：字段列表接口返回内容不是合法 JSON。")
        print(f"HTTP 状态码：{response.status_code}")
        return None

    if result.get("code") != 0:
        print("读取字段失败")
        print(f"飞书返回的 code：{result.get('code')}")
        print(f"飞书返回的 msg：{result.get('msg')}")
        return None

    return result.get("data", {}).get("items", [])


def print_fields(fields: list[dict]) -> None:
    print(f"读取字段成功，共 {len(fields)} 个字段：")
    for index, field in enumerate(fields, start=1):
        field_name = field.get("field_name", "")
        field_type = field.get("type", "")
        field_id = field.get("field_id", "")
        print(f"{index}. {field_name} | type={field_type} | field_id={field_id}")


def check_field_names(fields: list[dict]) -> None:
    existing_names = {field.get("field_name") for field in fields}

    for field_name in AUTO_FIELDS:
        if field_name not in existing_names:
            print(f"自动生成字段不存在：{field_name}")

    missing_raw_fields = [
        field_name for field_name in REQUIRED_RAW_FIELDS if field_name not in existing_names
    ]
    if missing_raw_fields:
        for field_name in missing_raw_fields:
            print(f"缺少字段：{field_name}")
        return

    print("原始写入字段检查通过。")


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

    fields = list_fields(
        env["BITABLE_APP_TOKEN"],
        env["BITABLE_TABLE_ID"],
        tenant_access_token,
    )
    if fields is None:
        return

    print_fields(fields)
    check_field_names(fields)


if __name__ == "__main__":
    main()
