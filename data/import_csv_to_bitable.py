# -*- coding: utf-8 -*-
"""
CSV 数据导入飞书多维表格（1号数据线辅助工具）

功能：
  1. 读取本地 CSV 文件（data/output/mock_feedback.csv）
  2. 将日期字段转换为飞书多维表格格式（毫秒时间戳）
  3. 批量上传到飞书多维表格

运行方式：
  python data/import_csv_to_bitable.py

依赖：需要在 .env 中配置飞书凭证
"""

import csv
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

# ============================================================
# ★ 工单 Schema 常量：统一从根目录 schema_constants.py 引用
# ============================================================
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.normpath(os.path.join(_SCRIPT_DIR, ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
from schema_constants import (
    WORKORDER_SCHEMA_FIELDS,    # 18 字段顺序，导入 CSV 时做列名校验
    validate_contact_allowed,   # 统一收敛 contact_allowed 到合法三态，防止飞书单选报错
    # ===== 双语映射（Schema 内部枚举 → 飞书UI配置的中文选项文本）=====
    # 解决：写入英文枚举但飞书UI只配中文选项时，落到「无匹配类别」兜底的召回率问题
    to_bitable_channel,    # 7 英文枚举 → 7 中文（如 social_media → 社媒舆情）
    to_bitable_user_tier,  # 6 中文枚举 → 同值恒等（接口统一，未来可扩展）
    to_bitable_category,   # 5 中文枚举 → 同值恒等
    to_bitable_priority,   # P0~P3 英文 → 同值恒等
    to_bitable_status,     # 4 中文枚举 → 同值恒等
    # ===== P1 新增：路由分派规则 =====
    route_assignee_env_key,  # 按 category/priority/city 匹配 → 返回 .env变量名
    describe_route_rules,    # 人类可读规则清单（答辩演示打印用）
)

# 常量配置
BATCH_SIZE = 50  # 每次批量创建的记录数
MAX_RETRIES = 3  # 重试次数
RETRY_DELAY = 5  # 重试间隔（秒）
TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
BITABLE_BATCH_CREATE_URL = "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"
BITABLE_RECORDS_URL = "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
CSV_PATH = os.path.join(os.path.dirname(__file__), "output", "mock_feedback.csv")


def load_env() -> Optional[Dict[str, str]]:
    """读取 .env 配置（兼容从任意子目录启动的场景：自动向上定位项目根目录的 .env）"""
    # 当前脚本在 data/ 目录下，根目录 .env 在 ../.env
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidate_paths = [
        os.path.join(script_dir, "..", ".env"),    # 从 data/ 启动 → 上一级
        os.path.join(script_dir, ".env"),          # 根目录直接放
        os.path.join(os.getcwd(), ".env"),         # 当前工作目录
    ]
    loaded = False
    for p in candidate_paths:
        norm = os.path.normpath(p)
        if os.path.exists(norm):
            load_dotenv(norm)
            loaded = True
            print(f"✅ 已加载环境变量: {norm}")
            break
    if not loaded:
        print("⚠️ 未在以下位置找到 .env 文件（已检查）:")
        for p in candidate_paths:
            print(f"  - {os.path.normpath(p)}")

    env_names = ["FEISHU_APP_ID", "FEISHU_APP_SECRET", "BITABLE_APP_TOKEN", "BITABLE_TABLE_ID"]
    values = {name: os.getenv(name) for name in env_names}
    missing_vars = [name for name, value in values.items() if not value]
    
    if missing_vars:
        print("❌ 配置检查失败")
        print("原因：以下环境变量缺失（请检查 .env 或系统环境变量）:")
        for var_name in missing_vars:
            print(f"  - {var_name}")
        return None
    
    return values


def get_tenant_access_token(app_id: str, app_secret: str) -> Optional[str]:
    """获取飞书 tenant_access_token"""
    try:
        response = requests.post(
            TOKEN_URL,
            json={"app_id": app_id, "app_secret": app_secret},
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"❌ 获取 tenant_access_token 失败：{exc}")
        return None
    
    result = response.json()
    if result.get("code") != 0:
        print(f"❌ 飞书返回错误：code={result.get('code')}, msg={result.get('msg')}")
        return None
    
    return result.get("tenant_access_token")


def format_datetime(dt_str: str) -> Optional[int]:
    """将日期字符串转换为飞书多维表格格式（毫秒时间戳）"""
    if not dt_str:
        return None
    
    formats = ["%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(dt_str, fmt)
            return int(dt.timestamp() * 1000)
        except ValueError:
            continue
    
    print(f"⚠️ 日期格式解析失败：{dt_str}")
    return None


def read_csv(file_path: str) -> List[Dict[str, Any]]:
    """读取 CSV 文件"""
    records = []
    
    with open(file_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    
    print(f"✅ 从 CSV 读取到 {len(records)} 条记录")
    return records


def convert_to_bitable_format(csv_records: List[Dict[str, Any]],
                              open_id_lookup: Optional[Dict[str, str]] = None
                              ) -> List[Dict[str, Any]]:
    """将 CSV 记录转换为飞书多维表格格式（严格按 18 字段 Schema + 飞书字段真实类型适配）

    Args:
        csv_records: 从 CSV 读出来的原始工单列表
        open_id_lookup: 路由分派 open_id 映射表，key=env变量名（如ROUTE_SAFETY_P0_OPEN_ID），
                        value=真实 ou_xxx / on_xxx。None 或 env 值为空 → 不写 assigned_to。
    """
    bitable_records = []
    if open_id_lookup is None:
        open_id_lookup = {}
    # 统计路由分派命中情况（仅用于答辩演示打印）
    route_hit_counter: Dict[str, int] = {}      # 规则命中数（不管写没写 assigned_to，只要规则匹配就 +1）
    route_written_counter: Dict[str, int] = {}  # 实际写入 assigned_to 的条数（.env 填了真实 open_id 才会 +1）
    route_miss_unassigned = 0  # 规则命中了但 open_id 没配

    for row in csv_records:
        fields = {}

        # ⚠️ feedback_id（飞书字段类型=1005 自动编号，API 无法写入，跳过！）
        # 若以后希望写入 S-舆情/H-扫码/M-mock 的自定义前缀，
        # 请在飞书多维表格UI里把该字段类型从「自动编号」改为「文本」，
        # 再放开下一行注释即可：
        # fields["feedback_id"] = str(row.get("feedback_id", "")).strip()

        # ========== 单选字段（channel/user_tier/category/priority/status/contact_allowed）
        # 飞书类型码=3，必须严格等于 options 里的字符串
        # ★ 语言统一：写入前用 to_bitable_* 把 Schema 枚举（channel 英文、其余中文）
        #   转换为飞书 UI 里实际配置的中文选项文本，彻底杜绝「无匹配类别」兜底风险
        #   （特别是 channel：social_media → 社媒舆情）
        # ==========
        channel = to_bitable_channel(str(row.get("channel", "")).strip())
        if channel:
            fields["channel"] = channel

        user_tier = to_bitable_user_tier(str(row.get("user_tier", "")).strip())
        if user_tier:
            fields["user_tier"] = user_tier

        # 保存 category/priority/city 原始值（CSV Schema 态），后面路由分派要用
        category_raw_for_route = str(row.get("category", "")).strip()
        priority_raw_for_route = str(row.get("priority", "")).strip()
        city_raw_for_route = str(row.get("city", "")).strip()

        category = to_bitable_category(category_raw_for_route)
        if category:
            fields["category"] = category

        priority = to_bitable_priority(priority_raw_for_route)
        if priority:
            fields["priority"] = priority

        status = to_bitable_status(str(row.get("status", "")).strip())
        if status:
            fields["status"] = status

        # ========== 普通文本字段（vehicle_id/city/content_raw/content_summary/contact_name）======
        for text_key in ("vehicle_id", "city", "content_raw", "content_summary", "contact_name"):
            v = str(row.get(text_key, "")).strip()
            if v:
                fields[text_key] = v

        # ========== 电话字段（contact_phone，类型=13）直接字符串 =========================
        contact_phone = str(row.get("contact_phone", "")).strip()
        if contact_phone:
            fields["contact_phone"] = contact_phone

        # ========== 日期时间字段（created_at/closed_at，类型=5 毫秒时间戳）===============
        created_at = format_datetime(row.get("created_at", ""))
        if created_at:
            fields["created_at"] = created_at

        closed_at = format_datetime(row.get("closed_at", ""))
        if closed_at:
            fields["closed_at"] = closed_at

        # ========== assigned_to（人员字段 类型=11，需要 open_id）==========================
        # P1 新增：Python 代码端按 category/priority/city 规则路由
        #   步骤：route_assignee_env_key → .env变量名 → open_id_lookup拿真实 ou_xxx → 写入 [{"id": ou_xxx}]
        env_key = route_assignee_env_key(category_raw_for_route, priority_raw_for_route, city_raw_for_route)
        if env_key:
            # ⚠️ 修复：规则一旦命中（不管 open_id 配没配）都先 +1 到 route_hit_counter，
            #        这样答辩时即使 .env 全空，规则表的命中条数也能真实显示给评委看
            route_hit_counter[env_key] = route_hit_counter.get(env_key, 0) + 1
            real_open_id = open_id_lookup.get(env_key, "").strip()
            if real_open_id:
                # 飞书用户类型字段的 API 写入格式是数组包对象 [{"id": open_id}]
                fields["assigned_to"] = [{"id": real_open_id}]
                route_written_counter[env_key] = route_written_counter.get(env_key, 0) + 1
            else:
                # 规则匹配到了但 open_id 没配置 → 不写字段（保持原行为，不计入失败）
                route_miss_unassigned += 1

        # ========== csat_score（类型=2 Number，1-5 星级）================================
        csat_score = row.get("csat_score", "")
        if csat_score not in ("", None):
            try:
                n = int(str(csat_score).strip())
                if 1 <= n <= 5:
                    fields["csat_score"] = n
            except (ValueError, TypeError):
                pass

        # ========== contact_allowed（单选 类型=3，选项只有「是/否」2 项，**没有空选项！**）====
        # 用 schema_constants.validate_contact_allowed 归一化 → 合法三态：是/否/""
        contact_allowed_norm = validate_contact_allowed(row.get("contact_allowed", ""))
        if contact_allowed_norm in ("是", "否"):
            # 只有当值是明确的是/否时才写入字段；空值不传键（飞书单选默认为未选择状态）
            fields["contact_allowed"] = contact_allowed_norm

        # ========== location_detail（类型=22 Location，必须 {"name": xxx} 结构）=============
        location_detail = str(row.get("location_detail", "")).strip()
        if location_detail:
            fields["location_detail"] = {"name": location_detail}

        bitable_records.append({"fields": fields})

    # ========== P1 新增：路由分派命中报告（答辩讲给评委听，即使没写 open_id 也能讲）==========
    print("\n" + "=" * 72)
    print("🧭  P1 路由分派报告（Python 代码端自动派单规则命中情况）")
    print("=" * 72)
    print(f"  · 路由规则优先级（从高到低，共 {len(describe_route_rules())} 条）：")
    total_written = sum(route_written_counter.values())
    for rule_label, env_key in describe_route_rules():
        cnt_hit = route_hit_counter.get(env_key, 0)
        cnt_written = route_written_counter.get(env_key, 0)
        if cnt_written > 0:
            flag = f"✅ 已写入 {cnt_written} 条"
        elif cnt_hit > 0:
            flag = "🔧 命中规则，待配open_id"
        else:
            flag = "—"
        print(f"     - {rule_label:40s} → {env_key:36s} 命中 {cnt_hit:3d} 条  {flag}")
    print(f"\n  · 总计：{len(bitable_records)} 条工单")
    print(f"     → 规则表总命中：{sum(route_hit_counter.values())} 条（{sum(route_hit_counter.values())/max(len(bitable_records),1)*100:.0f}% 工单已匹配规则）")
    print(f"     → 成功派单并写入 assigned_to：{total_written} 条")
    print(f"     → 规则命中但 .env 未填 open_id（不写字段，原行为不变）：{route_miss_unassigned} 条")
    print(f"     → （演示提示：即使写入 0 条也没关系，评委看「命中 N 条」列 + 规则表就能理解派单逻辑）")
    print("=" * 72 + "\n")

    return bitable_records


def delete_all_records(app_token: str, table_id: str, tenant_access_token: str) -> bool:
    """删除多维表格中所有记录"""
    url = BITABLE_RECORDS_URL.format(app_token=app_token, table_id=table_id)
    headers = {"Authorization": f"Bearer {tenant_access_token}"}
    
    print("🗑️ 正在获取所有记录ID...")
    
    # 获取所有记录ID
    record_ids = []
    page_token = ""
    
    while True:
        params = {"page_size": 500}
        if page_token:
            params["page_token"] = page_token
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"❌ 获取记录列表失败：{exc}")
            return False
        
        result = response.json()
        if result.get("code") != 0:
            print(f"❌ 飞书返回错误：code={result.get('code')}, msg={result.get('msg')}")
            return False
        
        data = result.get("data", {})
        records = data.get("items", [])
        
        for record in records:
            record_ids.append(record.get("record_id"))
        
        page_token = data.get("page_token")
        if not page_token:
            break
    
    if not record_ids:
        print("   ✅ 表格为空，无需删除")
        return True
    
    print(f"   找到 {len(record_ids)} 条记录，正在删除...")

    # 批量删除（每批 20 条，飞书 API 保守兼容上限；原 50 条过大会触发 400 Bad Request）
    delete_url = url + "/batch_delete"
    DELETE_BATCH = 20
    success_count = 0

    for i in range(0, len(record_ids), DELETE_BATCH):
        batch_ids = record_ids[i:i + DELETE_BATCH]
        batch_no = i // DELETE_BATCH + 1
        total_batches = (len(record_ids) + DELETE_BATCH - 1) // DELETE_BATCH

        try:
            response = requests.post(
                delete_url,
                json={"record_ids": batch_ids},
                headers=headers,
                timeout=30,
            )
            if response.status_code != 200:
                print(f"     批次 {batch_no}/{total_batches} HTTP {response.status_code}: {response.text[:200]}")
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"❌ 删除失败 批次 {batch_no}/{total_batches}: {exc}")
            return False

        result = response.json()
        if result.get("code") != 0:
            print(
                f"❌ 删除失败 批次 {batch_no}/{total_batches}: "
                f"code={result.get('code')}, msg={result.get('msg')}"
            )
            return False

        success_count += len(batch_ids)
        print(f"   ✅ 批次 {batch_no}/{total_batches} 已删除 {len(batch_ids)} 条，累计 {success_count}/{len(record_ids)}")
    
    print(f"   ✅ 删除成功，共删除 {success_count} 条记录")
    return True


def batch_create_records(
    app_token: str, table_id: str, tenant_access_token: str, records: List[Dict[str, Any]]
) -> bool:
    """批量创建记录到飞书多维表格（带重试机制）"""
    url = BITABLE_BATCH_CREATE_URL.format(app_token=app_token, table_id=table_id)
    headers = {
        "Authorization": f"Bearer {tenant_access_token}",
        "Content-Type": "application/json",
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                url,
                json={"records": records},
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            try:
                error_detail = response.json()
                code = error_detail.get("code")
                msg = error_detail.get("msg")
                
                # 1254607 表示数据未准备好，需要重试
                if code == 1254607 and attempt < MAX_RETRIES - 1:
                    print(f"   ⏳ 数据未准备好，{RETRY_DELAY}秒后重试（{attempt+1}/{MAX_RETRIES}）")
                    time.sleep(RETRY_DELAY)
                    continue
                
                print(f"❌ 批量创建失败：{exc}")
                print(f"   错误详情：code={code}, msg={msg}")
            except:
                print(f"❌ 批量创建失败：{exc}")
            return False
        
        result = response.json()
        if result.get("code") != 0:
            code = result.get("code")
            msg = result.get("msg")
            
            # 1254607 表示数据未准备好，需要重试
            if code == 1254607 and attempt < MAX_RETRIES - 1:
                print(f"   ⏳ 数据未准备好，{RETRY_DELAY}秒后重试（{attempt+1}/{MAX_RETRIES}）")
                time.sleep(RETRY_DELAY)
                continue
            
            print(f"❌ 飞书返回错误：code={code}, msg={msg}")
            return False
        
        return True
    
    return False


def main():
    print("============================================")
    print("📥 CSV 数据导入飞书多维表格")
    print("============================================")
    
    # 加载配置
    config = load_env()
    if not config:
        return
    
    app_id = config["FEISHU_APP_ID"]
    app_secret = config["FEISHU_APP_SECRET"]
    app_token = config["BITABLE_APP_TOKEN"]
    table_id = config["BITABLE_TABLE_ID"]
    
    # 读取 CSV
    if not os.path.exists(CSV_PATH):
        print(f"❌ CSV 文件不存在：{CSV_PATH}")
        return
    
    csv_records = read_csv(CSV_PATH)
    if not csv_records:
        print("❌ CSV 文件为空")
        return
    
    # 获取访问令牌
    print("🔑 正在获取飞书访问令牌...")
    token = get_tenant_access_token(app_id, app_secret)
    if not token:
        return
    
    # 删除已有记录（尝试，失败则跳过）
    print("🗑️ 正在清理已有记录...")
    if not delete_all_records(app_token, table_id, token):
        print("⚠️ 清理记录失败，继续追加导入（可能会有重复数据）")
    
    # ============================================================
    # P1 路由分派：从 .env 读取所有 ROUTE_*_OPEN_ID 构建查找表
    #   · 即使 .env 里全为空（没填真实 open_id），也会正常执行规则统计
    #     → 答辩演示时能打印出每条规则命中了多少条工单，逻辑可视化
    #   · 填了真实 open_id 的就自动写入 assigned_to = [{"id": open_id}]
    # ============================================================
    print("🧭 正在加载路由分派规则表...")
    open_id_lookup: Dict[str, str] = {}
    for _label, env_key in describe_route_rules():
        open_id_lookup[env_key] = os.getenv(env_key, "").strip()
    filled_count = sum(1 for v in open_id_lookup.values() if v)
    print(f"   规则表共 {len(open_id_lookup)} 条，已填 open_id：{filled_count} 条（未填则不写 assigned_to）")

    # 转换格式（含路由分派 assigned_to 写入）
    print("🔄 正在转换数据格式（含路由分派）...")
    bitable_records = convert_to_bitable_format(csv_records, open_id_lookup)
    
    # 分批上传
    total = len(bitable_records)
    success_count = 0
    
    print(f"📤 正在分批上传到多维表格（共 {total} 条，每批 {BATCH_SIZE} 条）...")
    
    for i in range(0, total, BATCH_SIZE):
        batch = bitable_records[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"  批次 {batch_num}/{total_batches}：正在上传 {len(batch)} 条记录...")
        
        if batch_create_records(app_token, table_id, token, batch):
            success_count += len(batch)
            print(f"    ✅ 批次 {batch_num} 上传成功")
        else:
            print(f"    ❌ 批次 {batch_num} 上传失败")
    
    print("============================================")
    print(f"📊 导入完成！")
    print(f"   总记录数：{total}")
    print(f"   成功上传：{success_count}")
    print(f"   失败数量：{total - success_count}")
    print("============================================")


if __name__ == "__main__":
    main()
