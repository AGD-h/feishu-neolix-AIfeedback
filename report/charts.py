# -*- coding: utf-8 -*-
"""
图表生成 + 飞书文档上传模块

功能：
- 生成饼图（分类分布、优先级分布、渠道分布）
- 生成柱状图（城市反馈量 TOP）
- 生成趋势折线图（每日反馈趋势）
- 上传图片到飞书，返回图片 block dict
- 图表配套分析文字生成
"""

import io
import os
import colorsys
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.ticker as mticker
import numpy as np
import requests


# ============================================================
# 中文字体设置
# ============================================================

def _setup_chinese_font() -> None:
    """设置 matplotlib 中文字体，优先使用微软雅黑"""
    font_candidates = [
        "Microsoft YaHei",
        "SimHei",
        "Noto Sans CJK SC",
        "WenQuanYi Micro Hei",
        "Arial Unicode MS",
    ]
    for font_name in font_candidates:
        for f in fm.fontManager.ttflist:
            if font_name.lower() in f.name.lower():
                plt.rcParams["font.family"] = f.name
                return
    plt.rcParams["axes.unicode_minus"] = False


_setup_chinese_font()

# 全局样式：干净、现代，类似飞书仪表盘
plt.rcParams.update({
    "axes.unicode_minus": False,
    "axes.facecolor": "#FAFBFC",
    "figure.facecolor": "white",
    "axes.edgecolor": "#E5E5E5",
    "axes.grid": True,
    "grid.alpha": 0.4,
    "grid.color": "#E8E8E8",
    "axes.labelcolor": "#333333",
    "text.color": "#333333",
    "xtick.color": "#999999",
    "ytick.color": "#999999",
    "font.size": 11,
    "axes.titlesize": 15,
    "axes.titleweight": "bold",
    "axes.labelsize": 11,
})

# 飞书风格调色板
FEISHU_PALETTE = [
    "#3370FF",  # 飞书蓝
    "#00B578",  # 绿色
    "#FF8F1F",  # 橙色
    "#F54C40",  # 红色
    "#8B5CF6",  # 紫色
    "#0EA5E9",  # 天蓝
    "#F59E0B",  # 琥珀
    "#10B981",  # 翠绿
    "#6366F1",  # 靛蓝
    "#EC4899",  # 粉色
]

PRIORITY_COLORS = {
    "P0": "#F54C40",  # 红色
    "P1": "#FF8F1F",  # 橙色
    "P2": "#FACC15",  # 黄色
    "P3": "#00B578",  # 绿色
}


# ============================================================
# 图表生成
# ============================================================

def _save_to_bytes(fig: plt.Figure) -> bytes:
    """统一保存为 PNG 字节"""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    return buf.getvalue()


def generate_trend_line(dates: List[str], values: List[int],
                        title: str = "每日反馈趋势",
                        ylabel: str = "反馈数") -> bytes:
    """生成趋势折线图 — 飞书仪表盘风格（带渐变填充）"""
    fig, ax = plt.subplots(figsize=(12, 5))

    x = np.arange(len(dates))
    color = "#3370FF"  # 飞书蓝

    # 渐变填充
    for i in range(len(values)):
        ax.fill_between(x[i:i+2], values[i:i+2], alpha=0.08 + i * 0.01,
                        color=color, step='mid')

    ax.plot(x, values, color=color, linewidth=2.8, marker='o',
            markersize=8, markerfacecolor='white', markeredgewidth=2.5,
            markeredgecolor=color, zorder=5)

    # 数据标签（只显示高于均值的标签，避免过于密集）
    if values:
        max_val = max(values)
        avg_val = sum(values) / len(values)
        for i, v in enumerate(values):
            if v >= avg_val or v == max_val or v == min(values):
                offset = max_val * 0.06
                ax.text(i, v + offset, str(v), ha='center', fontsize=10,
                        fontweight='bold', color=color)

    # 均值线
    if values:
        avg_val = sum(values) / len(values)
        ax.axhline(y=avg_val, color='#999', linewidth=1, linestyle='--', alpha=0.6)
        ax.text(len(values) - 0.5, avg_val, f'均值 {avg_val:.1f}',
                va='bottom', ha='right', fontsize=8, color='#999')

    # X轴日期标签优化：间隔显示，避免重叠
    ax.set_xticks(x)
    
    # 根据日期数量决定显示策略
    if len(dates) > 15:
        # 日期太多，只显示每隔3个的日期
        visible_indices = x[::3]
        visible_labels = [dates[i] for i in range(len(dates)) if i % 3 == 0]
        ax.set_xticks(visible_indices)
        ax.set_xticklabels(visible_labels, rotation=45, ha='right', fontsize=9)
    else:
        ax.set_xticklabels(dates, rotation=45, ha='right', fontsize=9)
    
    ax.set_ylabel(ylabel, fontsize=10, color='#666')
    ax.set_title(title, fontsize=16, fontweight='bold', pad=12, color='#1A1A1A', loc='left')
    ax.set_ylim(bottom=0, top=max_val * 1.3 if values else 5)
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#E5E5E5')
    ax.spines['bottom'].set_color('#E5E5E5')
    
    plt.tight_layout()

    return _save_to_bytes(fig)


def generate_category_pie(categories: List[str], counts: List[int],
                          title: str = "问题分类分布") -> bytes:
    """生成分类柱状图 — 飞书仪表盘风格（圆角柱、数字在柱顶）"""
    fig, ax = plt.subplots(figsize=(9, 5))

    n = len(categories)
    x = np.arange(n)
    bar_width = 0.55
    color = "#3370FF"  # 飞书蓝

    bars = ax.bar(x, counts, width=bar_width, color=color,
                  edgecolor='none', zorder=3)

    # 数据标签在柱顶
    for bar, val in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(counts) * 0.03 if counts else 0.3,
                str(val), ha='center', va='bottom', fontsize=12,
                fontweight='bold', color='#333')

    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=11, color='#666')
    ax.set_ylabel("计数", fontsize=10, color='#666')
    ax.set_title(title, fontsize=16, fontweight='bold', pad=15, color='#1A1A1A', loc='left')
    ax.set_ylim(bottom=0, top=max(counts) * 1.2 if counts else 5)
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#E5E5E5')
    ax.spines['bottom'].set_color('#E5E5E5')
    ax.grid(axis='y', alpha=0.5, color='#E8E8E8', zorder=0)
    ax.set_axisbelow(True)

    return _save_to_bytes(fig)


def generate_priority_pie(priorities: List[str], counts: List[int],
                          title: str = "优先级分布") -> bytes:
    """生成优先级饼图 — 飞书仪表盘风格"""
    fig, ax = plt.subplots(figsize=(7.5, 5))
    colors = [PRIORITY_COLORS.get(p, "#95A5A6") for p in priorities]

    total = sum(counts) if counts else 1
    explode = []
    for p, cnt in zip(priorities, counts):
        if cnt / total * 100 < 2:
            explode.append(0.3)
        else:
            explode.append(0.02)

    wedges, texts, autotexts = ax.pie(
        counts, labels=None, autopct="%1.1f%%",
        colors=colors, startangle=90,
        pctdistance=0.75, explode=explode,
        wedgeprops={"linewidth": 2, "edgecolor": "white"},
        textprops={"fontsize": 10, "color": "#333"},
    )

    for t in autotexts:
        t.set_fontsize(9)
        t.set_fontweight("bold")
        t.set_color("#333")

    legend_labels = [f"{p}（{n}次）" for p, n in zip(priorities, counts)]
    ax.legend(wedges, legend_labels, loc="center left",
              bbox_to_anchor=(1, 0, 0.5, 1), fontsize=9,
              frameon=False)

    ax.set_title(title, fontsize=15, fontweight='bold', pad=12, color='#1A1A1A')

    return _save_to_bytes(fig)


def generate_channel_pie(channels: List[str], counts: List[int],
                          title: str = "反馈渠道分布") -> bytes:
    """生成渠道分布环形图（甜甜圈）— 飞书仪表盘风格"""
    fig, ax = plt.subplots(figsize=(10, 6))

    total = sum(counts) if counts else 1
    
    # 合并小项（占比 <5% 的合并为"其他"）
    main_channels = []
    main_counts = []
    other_count = 0
    
    for ch, cnt in zip(channels, counts):
        pct = cnt / total * 100
        if pct >= 5:
            main_channels.append(ch)
            main_counts.append(cnt)
        else:
            other_count += cnt
    
    if other_count > 0:
        main_channels.append("其他")
        main_counts.append(other_count)

    # 使用飞书风格多彩配色
    n = len(main_channels)
    colors = FEISHU_PALETTE[:n]

    wedgeprops = dict(width=0.4, edgecolor='white', linewidth=2)

    wedges, texts = ax.pie(
        main_counts, labels=None,
        colors=colors, startangle=90,
        wedgeprops=wedgeprops,
        counterclock=False,
    )

    # 使用 legend 替代自定义标签
    legend_labels = [f"{ch}: {cnt} ({cnt/total*100:.0f}%)" for ch, cnt in zip(main_channels, main_counts)]
    ax.legend(wedges, legend_labels, loc="center left",
              bbox_to_anchor=(1, 0, 0.3, 1), fontsize=10,
              frameon=False, borderaxespad=0)

    ax.set_title(title, fontsize=16, fontweight='bold', pad=15, color='#1A1A1A', loc='left')

    ax.text(0, 0.1, str(total), ha='center', va='center',
            fontsize=28, fontweight='bold', color='#1A1A1A')
    ax.text(0, -0.15, "总反馈数", ha='center', va='center',
            fontsize=10, color='#999')

    return _save_to_bytes(fig)


def generate_top_bar(labels: List[str], values: List[int],
                     title: str = "高频问题 TOP 5",
                     xlabel: str = "出现次数") -> bytes:
    """生成横向柱状图 — 飞书仪表盘风格"""
    fig, ax = plt.subplots(figsize=(9, len(labels) * 0.7 + 2))

    colors = FEISHU_PALETTE[:len(labels)]
    y_pos = np.arange(len(labels))

    bars = ax.barh(y_pos, values, color=colors, height=0.55,
                   edgecolor='white', linewidth=1.5)

    # 数据标签
    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + max(values) * 0.02,
                bar.get_y() + bar.get_height() / 2,
                f"{val}次", va='center', fontsize=10,
                fontweight='bold', color='#333')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel(xlabel, fontsize=10, color='#666')
    ax.set_title(title, fontsize=15, fontweight='bold', pad=12, color='#1A1A1A')
    ax.set_xlim(0, max(values) * 1.25 if values else 1)
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#E5E5E5')
    ax.spines['bottom'].set_color('#E5E5E5')

    return _save_to_bytes(fig)


def generate_architecture_diagram() -> bytes:
    """生成系统技术架构图（飞书风格）

    展示从数据采集到推送的完整技术链路。
    从上到下：采集 → 汇聚 → 分析 → 输出 → 推送
    """
    fig, ax = plt.subplots(figsize=(12, 14))
    ax.set_xlim(0, 12)
    ax.set_ylim(-0.5, 14)
    ax.axis('off')

    blue = "#3370FF"
    green = "#00B96B"
    orange = "#FF7D00"
    purple = "#8658FF"
    text_dark = "#1D2129"
    text_gray = "#4E5969"
    text_light = "#86909C"

    TITLE_LINE_GAP = 0.35
    LINE_CONTENT_GAP = 0.40
    LINE_ITEM_GAP = 0.50
    DUAL_BOX_HEIGHT = 2.0
    ARROW_LENGTH = 0.80
    ARROW_GAP = 0.25

    layers = [
        {
            "title": "数据采集层", "color": blue,
            "desc": "全渠道用户反馈接入",
            "items": ["扫码反馈", "客服热线", "社交媒体", "滴滴评价", "主动抓取"],
            "is_dual": False
        },
        {
            "title": "数据汇聚层", "color": green,
            "desc": "统一工单池 · 实时同步",
            "items": ["飞书多维表格", "统一工单池", "自动聚合", "可视化仪表盘"],
            "is_dual": False
        },
        {
            "title": "AI 分析层", "color": purple,
            "desc": "双引擎交叉聚合分析",
            "is_dual": True,
            "left_title": "DeepSeek R1",
            "left_items": ["问题聚类", "根因推断", "趋势预测", "异常检测"],
            "right_title": "飞书 AI 问数",
            "right_items": ["自然语言查询", "多维度下钻", "关联分析", "预测建模"],
        },
        {
            "title": "周报输出层", "color": blue,
            "desc": "结构化运营周报",
            "items": ["KPI 概览", "可视化图表", "智能洞察", "行动建议"],
            "is_dual": False
        },
        {
            "title": "智能推送层", "color": orange,
            "desc": "多渠道自动触达",
            "items": ["飞书群推送", "邮件通知", "异常实时告警"],
            "is_dual": False
        },
    ]

    layer_info = []
    current_y_line = 12.0

    for layer in layers:
        if layer["is_dual"]:
            content_h = DUAL_BOX_HEIGHT
        else:
            items = layer.get("items", [])
            content_h = max(0.9, len(items) * LINE_ITEM_GAP)

        y_line = current_y_line
        y_title = y_line + TITLE_LINE_GAP
        y_content_top = y_line - LINE_CONTENT_GAP
        y_content_bottom = y_content_top - content_h

        layer_info.append({
            "layer": layer,
            "y_title": y_title,
            "y_line": y_line,
            "y_content_top": y_content_top,
            "y_content_bottom": y_content_bottom,
        })

        current_y_line = y_content_bottom - ARROW_GAP - ARROW_LENGTH - ARROW_GAP

    for info in layer_info:
        layer = info["layer"]
        y_title = info["y_title"]
        y_line = info["y_line"]
        y_content_top = info["y_content_top"]
        color = layer["color"]

        ax.plot(0.6, y_title, 'o', color=color, markersize=12, zorder=5)
        ax.text(1.0, y_title, layer["title"], fontsize=14, fontweight='bold',
                color=text_dark, va='center')
        ax.text(11.4, y_title, layer["desc"], fontsize=10, color=text_light,
                va='center', ha='right')

        ax.plot([0.5, 11.5], [y_line, y_line],
                color=color, linewidth=2.5, solid_capstyle='round', alpha=0.9, zorder=2)

        if layer["is_dual"]:
            box_y_top = y_content_top
            box_h = DUAL_BOX_HEIGHT
            box_w = 5.0

            rect_l = plt.Rectangle((0.8, box_y_top - box_h), box_w, box_h,
                                    facecolor='#F7F3FF', edgecolor=color,
                                    linewidth=1.5, alpha=0.9, zorder=1)
            ax.add_patch(rect_l)
            ax.text(0.8 + box_w/2, box_y_top - 0.3, layer["left_title"],
                    ha='center', va='center', fontsize=12, fontweight='bold',
                    color=text_dark, zorder=3)
            ax.plot([0.8 + 0.4, 0.8 + box_w - 0.4], [box_y_top - 0.7, box_y_top - 0.7],
                    color=color, alpha=0.3, linewidth=1, zorder=2)

            for j, item in enumerate(layer["left_items"]):
                col = j % 2
                row = j // 2
                ix = 0.8 + 0.6 + col * (box_w - 1.2) / 2
                iy = box_y_top - 1.0 - row * 0.5
                ax.text(ix, iy, f"• {item}", fontsize=9.5, color=text_gray,
                        va='center', ha='left', zorder=3)

            rect_r = plt.Rectangle((6.2, box_y_top - box_h), box_w, box_h,
                                    facecolor='#F2F7FF', edgecolor=color,
                                    linewidth=1.5, alpha=0.9, zorder=1)
            ax.add_patch(rect_r)
            ax.text(6.2 + box_w/2, box_y_top - 0.3, layer["right_title"],
                    ha='center', va='center', fontsize=12, fontweight='bold',
                    color=text_dark, zorder=3)
            ax.plot([6.2 + 0.4, 6.2 + box_w - 0.4], [box_y_top - 0.7, box_y_top - 0.7],
                    color=color, alpha=0.3, linewidth=1, zorder=2)

            for j, item in enumerate(layer["right_items"]):
                col = j % 2
                row = j // 2
                ix = 6.2 + 0.6 + col * (box_w - 1.2) / 2
                iy = box_y_top - 1.0 - row * 0.5
                ax.text(ix, iy, f"• {item}", fontsize=9.5, color=text_gray,
                        va='center', ha='left', zorder=3)

        else:
            items = layer["items"]
            card_y_top = y_content_top

            for j, item in enumerate(items):
                iy = card_y_top - 0.35 - j * LINE_ITEM_GAP
                ax.text(0.8, iy, f"• {item}", fontsize=10, color=text_dark,
                        va='center', ha='left', zorder=3)

    for i in range(len(layer_info) - 1):
        y_start = layer_info[i]["y_content_bottom"] - ARROW_GAP
        y_end = layer_info[i+1]["y_line"] + ARROW_GAP
        ax.annotate('', xy=(6, y_end), xytext=(6, y_start),
                    arrowprops=dict(arrowstyle='->', color='#C9CDD4', lw=2.5,
                                    shrinkA=0, shrinkB=0))

    ax.text(6, 13.5, "无人配送反馈智能分析系统 · 技术架构",
            ha='center', fontsize=17, fontweight='bold', color=text_dark)
    ax.text(6, 13.0, "交叉聚合架构  ·  飞书多维表格 + DeepSeek + 飞书 AI 问数",
            ha='center', fontsize=10.5, color=text_gray)

    return _save_to_bytes(fig)


# ============================================================
# 图表分析文字生成
# ============================================================

def build_chart_analysis(stats: Dict[str, Any]) -> List[Tuple[str, str, str, str]]:
    """为每张图表生成配套分析文字（深度版）

    返回: [(图表标题, 数据描述, 逻辑分析, 深度解析), ...]
    """
    analyses = []

    total = stats.get("total", 0)
    if total == 0:
        return analyses

    is_low = total < 3

    # ── 趋势图分析 ──
    daily_trend = stats.get("daily_trend", [])
    if daily_trend:
        dates = [d[0] for d in daily_trend]
        vals = [d[1] for d in daily_trend]
        max_day = dates[vals.index(max(vals))] if vals else ""
        min_day = dates[vals.index(min(vals))] if vals else ""
        avg_val = sum(vals) / len(vals) if vals else 0

        if len(vals) >= 2:
            trend = "上升" if vals[-1] > vals[0] else "下降"
            change = abs(vals[-1] - vals[0])
            trend_desc = f"周环比{trend}{change}条"
        else:
            trend_desc = "数据不足，无法判断趋势"

        if is_low:
            desc = f"⚠️ 样本量仅 {total} 条，趋势分析仅供参考。"
            logic = f"日均 {avg_val:.1f} 条，{trend_desc}。"
            insight = "建议扩大数据采集范围或延长统计周期以获得可靠的趋势判断。"
        else:
            desc = f"本周期共收集 {total} 条反馈，日均 {avg_val:.1f} 条，{trend_desc}。"
            logic = f"峰值日 {max_day}（{max(vals) if vals else 0}条），谷值日 {min_day}（{min(vals) if vals else 0}条），波动幅度 {max(vals) - min(vals) if vals else 0} 条。"
            insight = f"建议排查 {max_day} 是否有运营活动或系统变更触发集中反馈，针对波动规律建立预警阈值。"
        analyses.append(("每日反馈量趋势", desc, logic, insight))

    # ── 分类柱状图分析 ──
    categories = stats.get("categories", {})
    if categories:
        top_cat = list(categories.keys())[0] if categories else "无"
        top_cnt = categories[top_cat]
        top_pct = top_cnt / total * 100 if total > 0 else 0
        cat_total = len(categories)

        if cat_total >= 3:
            top3_pct = sum(list(categories.values())[:3]) / total * 100 if total > 0 else 0
            concentration = "高" if top3_pct > 70 else "中" if top3_pct > 40 else "低"
            desc = f"问题集中在「{top_cat}」（{top_cnt}条，{top_pct:.1f}%），前3类占比 {top3_pct:.1f}%，集中度{concentration}。"
        else:
            desc = f"「{top_cat}」为最主要类别（{top_cnt}条，{top_pct:.1f}%），覆盖 {cat_total} 个类别。"

        if top_pct > 50:
            logic = f"单一类别占比超 50%，说明该领域存在系统性短板，非偶发问题。"
            insight = f"建议启动「{top_cat}」专项治理，从技术/流程/设计三个维度排查根因。"
        else:
            logic = f"类别分布相对分散，{cat_total} 个类别均有关注，不存在严重的单点问题。"
            insight = "建议按影响面排序建立优化路线图，优先解决高频+高影响类别。"
        analyses.append(("问题分类分布", desc, logic, insight))

    # ── 优先级饼图分析 ──
    priorities = stats.get("priorities", {})
    if priorities:
        p0_p1 = priorities.get("P0", 0) + priorities.get("P1", 0)
        p0_p1_pct = p0_p1 / total * 100 if total > 0 else 0

        if p0_p1_pct > 30:
            desc = f"⚠️ P0+P1 高优问题 {p0_p1} 条，占比 {p0_p1_pct:.1f}%，远超 20% 警戒线。"
            logic = f"P0: {priorities.get('P0', 0)}条，P1: {priorities.get('P1', 0)}条。平均每 {total / max(p0_p1, 1):.1f} 条反馈就有 1 条是高优。"
            insight = "立即启动高优问题专项响应，将 P0/P1 处理时长压缩至 2 小时内，同时追查根因防止同类问题重复出现。"
        else:
            desc = f"P0+P1 高优问题 {p0_p1} 条，占比 {p0_p1_pct:.1f}%，处于可控范围。"
            logic = f"大部分为 P2/P3 常规级别，可按正常流程处理。"
            insight = "保持当前分级管理策略，但需持续监控 P0/P1 是否有增长趋势，防范于未然。"
        analyses.append(("优先级分布", desc, logic, insight))

    # ── 渠道环形图分析 ──
    channels = stats.get("channels", {})
    if channels:
        top_ch = list(channels.keys())[0] if channels else "未知"
        top_ch_pct = channels[top_ch] / total * 100 if total > 0 else 0
        ch_count = len(channels)

        desc = f"反馈主要通过「{top_ch}」渠道进入（{top_ch_pct:.1f}%），覆盖 {ch_count} 个渠道。"
        if ch_count >= 2:
            second_ch = list(channels.keys())[1]
            logic = f"前2渠道占总量的 {sum(list(channels.values())[:2]) / total * 100:.1f}%，渠道集中度较高。"
            insight = f"建议在「{top_ch}」和「{second_ch}」渠道部署自动化反馈入口，降低人工录入成本，同时拓展其他渠道覆盖。"
        else:
            logic = "渠道来源单一，可能存在数据采集盲区。"
            insight = "建议拓展扫码反馈、客服热线等渠道，确保全量反馈无遗漏。"
        analyses.append(("反馈渠道分布", desc, logic, insight))

    # ── 城市柱状图分析 ──
    cities = stats.get("cities", {})
    if cities:
        city_sorted = sorted(cities.items(), key=lambda x: x[1], reverse=True)
        top_city = city_sorted[0][0] if city_sorted else "未知"
        top_city_cnt = city_sorted[0][1] if city_sorted else 0
        city_count = len(city_sorted)

        desc = f"「{top_city}」反馈量最高（{top_city_cnt}条），覆盖 {city_count} 个城市。"
        if len(city_sorted) >= 2:
            second = city_sorted[1]
            gap = top_city_cnt - second[1]
            logic = f"与第二名「{second[0]}」差距 {gap} 条，TOP3 城市占总量的 {sum(c[1] for c in city_sorted[:3]) / total * 100:.1f}%。"
        else:
            logic = "城市覆盖有限，当前数据无法反映全量地域差异。"

        if top_city_cnt > total * 0.4:
            insight = f"「{top_city}」反馈占比超 40%，建议优先排查该城市是否存在区域性系统问题（如车辆密集度、道路适配等），同时对比其他城市找出差异根因。"
        else:
            insight = "各城市反馈分布相对均匀，可按反馈量排序建立分城市巡检计划。"
        analyses.append(("城市反馈量 TOP 5", desc, logic, insight))

    return analyses


# ============================================================
# 上传图片到飞书
# ============================================================

UPLOAD_URL = "https://open.feishu.cn/open-apis/drive/v1/medias/upload_all"


def upload_image_to_feishu(
    image_bytes: bytes,
    file_name: str,
    doc_id: str,
    tenant_access_token: str,
) -> Optional[str]:
    """上传图片到飞书，返回 file_token，失败返回 None"""
    headers = {"Authorization": f"Bearer {tenant_access_token}"}
    data = {
        "file_name": file_name,
        "parent_type": "docx_image",
        "parent_node": doc_id,
        "size": len(image_bytes),
    }
    files = {"file": (file_name, io.BytesIO(image_bytes), "image/png")}

    try:
        resp = requests.post(UPLOAD_URL, headers=headers, data=data, files=files, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"❌ 上传图片失败：{exc}")
        return None

    result = resp.json()
    if result.get("code") != 0:
        print(f"❌ 上传图片错误：code={result.get('code')}, msg={result.get('msg')}")
        return None

    return result.get("data", {}).get("file_token")


def make_image_block(image_token: str) -> Dict[str, Any]:
    """构造飞书文档图片 block（block_type=27）"""
    return {
        "block_type": 27,
        "image": {
            "image_token": image_token,
        },
    }


def insert_image_to_doc(
    image_bytes: bytes,
    file_name: str,
    doc_id: str,
    parent_block_id: str,
    tenant_access_token: str,
    index: int = -1,
) -> Optional[str]:
    """完整的图片插入流程：先创建空图片block，再上传图片

    Args:
        image_bytes: 图片二进制数据
        file_name: 文件名
        doc_id: 文档ID
        parent_block_id: 父block的ID（一般是doc_id）
        tenant_access_token: 访问令牌
        index: 插入位置，-1表示追加到末尾

    Returns:
        成功返回图片block的ID，失败返回None
    """
    headers_json = {
        "Authorization": f"Bearer {tenant_access_token}",
        "Content-Type": "application/json",
    }

    # 第一步：创建空图片 block
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{parent_block_id}/children"
    resp = requests.post(
        url,
        headers=headers_json,
        json={
            "children": [
                {"block_type": 27, "image": {}}
            ],
            "index": index,
        },
        timeout=30,
    )
    result = resp.json()
    if result.get("code") != 0:
        print(f"❌ 创建空图片block失败：code={result.get('code')}, msg={result.get('msg')}")
        return None

    children = result.get("data", {}).get("children", [])
    if not children:
        print("❌ 创建图片block后未获取到block_id")
        return None

    image_block_id = children[0]["block_id"]

    # 第二步：上传图片到这个图片 block
    upload_headers = {"Authorization": f"Bearer {tenant_access_token}"}
    upload_data = {
        "file_name": file_name,
        "parent_type": "docx_image",
        "parent_node": image_block_id,
        "size": len(image_bytes),
    }
    upload_files = {"file": (file_name, io.BytesIO(image_bytes), "image/png")}

    resp = requests.post(
        UPLOAD_URL,
        headers=upload_headers,
        data=upload_data,
        files=upload_files,
        timeout=60,
    )
    result = resp.json()
    if result.get("code") != 0:
        print(f"❌ 上传图片失败：code={result.get('code')}, msg={result.get('msg')}")
        return None

    file_token = result.get("data", {}).get("file_token")
    if not file_token:
        print("❌ 上传图片后未获取到 file_token")
        return None

    # 第三步：PATCH 更新图片 block，确认关联
    patch_url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{image_block_id}"
    resp = requests.patch(
        patch_url,
        headers=headers_json,
        json={
            "replace_image": {
                "token": file_token,
            }
        },
        timeout=30,
    )
    patch_result = resp.json()
    if patch_result.get("code") != 0:
        print(f"⚠️ PATCH 更新图片失败：code={patch_result.get('code')}, msg={patch_result.get('msg')}")

    return image_block_id
