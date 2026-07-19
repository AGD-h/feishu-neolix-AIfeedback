# -*- coding: utf-8 -*-
"""
仿真反馈数据集生成脚本（1号 · 数据线）
运行方式：在 data 目录下执行  python gen_mock_data.py
产出：output/mock_feedback.csv 和 output/分布说明.md
不需要联网、不需要 API Key。
"""

import csv
import os
import random
from datetime import datetime, timedelta

# ============ 配置区（想调整就改这里） ============
TOTAL = 800                # 生成条数（500–1000 之间）
DAYS = 30                  # 时间分布在近 N 天
SEED = 42                  # 随机种子，固定后每次生成结果一致，便于复现
OUT_DIR = "output"

# 优先级分布（与 AGENTS.md 一致：P0 极少、P3 最多）
PRIORITY_WEIGHTS = {"P0": 2, "P1": 10, "P2": 40, "P3": 48}

# 用户分层分布（B 端为主，符合新石器业务结构）
USER_TIER_WEIGHTS = {
    "网点经理": 18, "快递员": 27, "RaaS商户": 15,
    "收件人": 25, "路人社区": 12, "监管方": 3,
}

CITIES = ["北京", "石家庄", "青岛", "苏州", "无锡", "天水", "深圳", "杭州", "成都", "武汉"]
NAMES = ["张伟", "李娜", "王强", "刘敏", "陈杰", "赵磊"]  # assigned_to 演示用

# ============ 反馈内容模板 ============
# 结构：(user_tier, category, priority, 原声模板列表)
# 模板依据公开报道的真实痛点编写，口吻按角色区分
TEMPLATES = [
    ("快递员", "故障", "P1", [
        "车到驿站门口柜门打不开，急着派件，卡了快{n}分钟了",
        "无人车半路停在小区门口不动了，后面一车货都在上面",
        "今早车没按时到网点，等到{n}点才来，派件全耽误了",
    ]),
    ("快递员", "体验", "P2", [
        "装货的时候柜格分配不合理，大件塞不进去只能空着跑",
        "app上显示车已到，实际还差两条街，白跑一趟",
        "雨天车速特别慢，比平时晚了{n}分钟，能不能优化下",
    ]),
    ("快递员", "建议", "P3", [
        "建议增加夜间接驳班次，早上到岗就能直接派件",
        "希望车上加个保温格，夏天生鲜件不敢放",
    ]),
    ("网点经理", "故障", "P1", [
        "今天两台车同时趴窝，网点到驿站的接驳全断了，损失不小",
        "车辆充电桩故障，明早的班次跑不了，急需处理",
    ]),
    ("网点经理", "体验", "P2", [
        "大促期间车次不够用，能不能临时加车？上报了{n}天没回音",
        "月租扣费对不上账，多扣了一次，找谁核对？",
    ]),
    ("网点经理", "建议", "P3", [
        "建议给网点开个数据后台，能看每台车每天跑了多少单",
        "希望合同里明确雨雪天停运的责任划分",
    ]),
    ("RaaS商户", "体验", "P2", [
        "下单后等了{n}分钟车才到，比页面预估晚了一倍，急单只能改叫货拉拉",
        "车到了以后找不到具体停哪，电话也没人接，转了两圈才找到",
    ]),
    ("RaaS商户", "投诉", "P2", [
        "扫码开柜失败三次，货卡在车里取不出来，耽误我给客户交货",
        "运费比谈好的贵了，说是里程算法调整，事先没通知",
    ]),
    ("RaaS商户", "建议", "P3", [
        "建议支持预约固定时段用车，我们每天下午都要发一批货",
    ]),
    ("收件人", "体验", "P2", [
        "取件码输了没反应，柜门不开，站在车边上等了{n}分钟",
        "通知说车到楼下了，下去发现车已经开走了",
        "取件的格子太高，老人踮脚都够不着",
    ]),
    ("收件人", "投诉", "P2", [
        "包裹在车里放了一天才通知我取，里面生鲜都坏了",
        "取件时柜门夹了一下手，虽然没受伤但很吓人，要给个说法",
    ]),
    ("收件人", "建议", "P3", [
        "建议取件通知提前十分钟发，不然赶不上车",
    ]),
    ("路人社区", "安全", "P0", [
        "无人车在小区门口跟电动车剐蹭了，骑车人摔倒了，快来处理",
        "车过路口没让行人，差点撞到推婴儿车的，太危险了",
    ]),
    ("路人社区", "体验", "P2", [
        "车停在人行道正中间挡路，轮椅都过不去",
        "半夜车经过提示音太响，吵得没法睡觉",
    ]),
    ("路人社区", "投诉", "P3", [
        "小区里车速有点快，建议限速，孩子多的地方危险",
    ]),
    ("监管方", "安全", "P0", [
        "接群众举报贵司车辆在未报备路段运营，请立即说明情况",
    ]),
    ("监管方", "投诉", "P1", [
        "贵司车辆占用消防通道停放，请24小时内整改并回复",
    ]),
]

CHANNELS = ["scan_qr", "hotline", "wechat_group", "didi_review", "social_media", "telemetry", "manual"]
# 各角色更可能使用的渠道（让数据更真实）
TIER_CHANNEL = {
    "网点经理": ["wechat_group", "hotline", "manual"],
    "快递员": ["wechat_group", "scan_qr", "hotline"],
    "RaaS商户": ["didi_review", "hotline", "scan_qr"],
    "收件人": ["scan_qr", "hotline", "social_media"],
    "路人社区": ["scan_qr", "social_media", "hotline"],
    "监管方": ["manual", "hotline"],
}


def weighted_choice(weights: dict):
    """按权重随机选一个 key"""
    keys = list(weights.keys())
    return random.choices(keys, weights=[weights[k] for k in keys], k=1)[0]


def random_time_in_days(days: int) -> datetime:
    """近 N 天内的随机时间，早晚高峰（8-10、18-20点）概率加倍"""
    day_offset = random.randint(0, days - 1)
    hour_pool = list(range(24)) + [8, 9, 18, 19] * 2  # 高峰时段重复加入，提高概率
    hour = random.choice(hour_pool)
    t = datetime.now() - timedelta(days=day_offset)
    return t.replace(hour=hour, minute=random.randint(0, 59), second=0, microsecond=0)


def make_summary(content: str, category: str) -> str:
    """演示用的简易摘要（正式系统里这一列由飞书 AI 字段生成）"""
    return f"[{category}] " + (content[:30] + "..." if len(content) > 30 else content)


def main():
    random.seed(SEED)
    os.makedirs(OUT_DIR, exist_ok=True)

    # 按目标优先级分布，把模板按 priority 分组
    by_priority = {}
    for tier, cat, pri, texts in TEMPLATES:
        by_priority.setdefault(pri, []).append((tier, cat, texts))

    rows = []
    date_counters = {}  # 每天一个流水号计数器，保证 feedback_id 唯一
    for _ in range(TOTAL):
        pri = weighted_choice(PRIORITY_WEIGHTS)
        tier, cat, texts = random.choice(by_priority[pri])
        # 模板中的 {n} 在时间语境下限制为 5-23（小时），其他语境 5-40
        raw = random.choice(texts)
        if "点" in raw and "{n}" in raw:
            content = raw.replace("{n}", str(random.randint(5, 23)))
        else:
            content = raw.replace("{n}", str(random.randint(5, 40)))

        created = random_time_in_days(DAYS)
        datekey = created.strftime("%Y%m%d")
        date_counters[datekey] = date_counters.get(datekey, 0) + 1
        fid = f"FB-{datekey}-{date_counters[datekey]:04d}"

        # 大部分历史工单已闭环（有 closed_at 和评分），近 3 天的多数还在处理中
        is_recent = (datetime.now() - created).days < 3
        if is_recent and random.random() < 0.6:
            status = random.choice(["待处理", "处理中", "待回访"])
            closed_at, csat = "", ""
        else:
            status = "已闭环"
            close_hours = {"P0": 2, "P1": 8, "P2": 24, "P3": 48}[pri]
            closed = created + timedelta(hours=random.uniform(0.5, close_hours))
            closed_at = closed.strftime("%Y-%m-%d %H:%M")
            csat = random.choices([5, 4, 3, 2, 1], weights=[35, 35, 18, 8, 4], k=1)[0]

        rows.append({
            "feedback_id": fid,
            "channel": random.choice(TIER_CHANNEL[tier]),
            "user_tier": tier,
            "category": cat,
            "priority": pri,
            "status": status,
            "vehicle_id": f"NX-{random.choice(['BJ','SJZ','QD','SZ','TS'])}-{random.randint(1, 500):04d}",
            "city": random.choice(CITIES),
            "content_raw": content,
            "content_summary": make_summary(content, cat),
            "created_at": created.strftime("%Y-%m-%d %H:%M"),
            "closed_at": closed_at,
            "assigned_to": random.choice(NAMES),
            "csat_score": csat,
        })

    # 按时间排序后写 CSV（utf-8-sig 带 BOM，Excel 直接打开不乱码）
    rows.sort(key=lambda r: r["created_at"])
    csv_path = os.path.join(OUT_DIR, "mock_feedback.csv")
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # 输出分布说明，供 docs 归档和路演引用
    stat = lambda key: {v: sum(1 for r in rows if r[key] == v) for v in sorted({r[key] for r in rows})}
    doc_path = os.path.join(OUT_DIR, "分布说明.md")
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write("# 仿真数据集分布说明\n\n")
        f.write(f"共 {len(rows)} 条，时间跨度近 {DAYS} 天，随机种子 {SEED}（可复现）。\n\n")
        f.write("构造依据：公开报道中的真实痛点（柜门故障、取件失败、响应慢、雨天降速、"
                "剐蹭事故、未报备被监管问询等），话术按用户角色区分口吻。\n\n")
        for key, title in [("priority", "优先级"), ("user_tier", "用户分层"),
                           ("category", "类别"), ("channel", "渠道"), ("status", "状态")]:
            f.write(f"## {title}分布\n\n")
            for k, v in stat(key).items():
                f.write(f"- {k}: {v} 条（{v * 100 // len(rows)}%）\n")
            f.write("\n")

    print(f"完成：{csv_path}（{len(rows)} 条）")
    print(f"完成：{doc_path}")


if __name__ == "__main__":
    main()
