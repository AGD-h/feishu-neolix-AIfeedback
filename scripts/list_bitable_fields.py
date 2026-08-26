# -*- coding: utf-8 -*-
"""
查询飞书多维表格的「全部字段定义」——列名（就是API要写入用的key）、字段类型、字段ID
—— 用来修复 convert_to_bitable_format 的英文 key → 真实中文列名映射
"""
import os
import sys
from os.path import dirname, join, normpath

_PROJECT_ROOT = normpath(join(dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import requests
from dotenv import load_dotenv


def main() -> None:
    # 找 .env
    candidates = [
        normpath(join(_PROJECT_ROOT, ".env")),
        normpath(join(os.getcwd(), ".env")),
    ]
    for p in candidates:
        if os.path.isfile(p):
            load_dotenv(p, override=False)
            print(f"✅ 加载 .env：{p}")
            break
    else:
        print("❌ 没找到 .env")
        sys.exit(1)

    app_id = os.environ.get("FEISHU_APP_ID", "")
    app_secret = os.environ.get("FEISHU_APP_SECRET", "")
    app_token = os.environ.get("BITABLE_APP_TOKEN", "")
    table_id = os.environ.get("BITABLE_TABLE_ID", "")
    missing = [k for k in ("FEISHU_APP_ID", "FEISHU_APP_SECRET", "BITABLE_APP_TOKEN", "BITABLE_TABLE_ID")
               if not os.environ.get(k)]
    if missing:
        print(f"❌ 缺少变量：{missing}")
        sys.exit(2)

    # get token
    r = requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": app_id, "app_secret": app_secret},
        timeout=15,
    )
    data = r.json()
    if data.get("code") != 0:
        print(f"❌ token失败：{data.get('msg')}")
        sys.exit(3)
    token = data["tenant_access_token"]
    print(f"🔑 token 获取 OK（长度 {len(token)}）")

    # list fields（分页，最多 200 列够了）
    url = (
        f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}"
        f"/tables/{table_id}/fields?page_size=200"
    )
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers, timeout=30)
    data = r.json()
    if data.get("code") != 0:
        print(f"❌ 拉字段失败：HTTP {r.status_code} body={r.text[:500]}")
        sys.exit(4)

    fields = data.get("data", {}).get("items", []) or []
    has_more = data.get("data", {}).get("has_more", False)
    page_token = data.get("data", {}).get("page_token", "")
    while has_more:
        r2 = requests.get(url + f"&page_token={page_token}", headers=headers, timeout=30)
        d2 = r2.json()
        if d2.get("code") != 0:
            break
        fields.extend(d2.get("data", {}).get("items", []) or [])
        has_more = d2.get("data", {}).get("has_more", False)
        page_token = d2.get("data", {}).get("page_token", "")

    print()
    print("=" * 100)
    print(f"📋 飞书多维表格字段列表（共 {len(fields)} 列）")
    print(f"   APP={app_token}  TABLE={table_id}")
    print("=" * 100)
    print(
        f"{'序号':<4}{'字段名（★API写入用这个作key！）':<30}"
        f"{'类型':<16}{'field_id':<24}"
    )
    print("-" * 100)
    for i, f in enumerate(fields, 1):
        name = f.get("field_name", "")
        typ = f.get("type", "")
        fid = f.get("field_id", "")
        print(f"{i:<4}{name:<30}{typ:<16}{fid:<24}")
    print("=" * 100)
    print()
    print("💡 请把上面的「字段名列」复制给我，我会把它映射到 18 个 Schema 英文字段，然后修复导入脚本。")


if __name__ == "__main__":
    main()
