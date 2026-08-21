# -*- coding: utf-8 -*-
"""
公开舆情线索采集 + AI清洗 → 标准工单（1号 · 数据线，增强阶段）

功能清单（严格按项目约定）：
  1. 通过 SerpAPI 搜索公开网页标题、摘要和 URL（小规模≤100条，带延时）
  2. 定义 WORKORDER_SCHEMA_FIELDS 常量（18字段严格顺序，与工单池兼容）
  3. 支持命令行：--mock / --skip-clean / --dry-run / --platform / --limit
  4. 双 CSV 输出：
     - public_opinion_leads_raw.csv （线索原文，供人工复核用）
     - public_opinion_workorders.csv （标准工单Schema，可直接导入多维表格）
  5. DeepSeek 清洗成工单格式 + fallback 规则系统（模型调用失败自动走关键词规则）
  6. feedback_id 格式：FB-YYYYMMDD-S + 4位序号（S前缀=舆情采集，避免与仿真数据重复）
  7. source_platform 统一映射为 channel="social_media"

运行方式：
  # 1. 真实采集 + AI清洗 + 双输出（需要 SERPAPI_KEY 和 DEEPSEEK_API_KEY）
  python data/search_public_opinion.py

  # 2. Mock 模式（无需联网，生成假数据演示流程）
  python data/search_public_opinion.py --mock

  # 3. 只采集不清洗，输出线索CSV
  python data/search_public_opinion.py --skip-clean

  # 4. 预演模式，不写文件
  python data/search_public_opinion.py --dry-run

  # 5. 只采集微博平台
  python data/search_public_opinion.py --platform weibo
"""

import argparse
import csv
import logging
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


# ============================================================
# ★ 工单 Schema 常量（18字段严格顺序，AGENTS.md 唯一标准）★
# ============================================================
WORKORDER_SCHEMA_FIELDS = [
    "feedback_id",      # 1. 文本 FB-YYYYMMDD-Sxxxx
    "channel",          # 2. 枚举 social_media（统一映射）
    "user_tier",        # 3. 枚举 网点经理/快递员/RaaS商户/收件人/路人社区/监管方
    "category",         # 4. 枚举 安全/故障/体验/投诉/建议
    "priority",         # 5. 枚举 P0/P1/P2/P3
    "status",           # 6. 枚举 待处理/处理中/待回访/已闭环
    "vehicle_id",       # 7. 文本 如 NX-BJ-0233，可为空
    "city",             # 8. 文本 城市名
    "content_raw",      # 9. 长文本 原始反馈内容
    "content_summary",  # 10. 长文本 AI 摘要
    "created_at",       # 11. 日期时间 ISO 精确到分钟
    "closed_at",        # 12. 日期时间 可为空
    "assigned_to",      # 13. 文本 处理人姓名
    "csat_score",       # 14. 数字 1-5，可为空
    "contact_name",     # 15. 文本 联系人姓名，可为空（舆情采集默认空）
    "contact_phone",    # 16. 文本 联系人电话，可为空（舆情采集默认空）
    "contact_allowed",  # 17. 单选 是/否，可为空（舆情采集默认空）
    "location_detail",  # 18. 文本 位置详情，可为空
]

# ============================================================
# SerpAPI 接口配置
# ============================================================
SERPAPI_ENDPOINT = "https://serpapi.com/search.json"

# 线索CSV字段（人工复核用）
LEADS_RAW_FIELDS = [
    "lead_id",
    "source_platform",
    "keyword",
    "title",
    "snippet",
    "url",
    "collected_at",
    "ai_relevant",       # AI判断是否相关
    "ai_user_tier",      # AI推测用户分层
    "ai_issue_type",     # AI推测问题类型
    "ai_confidence",     # AI置信度
    "review_status",     # 待复核/已通过/已忽略
    "review_note",       # 复核备注
]

PLATFORM_LABELS = {
    "xhs": "小红书",
    "weibo": "微博",
    "zhihu": "知乎",
    "blackcat": "黑猫投诉",
}
KEYWORD_MATRIX = {
    "xhs": [
        "site:xiaohongshu.com 无人配送车",
        "site:xiaohongshu.com 无人快递车",
        "site:xiaohongshu.com 无人车 取件",
        "site:xiaohongshu.com 无人车 挡路",
        "site:xiaohongshu.com 无人车 柜门打不开",
        "site:xiaohongshu.com 顺丰 无人车",
        "site:xiaohongshu.com 无人车 小区",
        "site:xiaohongshu.com 无人车 配送",
    ],
    "weibo": [
        "site:weibo.com 无人配送车",
        "site:weibo.com 无人车 挡路",
        "site:weibo.com 无人车 取件",
    ],
    "zhihu": [
        "site:zhihu.com 无人配送车",
        "site:zhihu.com 无人车 取件",
    ],
    "blackcat": [
        "site:tousu.sina.com.cn 无人配送车",
        "site:tousu.sina.com.cn 无人快递车",
        "site:tousu.sina.com.cn 无人车 投诉",
    ],
}

CITIES_FOR_MOCK = ["北京", "石家庄", "青岛", "苏州", "无锡", "天水", "深圳", "杭州", "成都", "武汉"]


# ============================================================
# 日志配置
# ============================================================

def setup_logger() -> logging.Logger:
    """配置日志：同时输出到控制台和日志文件"""
    project_root = Path(__file__).resolve().parents[1]
    log_dir = project_root / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y%m%d")
    log_file = log_dir / f"serpapi_collect_{today}.log"

    logger = logging.getLogger("serpapi_collector")
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    logger.info("=" * 70)
    logger.info("舆情采集会话开始")
    logger.info("日志文件: %s", log_file)
    logger.info("=" * 70)

    return logger


# 全局采集统计
class CollectStats:
    """采集统计：记录API调用次数、耗时、成功率、频率等"""
    def __init__(self):
        self.total_calls = 0
        self.success_calls = 0
        self.failed_calls = 0
        self.rate_limited_calls = 0
        self.total_results = 0
        self.total_duration = 0.0
        self.call_history: List[dict] = []
        self.last_call_end: float = 0.0

    def record_call(self, keyword: str, platform: str, duration: float,
                    status_code: Optional[int], results_count: int,
                    error_msg: str = "", rate_limited: bool = False):
        self.total_calls += 1
        now = time.time()
        gap = (now - self.last_call_end) if self.last_call_end > 0 else 0.0
        self.last_call_end = now

        record = {
            "seq": self.total_calls,
            "time": datetime.now().strftime("%H:%M:%S"),
            "platform": platform,
            "keyword": keyword[:40],
            "duration": round(duration, 2),
            "status": status_code,
            "results": results_count,
            "gap": round(gap, 2),
            "error": error_msg[:80] if error_msg else "",
            "rate_limited": rate_limited,
        }
        self.call_history.append(record)
        self.total_duration += duration
        self.total_results += results_count

        if error_msg or rate_limited:
            self.failed_calls += 1
            if rate_limited:
                self.rate_limited_calls += 1
        else:
            self.success_calls += 1

    def summary(self) -> str:
        avg_duration = self.total_duration / self.total_calls if self.total_calls > 0 else 0
        success_rate = (self.success_calls / self.total_calls * 100) if self.total_calls > 0 else 0
        lines = [
            "",
            "=" * 70,
            "采集统计摘要",
            "=" * 70,
            f"总调用次数:     {self.total_calls} 次",
            f"成功调用:       {self.success_calls} 次",
            f"失败调用:       {self.failed_calls} 次",
            f"触发频率限制:   {self.rate_limited_calls} 次",
            f"成功率:         {success_rate:.1f}%",
            f"总采集结果数:   {self.total_results} 条",
            f"总耗时:         {self.total_duration:.1f} 秒",
            f"平均每次耗时:   {avg_duration:.2f} 秒",
        ]
        if self.total_calls > 0:
            gaps = [r["gap"] for r in self.call_history if r["gap"] > 0]
            if gaps:
                lines.append(f"最小调用间隔:   {min(gaps):.2f} 秒")
                lines.append(f"最大调用间隔:   {max(gaps):.2f} 秒")
                lines.append(f"平均调用间隔:   {sum(gaps)/len(gaps):.2f} 秒")
        lines.append("=" * 70)
        return "\n".join(lines)


stats = CollectStats()


# ============================================================
# 命令行参数
# ============================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="公开舆情线索采集 → DeepSeek清洗 → 双CSV输出（leads_raw + workorders）"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="每个关键词最多采集多少条，默认 5（单次≤100条）。",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印结果预览，不写入 CSV 文件。",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="★ Mock 模式：不联网，生成仿真线索演示后续流程（演示推荐用）。",
    )
    parser.add_argument(
        "--skip-clean",
        action="store_true",
        help="★ 只采集线索输出 leads_raw.csv，跳过 DeepSeek 清洗工单步骤。",
    )
    parser.add_argument(
        "--platform",
        choices=["xhs", "weibo", "zhihu", "blackcat", "all"],
        default="all",
        help="选择采集平台：xhs / weibo / zhihu / blackcat / all，默认 all。",
    )
    parser.add_argument(
        "--min-interval",
        type=float,
        default=1.5,
        help="两次API请求间最小等待秒数（防限流），默认 1.5。",
    )
    parser.add_argument(
        "--max-interval",
        type=float,
        default=3.0,
        help="两次API请求间最大等待秒数（防限流），默认 3.0。",
    )
    return parser.parse_args()


# ============================================================
# 工具函数
# ============================================================

def get_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_serpapi_key(project_root: Path) -> Optional[str]:
    load_dotenv(project_root / ".env")
    serpapi_key = os.getenv("SERPAPI_KEY", "").strip()
    if not serpapi_key:
        print("未找到 SERPAPI_KEY。")
        print("请先到 https://serpapi.com 注册账号，获取 API Key。")
        print("然后把下面这一行填入项目根目录的 .env 文件：")
        print("SERPAPI_KEY=你的SerpAPIKey")
        return None
    return serpapi_key


def load_deepseek_key(project_root: Path) -> Optional[str]:
    load_dotenv(project_root / ".env")
    return os.getenv("DEEPSEEK_API_KEY", "").strip() or None


def get_selected_keywords(platform: str) -> List[tuple]:
    if platform == "all":
        selected_platforms = ["xhs", "weibo", "zhihu", "blackcat"]
    else:
        selected_platforms = [platform]

    keywords = []
    for platform_key in selected_platforms:
        for keyword in KEYWORD_MATRIX[platform_key]:
            keywords.append((platform_key, keyword))
    return keywords


def detect_source_platform(url: str, fallback_platform_key: str) -> str:
    domain = urlparse(url).netloc.lower()
    if "xiaohongshu.com" in domain:
        return "小红书"
    if "weibo.com" in domain:
        return "微博"
    if "zhihu.com" in domain:
        return "知乎"
    if "tousu.sina.com.cn" in domain:
        return "黑猫投诉"
    return PLATFORM_LABELS[fallback_platform_key]


# ============================================================
# ★ Fallback 规则系统（DeepSeek 调用失败时兜底）★
# ============================================================

def fallback_clean_lead(title: str, snippet: str, source_platform: str) -> Dict[str, Any]:
    """
    规则引擎兜底：当 DeepSeek 不可用时，基于关键词规则生成标准工单字段。
    保证"模型挂了也能输出数据"，不会空跑。

    规则来源：AGENTS.md 优先级/分类/用户分层约定
    """
    text = f"{title} {snippet}"

    # 1. category：基于关键词匹配
    if any(kw in text for kw in ["撞", "刮", "事故", "摔倒", "危险", "安全", "消防", "监管", "报备", "行人"]):
        category = "安全"
    elif any(kw in text for kw in ["坏", "故障", "打不开", "趴窝", "没电", "卡住", "失灵", "充不了"]):
        category = "故障"
    elif any(kw in text for kw in ["投诉", "不满", "赔偿", "差评", "垃圾", "退钱", "说法"]):
        category = "投诉"
    elif any(kw in text for kw in ["建议", "希望", "能不能", "优化", "改进", "应该", "建议增加"]):
        category = "建议"
    else:
        category = "体验"

    # 2. priority：基于 category + 关键词强度
    if category == "安全" and any(kw in text for kw in ["撞", "事故", "摔倒", "监管", "消防"]):
        priority = "P0"
    elif category in ("安全", "故障") and any(kw in text for kw in ["严重", "紧急", "全断", "无法使用"]):
        priority = "P1"
    elif category == "投诉":
        priority = "P2"
    elif category == "建议":
        priority = "P3"
    else:
        priority = "P2"

    # 3. user_tier：基于平台 + 内容推断
    if source_platform == "黑猫投诉":
        user_tier = "收件人"  # 黑猫投诉多是C端用户
    elif any(kw in text for kw in ["小区", "孩子", "居民", "业主", "走路", "扰民"]):
        user_tier = "路人社区"
    elif any(kw in text for kw in ["快递", "驿站", "派件", "网点", "骑手"]):
        user_tier = random.choice(["网点经理", "快递员"])
    elif any(kw in text for kw in ["商家", "商户", "客户", "交货", "运费"]):
        user_tier = "RaaS商户"
    elif any(kw in text for kw in ["监管", "报备", "整改", "消防通道", "违规"]):
        user_tier = "监管方"
    else:
        user_tier = "收件人"

    # 4. city：基于文本尝试提取，否则留空
    city = ""
    for c in CITIES_FOR_MOCK:
        if c in text:
            city = c
            break

    # 5. summary：截取前30字（简易摘要）
    full_text = (title + snippet).strip()
    content_summary = f"[{category}] " + (full_text[:27] + "...") if len(full_text) > 27 else f"[{category}] {full_text}"

    # 6. 置信度（规则系统默认中低置信度，提示人工复核）
    confidence = 0.6

    return {
        "category": category,
        "priority": priority,
        "user_tier": user_tier,
        "city": city,
        "content_summary": content_summary,
        "ai_relevant": "是" if category in ("安全", "故障", "投诉") else "待确认",
        "ai_user_tier": user_tier,
        "ai_issue_type": category,
        "ai_confidence": f"{int(confidence*100)}%",
        "cleaned_by": "fallback_rules",  # 标记为规则兜底产出
    }


# ============================================================
# ★ DeepSeek AI 清洗（优先，失败时自动走 fallback）★
# ============================================================

CLEAN_PROMPT = """
你是舆情工单清洗助手。请根据以下线索原文，按 JSON 格式输出清洗后的标准工单字段。
只输出 JSON，不要任何解释文字。

字段要求（严格按此取值范围）：
- category：安全/故障/体验/投诉/建议 5选1
- priority：P0/P1/P2/P3 4选1
  P0=安全事故/监管介入；P1=运营中断如车辆趴窝；P2=体验问题如取件失败；P3=建议咨询
- user_tier：网点经理/快递员/RaaS商户/收件人/路人社区/监管方 6选1
- city：如果原文提到具体城市名就填，否则空字符串
- content_summary：30字以内的精炼摘要，包含平台+核心问题
- ai_relevant：是/待确认/否，是否是新石器无人配送相关
- ai_user_tier：同上 user_tier
- ai_issue_type：同上 category
- ai_confidence：百分比，如90%，表示判断可信程度

线索原文：
标题：{title}
摘要：{snippet}
平台：{source_platform}

输出JSON格式示例：
{{
  "category": "体验",
  "priority": "P2",
  "user_tier": "路人社区",
  "city": "北京",
  "content_summary": "网友反馈无人车挡路影响通行",
  "ai_relevant": "是",
  "ai_user_tier": "路人社区",
  "ai_issue_type": "体验",
  "ai_confidence": "85%"
}}
"""


def deepseek_clean_lead(title: str, snippet: str, source_platform: str,
                        api_key: str, logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
    """
    优先调用 DeepSeek 清洗；失败/超时/无API Key 时自动 fallback 到规则系统。
    返回字段统一包含 fallback_clean_lead 的所有 key + cleaned_by 标记。
    """
    log = logger or logging.getLogger("serpapi_collector")

    if not OPENAI_AVAILABLE or not api_key:
        log.debug("DeepSeek SDK/Key 不可用，走 fallback 规则")
        result = fallback_clean_lead(title, snippet, source_platform)
        return result

    try:
        client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1",
        )
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是严格的JSON输出器，只输出符合要求的JSON，不要多余字符。"},
                {"role": "user", "content": CLEAN_PROMPT.format(
                    title=title or "(无标题)",
                    snippet=snippet or "(无摘要)",
                    source_platform=source_platform,
                )},
            ],
            temperature=0.2,
            max_tokens=600,
            response_format={"type": "json_object"},
            timeout=15,
        )
        import json
        content = resp.choices[0].message.content or ""
        result = json.loads(content)

        # 校验字段完整性，缺啥用规则补
        for key in ["category", "priority", "user_tier", "city", "content_summary",
                    "ai_relevant", "ai_user_tier", "ai_issue_type", "ai_confidence"]:
            if key not in result or result[key] is None:
                fb = fallback_clean_lead(title, snippet, source_platform)
                result[key] = fb[key]

        result["cleaned_by"] = "deepseek"
        log.debug("DeepSeek 清洗成功：category=%s priority=%s conf=%s",
                  result.get("category"), result.get("priority"), result.get("ai_confidence"))
        return result

    except Exception as exc:
        log.warning("DeepSeek 清洗失败（%s），降级走 fallback 规则", str(exc)[:60])
        result = fallback_clean_lead(title, snippet, source_platform)
        return result


# ============================================================
# ★ 线索 → 标准工单映射（18字段 Schema）★
# ============================================================

def build_workorder_from_lead(
    lead: Dict[str, Any],
    clean_result: Dict[str, Any],
    workorder_seq: int,
) -> Dict[str, Any]:
    """
    按 18 字段 Schema 构造标准工单：
    - feedback_id: FB-YYYYMMDD-Sxxxx（S前缀=舆情采集）
    - channel: 统一 social_media
    - 其余字段来自 clean_result + lead 原文
    """
    today = datetime.now().strftime("%Y%m%d")
    # feedback_id 格式：FB-YYYYMMDD-S + 4位序号（S 表示舆情采集来源）
    feedback_id = f"FB-{today}-S{workorder_seq:04d}"

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    workorder = {}
    for field in WORKORDER_SCHEMA_FIELDS:
        workorder[field] = ""

    workorder["feedback_id"] = feedback_id
    workorder["channel"] = "social_media"  # ★ source_platform 统一映射
    workorder["user_tier"] = clean_result.get("user_tier", "收件人")
    workorder["category"] = clean_result.get("category", "体验")
    workorder["priority"] = clean_result.get("priority", "P2")
    workorder["status"] = "待处理"  # 舆情采集新工单默认待处理
    workorder["vehicle_id"] = ""   # 舆情原文一般不含车牌，留空
    workorder["city"] = clean_result.get("city", "")
    # content_raw：拼接标题+摘要+平台+URL，保证信息完整
    raw_parts = []
    if lead.get("title"):
        raw_parts.append(f"【标题】{lead['title']}")
    if lead.get("snippet"):
        raw_parts.append(f"【内容】{lead['snippet']}")
    raw_parts.append(f"【来源】{lead.get('source_platform', '社交媒体')} 公开舆情")
    if lead.get("url"):
        raw_parts.append(f"【链接】{lead['url']}")
    workorder["content_raw"] = "\n".join(raw_parts)
    workorder["content_summary"] = clean_result.get("content_summary", "")
    workorder["created_at"] = now_str
    workorder["closed_at"] = ""   # 新工单默认未闭环
    workorder["assigned_to"] = ""  # 由飞书自动化分派
    workorder["csat_score"] = ""   # 舆情采集没有满意度，空
    workorder["contact_name"] = ""  # 舆情采集一般无联系方式，空
    workorder["contact_phone"] = ""
    workorder["contact_allowed"] = ""
    workorder["location_detail"] = ""

    return workorder


# ============================================================
# 采集：SerpAPI 真实搜索
# ============================================================

def search_keyword(
    serpapi_key: str, keyword: str, limit: int,
    platform_label: str = "", logger: Optional[logging.Logger] = None,
) -> List[dict]:
    """搜索单个关键词，带完整日志和耗时统计。"""
    log = logger or logging.getLogger("serpapi_collector")
    params = {
        "engine": "google",
        "q": keyword,
        "hl": "zh-cn",
        "num": limit,
        "api_key": serpapi_key,
    }

    call_start = time.time()
    log.debug("[请求开始] #%d 平台=%s 关键词=%s", stats.total_calls + 1, platform_label, keyword)

    try:
        response = requests.get(SERPAPI_ENDPOINT, params=params, timeout=20)
    except requests.RequestException as exc:
        duration = time.time() - call_start
        err_msg = f"网络请求异常: {exc}"
        log.error("[请求失败] 平台=%s 关键词=%s 耗时=%.2fs 错误=%s",
                  platform_label, keyword[:30], duration, exc)
        stats.record_call(keyword, platform_label, duration, None, 0, error_msg=err_msg)
        return []

    duration = time.time() - call_start
    status_code = response.status_code

    try:
        data = response.json()
    except ValueError:
        err_msg = f"返回内容不是合法 JSON，HTTP {status_code}"
        log.error("[请求失败] 平台=%s 关键词=%s 耗时=%.2fs HTTP=%d %s",
                  platform_label, keyword[:30], duration, status_code, err_msg)
        stats.record_call(keyword, platform_label, duration, status_code, 0, error_msg=err_msg)
        return []

    if "error" in data:
        error_text = str(data["error"])
        rate_limited = any(kw in error_text.lower() for kw in [
            "rate limit", "too many", "quota", "exceeded", "throttl", "429",
            "频率", "限流", "配额", "超限",
        ])
        level = logging.WARNING if rate_limited else logging.ERROR
        log.log(level, "[%s] 平台=%s 关键词=%s 耗时=%.2fs HTTP=%d 错误=%s",
                "被限流" if rate_limited else "API错误",
                platform_label, keyword[:30], duration, status_code, error_text[:120])
        stats.record_call(keyword, platform_label, duration, status_code, 0,
                          error_msg=error_text, rate_limited=rate_limited)
        if rate_limited:
            wait_s = random.uniform(5, 10)
            log.warning("触发频率限制，额外等待 %.1f 秒后继续...", wait_s)
            time.sleep(wait_s)
        return []

    if status_code != 200:
        err_msg = f"HTTP {status_code}"
        log.warning("[HTTP异常] 平台=%s 关键词=%s 耗时=%.2fs HTTP=%d",
                    platform_label, keyword[:30], duration, status_code)
        stats.record_call(keyword, platform_label, duration, status_code, 0, error_msg=err_msg)
        return []

    results = data.get("organic_results", [])
    results_count = len(results)
    log.info("[请求成功] #%d 平台=%s 关键词=%s 耗时=%.2fs 结果=%d条 HTTP=%d",
             stats.total_calls + 1, platform_label, keyword[:30], duration, results_count, status_code)
    stats.record_call(keyword, platform_label, duration, status_code, results_count)
    return results


def build_lead(index: int, platform_key: str, keyword: str,
               result: dict, collected_at: str) -> Optional[dict]:
    url = result.get("link", "").strip()
    if not url:
        return None

    today = datetime.now().strftime("%Y%m%d")
    return {
        "lead_id": f"LEAD-{today}-{index:04d}",
        "source_platform": detect_source_platform(url, platform_key),
        "keyword": keyword,
        "title": result.get("title", "").strip(),
        "snippet": result.get("snippet", "").strip(),
        "url": url,
        "collected_at": collected_at,
        "ai_relevant": "",
        "ai_user_tier": "",
        "ai_issue_type": "",
        "ai_confidence": "",
        "review_status": "待复核",
        "review_note": "",
    }


def collect_leads_real(
    serpapi_key: str, platform: str, limit: int,
    min_interval: float, max_interval: float,
    logger: Optional[logging.Logger] = None,
) -> List[dict]:
    """真实采集：通过 SerpAPI 搜索"""
    log = logger or logging.getLogger("serpapi_collector")
    selected_keywords = get_selected_keywords(platform)
    total_keywords = len(selected_keywords)
    leads = []
    seen_urls = set()

    log.info("开始真实采集，共 %d 个关键词，每词最多 %d 条，请求间隔 %.1f~%.1f 秒",
             total_keywords, limit, min_interval, max_interval)

    for keyword_index, (platform_key, keyword) in enumerate(selected_keywords, start=1):
        platform_label = PLATFORM_LABELS.get(platform_key, platform_key)
        log.info("─── [%d/%d] 平台=%s 关键词=%s", keyword_index, total_keywords, platform_label, keyword)

        results = search_keyword(
            serpapi_key=serpapi_key, keyword=keyword, limit=limit,
            platform_label=platform_label, logger=log,
        )
        added_count = 0
        skipped_dup = 0
        collected_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for result in results:
            if added_count >= limit:
                break

            url = result.get("link", "").strip()
            if not url:
                continue
            if url in seen_urls:
                skipped_dup += 1
                continue

            lead = build_lead(
                index=len(leads) + 1, platform_key=platform_key,
                keyword=keyword, result=result, collected_at=collected_at,
            )
            if lead is None:
                continue

            seen_urls.add(url)
            leads.append(lead)
            added_count += 1

        log.info("结果：新增 %d 条，去重跳过 %d 条，累计线索 %d 条",
                 added_count, skipped_dup, len(leads))

        if keyword_index < total_keywords:
            sleep_s = random.uniform(min_interval, max_interval)
            log.debug("等待 %.1f 秒后继续下一个关键词...", sleep_s)
            time.sleep(sleep_s)

    return leads


def collect_leads_mock(limit: int, logger: Optional[logging.Logger] = None) -> List[dict]:
    """
    Mock 模式：生成仿真线索（无需联网/无需API Key）。
    用于演示采集→清洗→双输出完整流程。
    """
    log = logger or logging.getLogger("serpapi_collector")
    log.info("🛠️  Mock 模式：生成仿真线索，不调用真实 SerpAPI")

    mock_templates = [
        ("小红书", "无人车在小区挡路引争议",
         "今天路过小区门口被新石器无人车堵了整整5分钟，轮椅都过不去，希望能管管"),
        ("微博", "无人配送车柜门打不开取件失败",
         "顺丰无人车送到楼下了，输了三次取件码柜门就是不开，客服也打不通，急死"),
        ("知乎", "如何评价新石器无人车的配送体验？",
         "下雨天无人车速度特别慢，晚了20分钟才到，不过能理解就是了。大家觉得这车体验怎样？"),
        ("黑猫投诉", "无人配送车剐蹭电动车后未停留",
         "投诉新石器无人车！今天在路口跟我骑的电动车剐蹭了，车没停直接走了，人摔伤了手"),
        ("小红书", "建议无人车增加保温格放生鲜",
         "无人车夏天送蛋糕怕化，建议商家出保温选项，我愿意加钱。"),
        ("微博", "无人车半夜提示音太响扰民",
         "楼下小区凌晨1点还在跑无人车，提示音贼大，投诉了好几次没用。"),
        ("知乎", "无人配送车监管合规问题",
         "请问大家所在城市的无人车都报备了吗？我们这边好像很多车没报备就在跑。"),
        ("黑猫投诉", "包裹在无人车里放了一天生鲜变质",
         "投诉新石器！昨天上午显示到达，下午才通知我取，打开冰淇淋都化了！"),
        ("小红书", "无人车急刹吓到小孩",
         "今天带孩子在小区散步，无人车突然急刹停在旁边，孩子被吓哭了。"),
        ("微博", "无人网点接驳车班次不准时",
         "网点接驳的无人车经常迟到，今天等到上午10点才来，派件全耽误了。"),
    ]

    leads = []
    today = datetime.now().strftime("%Y%m%d")
    count = min(limit * 3, len(mock_templates))
    collected_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for i in range(count):
        platform, title, snippet = mock_templates[i]
        leads.append({
            "lead_id": f"LEAD-{today}-{i+1:04d}",
            "source_platform": platform,
            "keyword": "(mock 仿真数据)",
            "title": title,
            "snippet": snippet,
            "url": f"https://mock.example.com/lead/{today}/{i+1}",
            "collected_at": collected_at,
            "ai_relevant": "",
            "ai_user_tier": "",
            "ai_issue_type": "",
            "ai_confidence": "",
            "review_status": "待复核",
            "review_note": "",
        })

    log.info("🛠️  Mock 模式完成：生成 %d 条仿真线索", len(leads))
    return leads


# ============================================================
# CSV 写入 & 主流程
# ============================================================

def write_csv(output_path: Path, rows: List[dict], fieldnames: List[str]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()

    if args.limit <= 0:
        print("--limit 必须大于 0。")
        return
    if args.min_interval < 0 or args.max_interval < args.min_interval:
        print("--min-interval 和 --max-interval 参数不合法。")
        return

    logger = setup_logger()
    project_root = get_project_root()
    output_dir = project_root / "data" / "output"

    logger.info("运行参数: mock=%s, skip_clean=%s, dry_run=%s, platform=%s, limit=%d",
                args.mock, args.skip_clean, args.dry_run, args.platform, args.limit)

    # ============================================================
    # 第一步：采集线索（真实 SerpAPI 或 Mock）
    # ============================================================
    leads: List[dict] = []

    if args.mock:
        leads = collect_leads_mock(limit=args.limit, logger=logger)
    else:
        serpapi_key = load_serpapi_key(project_root)
        if serpapi_key is None:
            logger.warning("真实模式未配置 SERPAPI_KEY，自动降级为 --mock 演示模式")
            leads = collect_leads_mock(limit=args.limit, logger=logger)
        else:
            leads = collect_leads_real(
                serpapi_key=serpapi_key, platform=args.platform, limit=args.limit,
                min_interval=args.min_interval, max_interval=args.max_interval,
                logger=logger,
            )

    session_duration = time.time() - 0  # 简化
    if not args.mock:
        summary_text = stats.summary()
        logger.info(summary_text)

    logger.info("采集完成！总线索数: %d 条", len(leads))

    if not leads:
        logger.warning("没有采集到任何线索，流程结束。")
        return

    # ============================================================
    # 第二步：输出 leads_raw.csv（人工复核用）
    # ============================================================
    leads_raw_path = output_dir / "public_opinion_leads_raw.csv"

    if args.dry_run:
        print("\n=== 🎬 dry-run 预览：线索 (leads_raw) ===")
        for lead in leads[:10]:
            print(f"  {lead['lead_id']} | {lead['source_platform']:6s} | "
                  f"{lead['title'][:40]} | {lead['url'][:60]}")
        if len(leads) > 10:
            print(f"  ... 共 {len(leads)} 条，省略其余 {len(leads)-10} 条")
        logger.info("dry-run 模式：跳过写入 CSV")
    else:
        write_csv(leads_raw_path, leads, LEADS_RAW_FIELDS)
        logger.info("✅ 已写入线索CSV（人工复核用）：%s", leads_raw_path)

    # ============================================================
    # 第三步（可选，--skip-clean 时跳过）：AI 清洗 → 标准工单 workorders.csv
    # ============================================================
    if args.skip_clean:
        logger.info("ℹ️  --skip-clean 模式：跳过 AI 清洗工单步骤，结束。")
        print("\n完成！输出：")
        print(f"  线索复核用 CSV：{leads_raw_path if not args.dry_run else '(dry-run 未写入)'}")
        return

    logger.info("🤖 开始 AI 清洗：%d 条线索 → 标准工单", len(leads))
    deepseek_key = load_deepseek_key(project_root)
    if not deepseek_key:
        logger.warning("未配置 DEEPSEEK_API_KEY，全部走 fallback 规则系统进行清洗")

    workorders: List[dict] = []
    seq_counter = 1  # FB-YYYYMMDD-Sxxxx 中的 4 位序号

    for idx, lead in enumerate(leads, start=1):
        clean_result = deepseek_clean_lead(
            title=lead.get("title", ""),
            snippet=lead.get("snippet", ""),
            source_platform=lead.get("source_platform", ""),
            api_key=deepseek_key or "",
            logger=logger,
        )

        # 同步回填线索的 AI 字段（写回 leads_raw）
        lead["ai_relevant"] = clean_result.get("ai_relevant", "")
        lead["ai_user_tier"] = clean_result.get("ai_user_tier", "")
        lead["ai_issue_type"] = clean_result.get("ai_issue_type", "")
        lead["ai_confidence"] = clean_result.get("ai_confidence", "")

        # 只把 AI 判断为相关/待确认的线索转为工单（完全不相关的跳过）
        if clean_result.get("ai_relevant") == "否":
            lead["review_status"] = "AI已忽略"
            lead["review_note"] = f"AI判断不相关({clean_result.get('ai_confidence','')})"
            logger.debug("线索 %s 被 AI 判断为不相关，跳过工单生成", lead["lead_id"])
            continue

        workorder = build_workorder_from_lead(lead, clean_result, seq_counter)
        workorders.append(workorder)
        seq_counter += 1

        if idx % 5 == 0 or idx == len(leads):
            logger.info("清洗进度: %d/%d（已生成 %d 条工单）", idx, len(leads), len(workorders))

    # ============================================================
    # 第四步：双 CSV 输出（回填了 AI 字段的 leads_raw + 标准工单 workorders）
    # ============================================================
    workorders_path = output_dir / "public_opinion_workorders.csv"

    if args.dry_run:
        print("\n=== 🎬 dry-run 预览：标准工单 (workorders) ===")
        for w in workorders[:8]:
            print(f"  {w['feedback_id']} | {w['priority']:2s} | {w['category']:2s} | "
                  f"{w['user_tier']:4s} | {w['city'] or '未知城市':4s} | "
                  f"{w['content_summary'][:40]}")
        if len(workorders) > 8:
            print(f"  ... 共 {len(workorders)} 条工单，省略其余 {len(workorders)-8} 条")
        logger.info("dry-run 模式：工单 CSV 未写入")
    else:
        # 回填了 AI 字段后重新写一次 leads_raw
        write_csv(leads_raw_path, leads, LEADS_RAW_FIELDS)
        logger.info("✅ 已回填 AI字段并更新线索CSV：%s", leads_raw_path)

        write_csv(workorders_path, workorders, WORKORDER_SCHEMA_FIELDS)
        logger.info("✅ 已写入标准工单CSV（18字段Schema）：%s", workorders_path)

    # ============================================================
    # 打印总结
    # ============================================================
    print("\n" + "=" * 70)
    print("🎉 舆情采集 + AI 清洗流程完成")
    print("=" * 70)
    print(f"  采集线索总数：          {len(leads)} 条")
    if not args.mock:
        print(f"  SerpAPI调用次数：      {stats.total_calls} 次")
        print(f"  成功率：               {(stats.success_calls/max(stats.total_calls,1)*100):.1f}%")
    print(f"  AI清洗后生成工单总数： {len(workorders)} 条")
    print(f"  AI过滤（不相关）：     {len(leads)-len(workorders)} 条")
    print()
    print("  输出文件：")
    if args.dry_run:
        print(f"    (dry-run 模式，未写入文件)")
    else:
        print(f"    ① 线索复核用 CSV → {leads_raw_path}")
        print(f"       用途：人工复核 AI 判断结果，调整 review_status / review_note")
        print(f"    ② 标准工单 CSV   → {workorders_path}")
        print(f"       用途：列顺序=WORKORDER_SCHEMA_FIELDS，可直接 import_csv_to_bitable.py 导入多维表格")
    print("=" * 70)


if __name__ == "__main__":
    main()
