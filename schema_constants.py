# ============================================================
# 工单 Schema 常量（全仓库唯一 SSOT = AGENTS.md 第四节）
#
# ⚠️ 任何脚本都不得私自增删字段、改字段顺序、改枚举值！
# ⚠️ 如需改动，必须三名队员一致同意后，只改此文件一处即可全局生效。
#
# 本文件被以下三个脚本共享引用：
#   data/gen_mock_data.py        — 生成仿真CSV时按此顺序排列列名
#   data/search_public_opinion.py — 舆情工单 CSV 列顺序
#   data/import_csv_to_bitable.py — 飞书多维表格写入字段白名单校验
#   report/weekly_report.py       — 读取工单时字段名引用（可选）
# ============================================================

from __future__ import annotations

# ============================================================
# 1. 工单 18 字段 Schema（严格按 AGENTS.md 表格顺序）
#    任何 CSV 输出、飞书字段名必须与此列表完全一致，顺序不可乱
# ============================================================
WORKORDER_SCHEMA_FIELDS: list[str] = [
    "feedback_id",      # 1. 文本 FB-YYYYMMDD-来源前缀+4位序号
    "channel",          # 2. 枚举 7 英文：scan_qr/hotline/wechat_group/didi_review/social_media/telemetry/manual
    "user_tier",        # 3. 枚举 6 中文：网点经理/快递员/RaaS商户/收件人/路人社区/监管方
    "category",         # 4. 枚举 5 中文：安全/故障/体验/投诉/建议
    "priority",         # 5. 枚举 P0/P1/P2/P3
    "status",           # 6. 枚举 待处理/处理中/待回访/已闭环
    "vehicle_id",       # 7. 文本 如 NX-BJ-0233，可为空
    "city",             # 8. 文本 城市名
    "content_raw",      # 9. 长文本 原始反馈内容
    "content_summary",  # 10. 长文本 AI 摘要
    "created_at",       # 11. 日期时间 YYYY-MM-DD HH:MM 精确到分钟
    "closed_at",        # 12. 日期时间 同格式，可为空
    "assigned_to",      # 13. 文本 处理人姓名
    "csat_score",       # 14. 数字 1-5，可为空
    "contact_name",     # 15. 文本 联系人姓名，可为空
    "contact_phone",    # 16. 文本 联系人电话，可为空
    "contact_allowed",  # 17. 单选枚举字符串 "是"/"否"/""（空串=未表态，严禁写True/False）
    "location_detail",  # 18. 文本 位置详情，可为空
]

# 字段总数校验（防止误加漏）
assert len(WORKORDER_SCHEMA_FIELDS) == 18, (
    f"Schema 字段数必须为18（AGENTS.md约定），当前 {len(WORKORDER_SCHEMA_FIELDS)}。"
    f" 字段列表：{WORKORDER_SCHEMA_FIELDS}"
)

# ============================================================
# 2. channel 枚举：7 英文合法值（Schema 要求）
# ============================================================
VALID_CHANNELS: set[str] = {
    "scan_qr",         # 车身扫码（一车一码H5）
    "hotline",         # 客服电话
    "wechat_group",    # 快递网点微信群
    "didi_review",     # 滴滴订单评价
    "social_media",    # 社媒舆情 / 公开数据采集
    "telemetry",       # 车端遥测告警
    "manual",          # 人工录入
}

# ============================================================
# 3. priority 枚举：P0/P1/P2/P3，以及对应的 SLA 响应时间
# ============================================================
VALID_PRIORITIES: set[str] = {"P0", "P1", "P2", "P3"}

PRIORITY_SLA: dict[str, str] = {
    "P0": "5分钟内",    # 安全事故/监管介入
    "P1": "30分钟内",   # 运营中断如车辆趴窝
    "P2": "1小时内",    # 体验问题如取件失败
    "P3": "24小时内",   # 建议咨询
}

# ============================================================
# 4. category → priority 默认映射（Schema 规定）
# ============================================================
VALID_CATEGORIES: set[str] = {"安全", "故障", "体验", "投诉", "建议"}

CATEGORY_PRIORITY_DEFAULT: dict[str, str] = {
    "安全": "P0",
    "故障": "P1",
    "投诉": "P1",
    "体验": "P2",
    "建议": "P3",
}

# ============================================================
# 5. user_tier 枚举：6 中文合法值
# ============================================================
VALID_USER_TIERS: set[str] = {
    "网点经理",
    "快递员",
    "RaaS商户",
    "收件人",
    "路人社区",
    "监管方",
}

# ============================================================
# 6. status 枚举：4 中文合法值
# ============================================================
VALID_STATUSES: set[str] = {"待处理", "处理中", "待回访", "已闭环"}

# ============================================================
# 7. contact_allowed 仅三态（飞书单选字段，严禁写入布尔值）
# ============================================================
VALID_CONTACT_ALLOWED: set[str] = {"是", "否", ""}

# ============================================================
# 8. feedback_id 格式帮助函数
#    FB-YYYYMMDD-来源前缀+4位序号
#    来源前缀：S=舆情  H=扫码  M=仿真/无后缀
# ============================================================
FEEDBACK_ID_PREFIX: dict[str, str] = {
    "social_media": "S",  # 舆情采集
    "scan_qr": "H",       # 车身扫码
    "mock": "M",          # 仿真数据
}


def validate_contact_allowed(val: object) -> str:
    """把任意输入的 contact_allowed 收敛到合法三态，非法值返回空串。"""
    if val in ("是", True, 1, "1", "yes", "YES", "true", "True"):
        return "是"
    if val in ("否", False, 0, "0", "no", "NO", "false", "False"):
        return "否"
    return ""


# ============================================================
# 9. 飞书多维表格「内部英文枚举 ↔ 飞书UI中文选项文本」双向映射（BIMAP）
#    用途：
#      · 写入飞书时（to_bitable_*）：把 Schema 英文枚举转成飞书UI里实际配置的中文选项文本，
#        彻底避免因「中文选项匹配不到英文枚举」落到「无匹配类别」兜底
#      · 读飞书验证时（from_bitable_*）：把飞书UI读出的中文/英文选项统一转回 Schema 标准枚举，
#        保证双向比对时语言一致，不会因中英文差异误报不匹配
#
#    数据来源：scripts/list_bitable_fields.py + scripts/debug_field_options_and_samples.py
#             通过飞书开放 API 真实拉取的字段选项文本（100% 对齐飞书 UI）
# ============================================================

# 9.1 channel：Schema 7 英文 ↔ 飞书UI 7 中文（真实选项13个=中文7+英文6，写入中文最稳）
CHANNEL_TO_BITABLE: dict[str, str] = {
    "scan_qr":       "车身扫码",
    "hotline":       "客服电话",
    "wechat_group":  "微信群",
    "didi_review":   "滴滴评价",
    "social_media":  "社媒舆情",
    "telemetry":     "车端告警",
    "manual":        "人工录入",
}
# 反向：飞书端中文/英文 → Schema 标准英文（中英文都能识别，兼容历史英文字段值）
CHANNEL_FROM_BITABLE: dict[str, str] = {}
for _en, _cn in CHANNEL_TO_BITABLE.items():
    CHANNEL_FROM_BITABLE[_en] = _en   # 英文 → 自己（兼容历史英文写入值）
    CHANNEL_FROM_BITABLE[_cn] = _en   # 中文 → 标准英文

# 9.2 category：Schema 5 中文 ↔ 飞书UI 5 中文（与「无匹配类别」兜底共存，飞书6项）
#      本身全是中文完全一致，做恒等映射，只为统一转换函数接口 + 兼容飞书扩展值
CATEGORY_TO_BITABLE: dict[str, str] = {
    "安全": "安全",
    "故障": "故障",
    "体验": "体验",
    "投诉": "投诉",
    "建议": "建议",
}
CATEGORY_FROM_BITABLE: dict[str, str] = dict(CATEGORY_TO_BITABLE)
# 飞书扩展兜底：「无匹配类别」→ 返回空串（调用方处理宽容）

# 9.3 priority：Schema 4 英文 ↔ 飞书UI 4 英文（与「无匹配类别」兜底共存，飞书5项）
PRIORITY_TO_BITABLE: dict[str, str] = {
    "P0": "P0",
    "P1": "P1",
    "P2": "P2",
    "P3": "P3",
}
PRIORITY_FROM_BITABLE: dict[str, str] = dict(PRIORITY_TO_BITABLE)

# 9.4 user_tier：Schema 6 中文 ↔ 飞书UI 6 中文（飞书另有校园用户/商户/运维/普通用户4个扩展值）
USER_TIER_TO_BITABLE: dict[str, str] = {
    "网点经理": "网点经理",
    "快递员":   "快递员",
    "RaaS商户": "RaaS商户",
    "收件人":   "收件人",
    "路人社区": "路人社区",
    "监管方":   "监管方",
}
USER_TIER_FROM_BITABLE: dict[str, str] = dict(USER_TIER_TO_BITABLE)

# 9.5 status：Schema 4 中文 ↔ 飞书UI 4 中文（完全一致）
STATUS_TO_BITABLE: dict[str, str] = {s: s for s in VALID_STATUSES}
STATUS_FROM_BITABLE: dict[str, str] = dict(STATUS_TO_BITABLE)


# ------------------------------------------------------------
# 转换函数（写入飞书 → 用 to_bitable_*；读飞书验证 → 用 from_bitable_*）
# ------------------------------------------------------------
def to_bitable_channel(internal: str) -> str:
    """Schema 标准英文 channel → 飞书UI中文选项文本（找不到就原样返回）"""
    return CHANNEL_TO_BITABLE.get(str(internal).strip(), str(internal).strip())


def from_bitable_channel(ui_val: str) -> str:
    """飞书端 channel 读出值（中文/英文都可能）→ Schema 标准英文"""
    return CHANNEL_FROM_BITABLE.get(str(ui_val).strip(), str(ui_val).strip())


def to_bitable_category(internal: str) -> str:
    """Schema 中文 category → 飞书UI中文选项文本（恒等映射，接口统一）"""
    return CATEGORY_TO_BITABLE.get(str(internal).strip(), str(internal).strip())


def from_bitable_category(ui_val: str) -> str:
    """飞书端 category 读出值 → Schema 中文（「无匹配类别」直接返回，由上层宽容）"""
    return CATEGORY_FROM_BITABLE.get(str(ui_val).strip(), str(ui_val).strip())


def to_bitable_priority(internal: str) -> str:
    """Schema 英文 priority → 飞书UI选项（恒等映射，接口统一）"""
    return PRIORITY_TO_BITABLE.get(str(internal).strip(), str(internal).strip())


def from_bitable_priority(ui_val: str) -> str:
    """飞书端 priority 读出值 → Schema 英文（「无匹配类别」直接返回，由上层宽容）"""
    return PRIORITY_FROM_BITABLE.get(str(ui_val).strip(), str(ui_val).strip())


def to_bitable_user_tier(internal: str) -> str:
    """Schema 中文 user_tier → 飞书UI中文选项（恒等映射）"""
    return USER_TIER_TO_BITABLE.get(str(internal).strip(), str(internal).strip())


def from_bitable_user_tier(ui_val: str) -> str:
    """飞书端 user_tier 读出值 → Schema 中文（扩展值原样返回，上层做宽容）"""
    return USER_TIER_FROM_BITABLE.get(str(ui_val).strip(), str(ui_val).strip())


def to_bitable_status(internal: str) -> str:
    """Schema 中文 status → 飞书UI中文（恒等映射）"""
    return STATUS_TO_BITABLE.get(str(internal).strip(), str(internal).strip())


# ============================================================
# 9.6 路由分派规则表（答辩演示用，P1 新增功能）
#    目标：把"工单分类完派给谁"这件事，从原来的全靠飞书UI自动化，
#          改成 Python 代码端可解释、可审计的规则路由，评委一眼能懂。
#    设计原则：
#      · Schema 里只存「规则匹配 → 返回 .env 里存储 open_id 的变量名」，
#        绝对不把真实 ou_xxx / on_xxx open_id 写死进仓库（合规+防泄漏）。
#      · 所有规则按优先级顺序匹配，第一个命中就返回。
#      · 如果 .env 里对应 env 变量为空（演示前没填真实 open_id），调用方
#        会直接跳过 assigned_to 写入，保持原来的行为 100% 不变，不破坏历史。
# ============================================================

# 每条规则：(匹配函数 lambda cat,pri,city: bool,  .env环境变量名,  中文说明，仅用于调试打印)
ROUTE_RULES_PRIORITY_FIRST: list[tuple] = [
    # ① 最高优先级：安全 P0 → 不分城市，直接派安全主管
    (lambda cat, pri, c: cat == "安全" and pri == "P0",
     "ROUTE_SAFETY_P0_OPEN_ID",
     "安全P0事故主管（公司级，不分城市）"),
    # ② P1 级故障/投诉 → 按城市派区域运维团队
    (lambda cat, pri, c: pri == "P1" and c in ("北京", "北京市"),
     "ROUTE_OPS_BEIJING_OPEN_ID",
     "北京区域运维P1团队"),
    (lambda cat, pri, c: pri == "P1" and c in ("上海", "上海市"),
     "ROUTE_OPS_SHANGHAI_OPEN_ID",
     "上海区域运维P1团队"),
    (lambda cat, pri, c: pri == "P1" and c in ("深圳", "深圳市", "广州", "广州市"),
     "ROUTE_OPS_SHENZHEN_OPEN_ID",
     "广深区域运维P1团队"),
    (lambda cat, pri, c: pri == "P1" and c in ("杭州", "杭州市", "苏州", "苏州市"),
     "ROUTE_OPS_EAST_OPEN_ID",
     "华东区域运维P1团队（杭州/苏州）"),
    # ③ P1 其他城市 → 派通用运维池
    (lambda cat, pri, c: pri == "P1",
     "ROUTE_OPS_GENERAL_OPEN_ID",
     "通用运维P1池（覆盖其余城市）"),
    # ④ 投诉 → 客服投诉池
    (lambda cat, pri, c: cat == "投诉",
     "ROUTE_CS_TEAM_OPEN_ID",
     "C端投诉客服池"),
    # ⑤ 体验类（扫码失败/找车难等）→ 通用客服池
    (lambda cat, pri, c: cat == "体验",
     "ROUTE_CS_TEAM_OPEN_ID",
     "C端体验客服池"),
    # ⑥ 建议 → 产品经理池
    (lambda cat, pri, c: cat == "建议",
     "ROUTE_PRODUCT_TEAM_OPEN_ID",
     "产品经理池（收集建议）"),
    # ⑦ 其余全部 → 默认池（兜底）
    (lambda cat, pri, c: True,
     "ROUTE_DEFAULT_OPEN_ID",
     "默认分派兜底池"),
]


def route_assignee_env_key(category: str, priority: str, city: str) -> str:
    """根据工单 category/priority/city 匹配路由规则，返回 .env 里 open_id 的变量名。

    调用方需要：
      ① 从 .env 里读取这个 env_key 对应的真实值（ou_xxx / on_xxx 格式 open_id）
      ② 如果 .env 里该变量为空或不存在 → 跳过 assigned_to 写入（行为与原来一致）
      ③ 如果非空 → 写入飞书用户类型字段：assigned_to = [{"id": open_id}]
    """
    cat_str = str(category).strip()
    pri_str = str(priority).strip()
    city_str = str(city).strip()
    for rule_fn, env_key, _note in ROUTE_RULES_PRIORITY_FIRST:
        try:
            if rule_fn(cat_str, pri_str, city_str):
                return env_key
        except Exception:
            # 规则函数报错（比如 lambda 类型异常）就跳过这条规则
            continue
    return ""


def describe_route_rules() -> list[tuple[str, str]]:
    """返回人类可读的路由规则清单（用于答辩演示/调试打印，不包含任何真实 open_id）。"""
    lines: list[tuple[str, str]] = []
    for i, (_fn, env_key, note) in enumerate(ROUTE_RULES_PRIORITY_FIRST, 1):
        lines.append((f"#{i} {note}", env_key))
    return lines


def from_bitable_status(ui_val: str) -> str:
    """飞书端 status 读出值 → Schema 中文"""
    return STATUS_FROM_BITABLE.get(str(ui_val).strip(), str(ui_val).strip())


if __name__ == "__main__":
    # 运行此文件可快速自检 Schema 是否正常
    print("✅ Schema 常量加载成功")
    print(f"  字段数：{len(WORKORDER_SCHEMA_FIELDS)} 个（应为 18）")
    print(f"  channel 枚举：{sorted(VALID_CHANNELS)}")
    print(f"  priority 枚举：{sorted(VALID_PRIORITIES)}")
    print(f"  category 枚举：{sorted(VALID_CATEGORIES)}")
    print(f"  user_tier 枚举：{sorted(VALID_USER_TIERS)}")
    print(f"  status 枚举：{sorted(VALID_STATUSES)}")
    print(f"  contact_allowed 合法值：{VALID_CONTACT_ALLOWED}")
    print("  Schema 字段顺序（可直接复制到 CSV header）：")
    for i, f in enumerate(WORKORDER_SCHEMA_FIELDS, 1):
        print(f"    {i:2d}. {f}")
