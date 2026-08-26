# -*- coding: utf-8 -*-
"""
Step1 探测：用 GET /bitable/v1/apps/:app_token/tables/:table_id/fields
拉取多维表格所有字段的完整定义（特别是 category / priority / content_summary），
看字段属性里有没有 ai_prompt / ai_config / formula 之类能写入AI提示词的字段。
"""
import os
import sys
import json
import requests
from pathlib import Path

# 把项目根目录加到 sys.path，方便 import .env 加载逻辑
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

# 复用 verify_bitable_sync.py 里的 load_env / get_tenant_access_token 代码
from dotenv import load_dotenv

def load_env():
    env_path = _PROJECT_ROOT / ".env"
    if not env_path.is_file():
        print(f"❌ 找不到 .env：{env_path}")
        return None
    load_dotenv(dotenv_path=str(env_path), override=False)
    keys = ["FEISHU_APP_ID", "FEISHU_APP_SECRET", "BITABLE_APP_TOKEN", "BITABLE_TABLE_ID"]
    cfg = {k: os.getenv(k, "").strip() for k in keys}
    for k, v in cfg.items():
        if not v:
            print(f"❌ .env 里 {k} 为空")
            return None
    print(f"✅ 加载 .env 成功：{env_path}")
    return cfg

TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"

def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    try:
        r = requests.post(TOKEN_URL, json={"app_id": app_id, "app_secret": app_secret}, timeout=15)
    except Exception as e:
        print(f"❌ 获取 tenant token 网络异常：{e}")
        return ""
    if r.status_code != 200:
        print(f"❌ 获取 tenant token HTTP {r.status_code}：{r.text[:300]}")
        return ""
    data = r.json()
    if data.get("code") != 0:
        print(f"❌ 获取 tenant token API {data.get('code')}：{data.get('msg')}")
        return ""
    return data.get("tenant_access_token", "")


def main():
    cfg = load_env()
    if not cfg:
        return 2
    token = get_tenant_access_token(cfg["FEISHU_APP_ID"], cfg["FEISHU_APP_SECRET"])
    if not token:
        return 3

    app_token = cfg["BITABLE_APP_TOKEN"]
    table_id = cfg["BITABLE_TABLE_ID"]

    # 分页拉取全部字段
    BITABLE_FIELDS_URL = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
    all_fields = []
    page_token = ""
    headers = {"Authorization": f"Bearer {token}"}
    while True:
        params = {"page_size": 100}
        if page_token:
            params["page_token"] = page_token
        r = requests.get(BITABLE_FIELDS_URL, headers=headers, params=params, timeout=20)
        if r.status_code != 200:
            print(f"❌ GET fields HTTP {r.status_code}：{r.text[:500]}")
            return 4
        data = r.json()
        if data.get("code") != 0:
            print(f"❌ GET fields API {data.get('code')}：{data.get('msg')}")
            return 5
        items = (data.get("data") or {}).get("items") or []
        all_fields.extend(items)
        has_more = (data.get("data") or {}).get("has_more")
        page_token = (data.get("data") or {}).get("page_token", "")
        if not has_more or not page_token:
            break

    print(f"\n📚 共拉到 {len(all_fields)} 个字段。以下是每个字段的**完整 JSON**（重点查找 ai_config / prompt / ai_ 开头属性）：\n")
    print("=" * 100)

    TARGET_NAMES = {"category", "priority", "content_summary", "user_tier"}

    for idx, f in enumerate(all_fields, 1):
        field_name = str(f.get("field_name", ""))
        is_target = field_name in TARGET_NAMES
        marker = "⭐⭐⭐ " if is_target else "  "
        print(f"\n{marker}[{idx}] 字段名 =【{field_name}】，field_id={f.get('field_id','')}，type={f.get('type','')}")
        if is_target:
            # 目标字段，打印完整 JSON（缩进），找出 AI 相关属性
            pretty = json.dumps(f, ensure_ascii=False, indent=2)
            print(f"  ── 完整属性 JSON ──\n{pretty}")
            # 高亮 ai 开头的 key
            ai_keys = [k for k in f.keys() if "ai" in k.lower() or "prompt" in k.lower() or "formula" in k.lower()]
            if ai_keys:
                print(f"  🎯 找到 AI/Prompt/Formula 相关 keys：{ai_keys}")
            else:
                print(f"  ⚠️  没有直接找到 ai_* / prompt / formula 属性，可能藏在 property / ui_property 里？")
        else:
            # 非目标字段，只打印 keys（快速扫一眼有没有 ai_* 全局属性）
            print(f"     keys = {sorted(f.keys())}")

    print("\n" + "=" * 100)
    # 再扫一遍所有字段的所有 key，汇总 unique key
    all_keys = set()
    for f in all_fields:
        all_keys.update(f.keys())
    print(f"\n🔎 所有字段出现过的 top-level key 汇总：{sorted(all_keys)}")

    # 扫 property 里的 key
    inner_keys = set()
    for f in all_fields:
        if isinstance(f.get("property"), dict):
            inner_keys.update(f["property"].keys())
    print(f"🔎 所有字段 property.* 里出现过的 key 汇总：{sorted(inner_keys)}")

    # 扫 ui_property（飞书UI端配置）
    ui_keys = set()
    for f in all_fields:
        if isinstance(f.get("ui_property"), dict):
            ui_keys.update(f["ui_property"].keys())
    if ui_keys:
        print(f"🔎 所有字段 ui_property.* 里出现过的 key：{sorted(ui_keys)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
