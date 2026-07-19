import json
import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
RECORDS = [
    {
        "channel": "scan_qr",
        "user_tier": "收件人",
        "vehicle_id": "NX-TEST-101",
        "city": "北京",
        "content_raw": "用户反馈：车辆在校园东门斑马线附近突然急停，后方骑行学生差点追尾，担心存在行人安全风险，请立即排查感知识别和刹停策略。",
        "status": "待处理",
        "contact_name": "测试用户A",
        "contact_phone": "13800000001",
        "contact_allowed": "是",
    },
    {
        "channel": "hotline",
        "user_tier": "RaaS商户",
        "vehicle_id": "NX-TEST-102",
        "city": "上海",
        "content_raw": "商户反馈：无人车原定 18:30 到达，但实际晚到 25 分钟，导致晚高峰订单积压，希望能提前预警并优化调度。",
        "status": "待处理",
        "contact_name": "测试用户B",
        "contact_phone": "13800000002",
        "contact_allowed": "是",
    },
    {
        "channel": "wechat_group",
        "user_tier": "收件人",
        "vehicle_id": "NX-TEST-103",
        "city": "广州",
        "content_raw": "用户反馈：到达取货点后不知道如何打开货舱，车身屏幕提示不明显，建议增加更清晰的取货步骤引导。",
        "status": "待处理",
        "contact_name": "测试用户C",
        "contact_phone": "13800000003",
        "contact_allowed": "是",
    },
    {
        "channel": "telemetry",
        "user_tier": "快递员",
        "vehicle_id": "NX-TEST-104",
        "city": "深圳",
        "content_raw": "车端告警：车辆连续 3 次上报定位漂移，路线偏离预设配送路径，建议运维人员检查定位模块和地图匹配状态。",
        "status": "待处理",
        "contact_name": "测试用户D",
        "contact_phone": "13800000004",
        "contact_allowed": "否",
    },
    {
        "channel": "didi_review",
        "user_tier": "收件人",
        "vehicle_id": "NX-TEST-105",
        "city": "杭州",
        "content_raw": "用户评价：配送整体顺利，但客服电话等待时间较长，问题解决前重复转接了两次，希望提升客服响应效率。",
        "status": "待处理",
        "contact_name": "测试用户E",
        "contact_phone": "13800000005",
        "contact_allowed": "是",
    },
]
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
    records_url: str,
    tenant_access_token: str,
    fields: dict[str, str],
    index: int,
) -> dict[str, Any] | None:
    try:
        response = requests.post(
            records_url,
            headers={
                "Authorization": f"Bearer {tenant_access_token}",
                "Content-Type": "application/json",
            },
            json={"fields": fields},
            timeout=10,
        )
    except requests.RequestException as exc:
        print("写入失败")
        print(f"失败发生在哪条：第 {index} 条")
        print("飞书返回 code：无")
        print("飞书返回 msg：请求失败，未取得飞书响应")
        print(f"原因：请求新增多维表格记录接口失败：{exc}")
        print("请检查 app_token、table_id、字段名称、字段类型和应用权限。")
        return None

    try:
        result = response.json()
    except ValueError:
        print("写入失败")
        print(f"失败发生在哪条：第 {index} 条")
        print("飞书返回 code：无")
        print("飞书返回 msg：响应不是合法 JSON")
        print("原因：新增记录接口返回内容不是合法 JSON。")
        print(f"HTTP 状态码：{response.status_code}")
        return None

    if result.get("code") != 0:
        print("写入失败")
        print(f"失败发生在哪条：第 {index} 条")
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

    records_url = (
        f"https://open.feishu.cn/open-apis/bitable/v1/apps/{env['BITABLE_APP_TOKEN']}"
        f"/tables/{env['BITABLE_TABLE_ID']}/records"
    )

    if len(RECORDS) != 5:
        print("写入失败")
        print("原因：脚本配置的测试数据不是 5 条，请先检查 RECORDS。")
        return

    print(f"本次计划写入 {len(RECORDS)} 条")
    success_count = 0
    for index, fields in enumerate(RECORDS, start=1):
        result = create_one_record(records_url, tenant_access_token, fields, index)
        if result is None:
            print(f"vehicle_id：{fields['vehicle_id']}")
            print(f"最终成功数量：{success_count}")
            return

        record_id = result.get("data", {}).get("record", {}).get("record_id")
        success_count += 1
        print(f"第 {index} 条写入成功 | record_id={record_id} | vehicle_id={fields['vehicle_id']}")

    print(f"最终成功数量：{success_count}")


if __name__ == "__main__":
    main()
