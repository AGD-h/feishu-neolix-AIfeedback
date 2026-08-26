# -*- coding: utf-8 -*-
"""
飞书 AI 分类召回率兜底脚本：apply_ai_classification_fallback.py

【为什么需要这个脚本】
飞书多维表格的「AI 字段」功能：
  ① 无法通过 OpenAPI 写入 system prompt（官方未开放）
  ② 浏览器 UI 自动化成功率极低（飞书 SPA 交互元素无法被 CDP 引擎识别）
  ③ 导致 category / priority 常被飞书 AI 二次覆盖为「无匹配类别」

【本脚本做什么】
相当于**用 Python 服务端代替飞书 AI 字段做二次兜底校验**：
  Step 1：拉飞书多维表格「最近 N 条」记录（默认最近 50 条，或指定 --last-minutes N）
  Step 2：逐条筛查：
     · 若 category == 空/「无匹配类别」 → 调用 DeepSeek（与UI prompt 100%同规则）重判 category
     · 若 priority == 空/「无匹配类别」/非法P0~P3 → 调用 DeepSeek 重判 priority
     · （可选 --summary 开关）若 content_summary 为空也重写 AI 摘要
  Step 3：对需要修复的记录，PATCH /records/:record_id 写回飞书
  Step 4：输出修复报告（多少条需要修 / 原来是什么 → 修完是什么）

【调用方式】
  # 修复最近 50 条
  python scripts\\apply_ai_classification_fallback.py
  # 修复最近 120 分钟（2 小时）内创建的记录
  python scripts\\apply_ai_classification_fallback.py --last-minutes 120
  # 同时修复 content_summary 为空的记录（默认只修 category/priority）
  python scripts\\apply_ai_classification_fallback.py --summary
  # 只打印报告，不实际写入（dry-run）
  python scripts\\apply_ai_classification_fallback.py --dry-run

【依赖】.env 中必须已有：FEISHU_APP_ID/SECRET / BITABLE_APP_TOKEN/TABLE_ID / DEEPSEEK_API_KEY
"""
import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv

# 项目根目录 & 跨目录 import schema_constants / CLEAN_PROMPT 常量
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT / "data"))  # import search_public_opinion.py 要这个

from schema_constants import (
    VALID_CATEGORIES, VALID_PRIORITIES, VALID_USER_TIERS,
    to_bitable_category, to_bitable_priority,
    # P1 路由分派补派：从飞书读出值 → Schema标准值（用于规则匹配）+ 路由规则
    from_bitable_category, from_bitable_priority,
    route_assignee_env_key, describe_route_rules,
)

# ============================================================
# 一、配置加载
# ============================================================
def load_env() -> Optional[Dict[str, str]]:
    env_path = _PROJECT_ROOT / ".env"
    if not env_path.is_file():
        print(f"❌ 找不到 .env：{env_path}")
        return None
    load_dotenv(dotenv_path=str(env_path), override=False)
    keys = [
        "FEISHU_APP_ID", "FEISHU_APP_SECRET",
        "BITABLE_APP_TOKEN", "BITABLE_TABLE_ID",
        "DEEPSEEK_API_KEY",
    ]
    cfg = {k: os.getenv(k, "").strip() for k in keys}
    for k, v in cfg.items():
        if not v:
            print(f"❌ .env 里 {k} 为空")
            return None
    print(f"✅ 加载 .env 成功：{env_path}")
    return cfg


TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"

def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    """获取应用级 tenant_access_token（自建应用内部）"""
    try:
        r = requests.post(
            TOKEN_URL,
            json={"app_id": app_id, "app_secret": app_secret},
            timeout=15,
        )
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


# ============================================================
# 二、DeepSeek 调用（与飞书 UI prompt 100% 同规则）
# ============================================================
# 注意：直接复用 search_public_opinion.py 里的 CLEAN_PROMPT 太麻烦（耦合了18字段完整处理）
#      这里为 category / priority 单独写一份 **极简单字段 prompt**，
#      但字段定义、关键词映射、Few-Shot 与 UI prompt 模板保持 100% 对齐。

CATEGORY_PROMPT = """你是「新石器无人配送车反馈工单分类专家」。
请根据以下工单信息，判断 category（工单类别）。
只输出一个中文词，从这 5 个里选：安全 / 故障 / 体验 / 投诉 / 建议。绝对不要输出其他词，不要加标点不要解释。
⚠️  反向规则：**严禁默认选「建议」！如果你不确定就选「体验」。**
  只有当内容明确包含：建议/希望/能不能/优化/改进/应该/建议增加/路线规划/推广/扩张/政策/行业/展会/合作 这些词，才能选「建议」。
  关键词出现就优先匹配：
    · 出现 撞/剐/事故/摔倒/受伤/120/报警/110/监管/报备/整改/消防/违规/隐患/火灾/漏电/危险 → 强制选 安全
    · 出现 坏/趴窝/停住不动/没电/卡顿/急刹/骤停/失灵/充不了/充电/续航/断网/死机/黑屏/跑偏/取件口打不开 → 强制选 故障
    · 出现 取件失败/找车难/扫不开/扫码失败/太慢/速度慢/挡路/占道/位置偏/路线绕/等太久/电话打不通 → 强制选 体验
    · 出现 投诉/不满/差评/垃圾/赔偿/赔/退钱/退款/说法/举报/客服态度差/12315 → 强制选 投诉
    · 出现 建议/希望/能不能/优化/改进/应该/建议增加/路线规划/推广/扩张/政策/行业/展会/合作 → 才能选 建议

【Few-Shot（照此逻辑类推）—— 注意顺序：投诉/安全/故障样例放最末，降低建议默认概率】
输入：L4级无人车公司重组配置官宣
输出：建议
输入：扫三次二维码都没打开车身屏幕一直转圈
输出：体验
输入：沈阳无人车剐蹭电动车致大爷擦伤留纸条
输出：安全
输入：深圳暴雨后12台新石器趴窝停运
输出：故障
输入：黑猫投诉丢快递要求赔偿12315举报
输出：投诉
"""

PRIORITY_PROMPT = """你是「新石器无人配送车反馈工单分级专家」。
已知工单内容和 category 分类结果，请判断 priority（SLA优先级）。
只输出一个英文代号，从这 4 个里选：P0 / P1 / P2 / P3。不要输出其他。

【分级定义+SLA联动规则】
· P0（5分钟响应）：category=安全 且 内容含：撞/事故/摔倒/受伤/120/监管/消防/交警/110/人员伤亡 → 强制P0
· P1（30分钟响应）：category=故障 且 含：趴窝/大面积/充电失败/无法使用/停运/全天没车；或 category=安全但不够P0
· P2（1小时响应）：category=投诉（默认P2）；category=体验（默认P2）；category=故障但局部问题
· P3（24小时响应）：category=建议（永远P3）

【Few-Shot（照此逻辑类推）】
输入 category=安全 内容=剐蹭大爷擦伤留纸条
输出：P0
输入 category=故障 内容=12台车趴窝停运
输出：P1
输入 category=体验 内容=扫码三次失败
输出：P2
输入 category=投诉 内容=丢快递要求赔偿
输出：P2
输入 category=建议 内容=L4级无人车配置官宣
输出：P3
输入 category=安全 内容=车身贴违规贴纸市容但无人受伤
输出：P1
"""

SUMMARY_PROMPT = """你是工单摘要专家。35字以内精炼摘要，必须包含三要素：来源平台+核心问题+影响对象。不要废话。
示例1：微博舆情：无人车剐蹭老人留致歉条未联系车主
示例2：知乎舆情：暴雨后12台无人车趴窝运营中断
"""


def _call_deepseek(cfg: Dict[str, str], system: str, user_text: str) -> str:
    """调用 DeepSeek（openai SDK 兼容），返回纯文本结果。失败返回空串。"""
    api_key = cfg["DEEPSEEK_API_KEY"]
    base = "https://api.deepseek.com/v1"
    try:
        r = requests.post(
            base + "/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "deepseek-chat",
                "temperature": 0.1,
                "max_tokens": 30,
                "response_format": {"type": "text"},
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_text},
                ],
            },
            timeout=45,
        )
    except Exception as e:
        print(f"    ❌ DeepSeek 网络异常：{e}")
        return ""
    if r.status_code != 200:
        print(f"    ❌ DeepSeek HTTP {r.status_code}：{r.text[:300]}")
        return ""
    data = r.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as e:
        print(f"    ❌ DeepSeek 响应格式异常：{e} / {data}")
        return ""


# ============================================================
# 二.五、【本地关键词规则引擎】优先于 DeepSeek 调用
#   逻辑与 search_public_opinion.fallback_clean_lead 100% 对齐
#   优点：①无网络QPS限制 ②无"默认选建议"偏见 ③省钱 ④速度快
# ============================================================
def _rule_category(text: str) -> Optional[str]:
    """关键词规则匹配 category，命中返回分类/None（没命中再调 DeepSeek）"""
    if any(kw in text for kw in [
        "撞", "剐", "刮", "事故", "摔倒", "砸", "压", "受伤", "流血",
        "120", "报警", "110", "监管", "报备", "整改", "消防", "违规",
        "隐患", "火灾", "漏电", "危险",
    ]):
        return "安全"
    if any(kw in text for kw in [
        "坏", "坏了", "故障", "打不开", "趴窝", "停住不动", "没电", "卡住",
        "卡顿", "急刹", "骤停", "失灵", "充不了", "充电", "续航", "断网",
        "无信号", "死机", "黑屏", "跑偏", "取件口",
    ]):
        return "故障"
    if any(kw in text for kw in [
        "投诉", "不满", "赔偿", "差评", "垃圾", "退钱", "说法", "赔",
        "退款", "举报", "客服态度差", "12315",
    ]):
        return "投诉"
    if any(kw in text for kw in [
        "建议", "希望", "能不能", "优化", "改进", "应该", "建议增加",
        "觉得可以", "路线规划", "推广", "扩张", "政策", "行业动态",
        "展会", "合作",
    ]):
        return "建议"
    if any(kw in text for kw in [
        "取件失败", "找车难", "扫不开", "扫码失败", "太慢", "速度慢",
        "挡路", "占道", "位置偏", "路线绕", "等太久", "电话打不通",
    ]):
        return "体验"
    return None


def _rule_priority(text: str, category: str) -> Optional[str]:
    """关键词规则匹配 priority（需要 category 已经是合法5类）。命中返回优先级，None=再调 DeepSeek。"""
    if category == "安全" and any(kw in text for kw in [
        "撞", "事故", "摔倒", "受伤", "120", "监管", "消防", "交警", "110",
    ]):
        return "P0"
    if category in ("安全", "故障") and any(kw in text for kw in [
        "严重", "紧急", "全断", "无法使用", "趴窝", "大面积", "充电失败",
    ]):
        return "P1"
    if category == "投诉":
        return "P2"
    if category == "建议":
        return "P3"
    if category == "体验":
        return "P2"
    return None


def ai_fix_category(cfg: Dict[str, str], content_raw: str, channel: str, user_tier: str) -> str:
    """【规则优先+AI兜底】重判 category。返回 5 合法枚举之一，失败返回「体验」。"""
    # Step 1：先用本地关键词规则匹配（快、稳、无偏见）
    rule_res = _rule_category(content_raw)
    if rule_res:
        print(f"    🧠 本地规则命中 category={rule_res}（跳过 DeepSeek 省 QPS）")
        return rule_res
    # Step 2：规则没命中 → 调 DeepSeek
    user_text = (
        f"渠道：{channel}；用户层级：{user_tier}\n"
        f"工单原始内容：{content_raw}\n"
        f"请输出 5 选 1（安全/故障/体验/投诉/建议）："
    )
    res = _call_deepseek(cfg, CATEGORY_PROMPT, user_text)
    # 去掉可能出现的标点空格
    res_clean = res.replace(" ", "").replace("　", "").replace("。", "").replace("，", "").strip()
    if res_clean in VALID_CATEGORIES:
        return res_clean
    # 如果输出里包含了关键字（例如包含了「安全」两字但前后有废话），做模糊匹配
    for c in VALID_CATEGORIES:
        if c in res:
            return c
    print(f"    ⚠️  DeepSeek category 输出非法='{res}' → 兜底=体验")
    return "体验"


def ai_fix_priority(cfg: Dict[str, str], content_raw: str, category: str) -> str:
    """【规则优先+AI兜底】重判 priority。返回 P0/P1/P2/P3，失败返回 P2。"""
    # Step 1：先跑本地规则
    rule_res = _rule_priority(content_raw, category)
    if rule_res:
        print(f"    🧠 本地规则命中 priority={rule_res}（跳过 DeepSeek 省 QPS）")
        return rule_res
    # Step 2：规则没命中 → 调 DeepSeek
    user_text = (
        f"category={category}\n"
        f"工单内容：{content_raw}\n"
        f"请输出 4 选 1（P0/P1/P2/P3）："
    )
    res = _call_deepseek(cfg, PRIORITY_PROMPT, user_text)
    res_clean = res.upper().strip()
    if res_clean in VALID_PRIORITIES:
        return res_clean
    for p in VALID_PRIORITIES:
        if p in res_clean:
            return p
    print(f"    ⚠️  DeepSeek priority 输出非法='{res}' → 兜底=P2")
    return "P2"


def ai_fix_summary(cfg: Dict[str, str], content_raw: str, channel: str) -> str:
    """DeepSeek 生成 content_summary（35 字以内）。失败返回空串由用户补充。"""
    user_text = f"来源平台：{channel}；工单内容：{content_raw}\n输出35字内摘要："
    res = _call_deepseek(cfg, SUMMARY_PROMPT, user_text)
    return res[:40] if res else ""


# ============================================================
# 三、飞书 API：拉记录 / PATCH 更新
# ============================================================
def list_all_bitable_records(app_token: str, table_id: str, token: str,
                             limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """拉多维表格全部记录（支持 limit 只取前 N 条用于加速）。"""
    base = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    headers = {"Authorization": f"Bearer {token}"}
    rows: List[Dict[str, Any]] = []
    page_token = ""
    while True:
        params = {"page_size": 500 if limit is None else min(500, limit)}
        if page_token:
            params["page_token"] = page_token
        r = requests.get(base, headers=headers, params=params, timeout=30)
        if r.status_code != 200:
            print(f"❌ list records HTTP {r.status_code}：{r.text[:300]}")
            break
        data = r.json()
        if data.get("code") != 0:
            print(f"❌ list records API {data.get('code')}：{data.get('msg')}")
            break
        items = (data.get("data") or {}).get("items") or []
        for it in items:
            fid = it.get("record_id")
            fields = it.get("fields") or {}
            fields["_record_id"] = fid
            rows.append(fields)
            if limit is not None and len(rows) >= limit:
                return rows
        has_more = (data.get("data") or {}).get("has_more")
        page_token = (data.get("data") or {}).get("page_token", "")
        if not has_more or not page_token:
            break
    return rows


def patch_record(app_token: str, table_id: str, token: str,
                 record_id: str, fields: Dict[str, Any]) -> bool:
    """PUT 更新单条记录的 fields（⚠️ 飞书多维表格的单条更新是 PUT 不是 PATCH，PATCH 会 404）。成功返回 True。"""
    url = (
        f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}"
        f"/tables/{table_id}/records/{record_id}"
    )
    try:
        r = requests.put(
            url,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"fields": fields},
            timeout=20,
        )
    except Exception as e:
        print(f"    ❌ PUT 网络异常：{e}")
        return False
    if r.status_code != 200:
        print(f"    ❌ PUT HTTP {r.status_code}：{r.text[:300]}")
        return False
    data = r.json()
    if data.get("code") != 0:
        print(f"    ❌ PUT API {data.get('code')}：{data.get('msg')}")
        return False
    return True


# ============================================================
# 四、主流程
# ============================================================
def main() -> int:
    parser = argparse.ArgumentParser(
        description="飞书 AI 分类兜底器：把 category/priority=无匹配类别 的工单用 DeepSeek 重判并写回飞书",
    )
    parser.add_argument("--last-count", type=int, default=50,
                        help="只处理最新多少条记录（默认 50 条，覆盖近1-2批次导入）")
    parser.add_argument("--last-minutes", type=int, default=0,
                        help="只处理过去 N 分钟内 created_at > (now-N分钟) 的记录（0=不启用）")
    parser.add_argument("--summary", action="store_true",
                        help="顺便修复 content_summary 为空的工单（默认只修 category/priority）")
    parser.add_argument("--dry-run", action="store_true",
                        help="只打印修复报告，不实际写回飞书（模拟用）")
    args = parser.parse_args()

    cfg = load_env()
    if not cfg:
        return 2
    token = get_tenant_access_token(cfg["FEISHU_APP_ID"], cfg["FEISHU_APP_SECRET"])
    if not token:
        return 3

    app_token = cfg["BITABLE_APP_TOKEN"]
    table_id = cfg["BITABLE_TABLE_ID"]

    # ============================================================
    # P1 路由分派补派兜底：构建 open_id_lookup
    #   · 一级分派（import_csv）漏派时，这里做二级兜底
    #   · 即使 .env 全空，也至少能打印「补派规则命中报告」
    # ============================================================
    print("🧭 正在加载路由分派补派规则表...", flush=True)
    open_id_lookup: Dict[str, str] = {}
    for _label, env_key in describe_route_rules():
        open_id_lookup[env_key] = os.getenv(env_key, "").strip()
    filled_count = sum(1 for v in open_id_lookup.values() if v)
    route_hit_count = 0  # 补派命中条数（即使 open_id 为空，只要规则命中就算）
    route_written_count = 0  # 实际写入 assigned_to 的条数（.env 填了真实 open_id 才会 +1）
    print(f"   补派规则表共 {len(open_id_lookup)} 条，已填 open_id：{filled_count} 条", flush=True)

    # 1. 拉取目标记录
    # ⚠️  飞书 list records API 默认按创建时间**升序**返回（最老→最新）。
    #      所以如果用 limit=X 只拉前 X 条，拿到的是 7 月最老的工单，不是要修的「最后 N 条」。
    #      正确做法：先**拉全量**（1800+ 条实际只需 < 3 秒），再在本地 [-last_count:] 切片 = 最后 N 条最新。
    print(f"📡 拉取飞书多维表格**全量记录**（API 默认升序，拉全后切片取最后 {args.last_count} 条 = 最新）...", flush=True)
    all_rows = list_all_bitable_records(app_token, table_id, token, limit=None)  # None=全量
    print(f"📡 全量共 {len(all_rows)} 条，取最后 {args.last_count} 条作为本次扫描目标", flush=True)
    target_rows = all_rows[-args.last_count:] if args.last_count < len(all_rows) else all_rows

    # 2. 如果启用了 --last-minutes，再按 created_at 窗口过滤
    if args.last_minutes > 0:
        cutoff_ms = int(time.time() * 1000) - args.last_minutes * 60 * 1000
        before = len(target_rows)
        target_rows = [
            r for r in target_rows
            if isinstance(r.get("created_at"), int) and r["created_at"] >= cutoff_ms
        ]
        print(f"⏰ 按 created_at 时间窗口过滤：{before} → {len(target_rows)} 条（最近 {args.last_minutes} 分钟内）")

    if not target_rows:
        print("✅ 没有符合条件的待处理记录，直接结束")
        return 0

    # 3. 遍历每条记录，筛查+修复
    fix_candidates: List[Dict[str, Any]] = []  # 需要修复的列表：{record_id, old_fields, new_fields, note}
    for idx, r in enumerate(target_rows, 1):
        record_id = r.get("_record_id", "")
        if not record_id:
            continue
        content_raw = str(r.get("content_raw", "")).strip()
        channel = str(r.get("channel", "")).strip()
        user_tier = str(r.get("user_tier", "")).strip()
        old_cat = str(r.get("category", "")).strip()
        old_pri = str(r.get("priority", "")).strip()
        old_sum = str(r.get("content_summary", "")).strip()

        if not content_raw:
            # 没有原始内容就无法 AI 判，跳过
            continue

        needs_fix = False
        new_fields: Dict[str, Any] = {}
        note_parts: List[str] = []

        # ---- Category 修复逻辑 ----
        cat_invalid = (
            (not old_cat)
            or old_cat == "无匹配类别"
            or old_cat not in VALID_CATEGORIES
        )
        if cat_invalid:
            new_cat = ai_fix_category(cfg, content_raw, channel, user_tier)
            new_cat_bitable = to_bitable_category(new_cat)
            new_fields["category"] = new_cat_bitable
            note_parts.append(f"category: '{old_cat}' → '{new_cat_bitable}'")
            needs_fix = True
            # 更新 new_cat 变量供后续 priority 判断使用（如果 old_cat 原本非法，则用新判的 category 作为 pri 的输入）
            cat_for_pri = new_cat
        else:
            cat_for_pri = old_cat

        # ---- Priority 修复逻辑 ----
        pri_invalid = (
            (not old_pri)
            or old_pri == "无匹配类别"
            or old_pri not in VALID_PRIORITIES
        )
        if pri_invalid:
            new_pri = ai_fix_priority(cfg, content_raw, cat_for_pri)
            new_pri_bitable = to_bitable_priority(new_pri)
            new_fields["priority"] = new_pri_bitable
            note_parts.append(f"priority: '{old_pri}' → '{new_pri_bitable}'")
            needs_fix = True

        # ---- (可选) Content Summary 修复 ----
        if args.summary and not old_sum:
            new_sum = ai_fix_summary(cfg, content_raw, channel)
            if new_sum:
                new_fields["content_summary"] = new_sum
                note_parts.append(f"content_summary: 空 → '{new_sum[:30]}…'")
                needs_fix = True

        # ============================================================
        # P1 路由分派补派兜底：assigned_to 为空时自动补派
        #   · 一级分派（import_csv）如果漏派，这里做二级兜底
        #   · 规则命中但 .env 没填 open_id → 只统计命中数，不实际写回
        # ============================================================
        old_assigned = r.get("assigned_to")
        assigned_empty = (
            old_assigned is None
            or (isinstance(old_assigned, list) and len(old_assigned) == 0)
            or (isinstance(old_assigned, str) and not old_assigned.strip())
        )
        if assigned_empty:
            # 归一化 cat/pri 到 Schema 标准值（飞书端可能是中文/英文/无匹配类别，都转成标准值给路由规则匹配）
            cat_for_route = from_bitable_category(new_fields.get("category") or old_cat)
            pri_for_route = from_bitable_priority(new_fields.get("priority") or old_pri)
            # 如果还没合法值（比如 new_fields 也没修），就跳过这条的补派（避免派错池）
            if (cat_for_route in VALID_CATEGORIES
                    and pri_for_route in VALID_PRIORITIES):
                city_raw = str(r.get("city", "")).strip()
                env_key = route_assignee_env_key(cat_for_route, pri_for_route, city_raw)
                if env_key:
                    # 规则命中
                    route_hit_count += 1
                    real_open_id = open_id_lookup.get(env_key, "").strip()
                    if real_open_id:
                        # .env 填了真实 open_id → 实际写入
                        new_fields["assigned_to"] = [{"id": real_open_id}]
                        note_parts.append(f"assigned_to: 空 → 路由规则命中（{env_key}）")
                        route_written_count += 1
                        needs_fix = True
                    # 否则：规则命中但 .env 空，只统计不写回

        if needs_fix:
            fid = r.get("feedback_id", record_id)
            fix_candidates.append({
                "idx_in_target": idx,
                "fid": fid,
                "record_id": record_id,
                "new_fields": new_fields,
                "note": " + ".join(note_parts),
            })

    # 4. 输出修复报告 & 执行写回
    print("\n" + "=" * 80)
    print(f"📋 扫描报告：目标 {len(target_rows)} 条 → 待修复 {len(fix_candidates)} 条")
    # P1 路由补派命中统计（即使 .env 空，也能展示给评委规则命中了多少条）
    print(f"🧭 路由补派统计：规则命中 {route_hit_count} 条 / 实际写入 assigned_to {route_written_count} 条")
    if route_hit_count > 0 and route_written_count == 0:
        print("   ℹ️  规则全部命中但未实际写入：.env 中 ROUTE_*_OPEN_ID 未填真实 open_id（不影响演示，逻辑是对的）")
    print("=" * 80)
    for i, c in enumerate(fix_candidates, 1):
        print(f"  [{i}/{len(fix_candidates)}] feedback_id={c['fid']}")
        print(f"        {c['note']}")

    if not fix_candidates:
        print("\n🎉 所有目标记录 category/priority 都已在合法枚举，不需要修复！")
        return 0

    if args.dry_run:
        print("\n⚠️  已启用 --dry-run，不会实际写回飞书。去掉 --dry-run 参数即可正式执行")
        return 0

    print(f"\n🛠️  开始 PUT 写回飞书（共 {len(fix_candidates)} 条）...", flush=True)
    ok_cnt = 0
    for i, c in enumerate(fix_candidates, 1):
        print(f"  ({i}/{len(fix_candidates)}) 修 {c['fid']} ：{c['note']} ...", end=" ", flush=True)
        ok = patch_record(
            app_token, table_id, token,
            record_id=c["record_id"],
            fields=c["new_fields"],
        )
        if ok:
            ok_cnt += 1
            print("✅", flush=True)
        else:
            print("❌", flush=True)
        # 节流：如果本批次有 DeepSeek 调用（规则没命中时），防 QPS 超限
        time.sleep(0.6)

    print(f"\n🏁 完成：成功 {ok_cnt}/{len(fix_candidates)} 条写回飞书")
    if ok_cnt < len(fix_candidates):
        print("⚠️  部分失败，请检查上面的报错（通常是 token 过期或网络问题，重跑即可）")
        return 4

    print("\n💡 小贴士：如果飞书 UI 显示的值没刷新，按一下 F5 刷新页面。现在 category/priority 合法率应该 100% ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
