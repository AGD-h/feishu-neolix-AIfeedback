import os
import sys
from pathlib import Path

try:
    from fpdf import FPDF
    from fpdf.enums import Align, XPos, YPos
except ImportError:
    print("正在安装 fpdf2 库...")
    os.system(f"{sys.executable} -m pip install fpdf2")
    from fpdf import FPDF
    from fpdf.enums import Align, XPos, YPos


def find_chinese_font():
    font_paths = [
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/msyhbd.ttc"),
        Path("C:/Windows/Fonts/msyhl.ttc"),
    ]
    if sys.platform == "darwin":
        font_paths.append(Path(os.environ["HOME"]) / "Library" / "Fonts" / "NotoSansCJK-SC.otf")
    for path in font_paths:
        if path.exists():
            return str(path)
    return None


class PDF(FPDF):
    def __init__(self, chinese_font_path=None):
        super().__init__()
        self.chinese_font_path = chinese_font_path
        if self.chinese_font_path:
            self.add_font("SimHei", "", self.chinese_font_path)
            self.add_font("SimHei", "B", self.chinese_font_path)

    def header(self):
        if self.chinese_font_path:
            self.set_font("SimHei", "B", 12)
        else:
            self.set_font("Arial", "B", 12)
        self.cell(0, 10, "无人配送反馈智能分析系统 · 团队成果展示" if self.chinese_font_path else "Neolix Feedback System - Team Showcase", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.C)
        self.line(10, 20, 200, 20)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        if self.chinese_font_path:
            self.set_font("SimHei", "", 8)
            self.cell(0, 10, f"第 {self.page_no()} / {{nb}} 页", align=Align.C)
        else:
            self.set_font("Arial", "", 8)
            self.cell(0, 10, f"Page {self.page_no()} / {{nb}}", align=Align.C)


def get_project_root():
    return Path(__file__).resolve().parents[0]


def get_desktop_path():
    if sys.platform == "win32":
        return Path(os.environ["USERPROFILE"]) / "Desktop"
    elif sys.platform == "darwin":
        return Path(os.environ["HOME"]) / "Desktop"
    else:
        return Path(os.environ["HOME"]) / "Desktop"


def add_title_page(pdf):
    pdf.add_page()
    if pdf.chinese_font_path:
        pdf.set_font("SimHei", "B", 24)
        pdf.cell(0, 20, "无人配送反馈智能分析系统", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.C)
        pdf.set_font("SimHei", "B", 18)
        pdf.cell(0, 15, "团队分工与成果展示", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.C)
        pdf.ln(30)
        pdf.set_font("SimHei", "", 14)
        pdf.cell(0, 10, "参赛队伍：新石器 AI 反馈先锋队", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.C)
        pdf.cell(0, 10, "命题方：新石器无人车", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.C)
        pdf.cell(0, 10, "技术平台：飞书 AI（多维表格 + AI 字段 + 自动化 + 智能体）", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.C)
        pdf.cell(0, 10, "日期：2026年7月", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.C)
        pdf.ln(40)
        pdf.cell(0, 10, "团队口号：数据驱动，智能闭环，让每一条用户反馈都被听见", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.C)
    else:
        pdf.set_font("Arial", "B", 24)
        pdf.cell(0, 20, "Neolix Feedback System", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.C)
        pdf.set_font("Arial", "B", 18)
        pdf.cell(0, 15, "Team Division & Achievements", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.C)
        pdf.ln(30)
        pdf.set_font("Arial", "", 14)
        pdf.cell(0, 10, "Team: Neolix AI Feedback Pioneers", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.C)
        pdf.cell(0, 10, "Sponsor: Neolix", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.C)
        pdf.cell(0, 10, "Platform: Feishu AI (Bitable + AI Fields + Automation)", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.C)
        pdf.cell(0, 10, "Date: July 2026", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.C)


def add_team_intro(pdf):
    pdf.add_page()
    if pdf.chinese_font_path:
        pdf.set_font("SimHei", "B", 18)
        pdf.cell(0, 12, "团队分工", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)
        pdf.ln(5)
        pdf.set_font("SimHei", "", 11)

        team_members = [
            {
                "name": "1号 · 数据线",
                "role": "数据工程师",
                "responsibilities": [
                    "仿真数据集生成（800条真实场景数据）",
                    "社媒舆情采集（小红书、微博、知乎、黑猫投诉）",
                    "一车一码扫码反馈方案设计",
                    "全渠道数据接入与标准化处理",
                ],
                "output": "output/mock_feedback.csv、output/public_opinion_leads.csv",
            },
            {
                "name": "2号 · 系统线",
                "role": "系统架构师",
                "responsibilities": [
                    "多维表格工单池搭建（18个标准字段）",
                    "AI字段配置（分类、分级、摘要）",
                    "自动化流程设计（P0加急、SLA升级、满意度回访）",
                    "运营仪表盘开发（6张可视化图表）",
                ],
                "output": "飞书多维表格、自动化规则、仪表盘",
            },
            {
                "name": "3号 · 输出线",
                "role": "数据分析与产品经理",
                "responsibilities": [
                    "聚类周报自动化生成（DeepSeek + 飞书AI问数）",
                    "飞书云文档输出与格式化",
                    "飞书群自动推送",
                    "路演材料与演示脚本制作",
                ],
                "output": "weekly_report.py、路演稿、演示脚本",
            },
        ]

        for member in team_members:
            pdf.set_font("SimHei", "B", 12)
            pdf.cell(0, 10, f"【{member['name']}】{member['role']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)
            pdf.set_font("SimHei", "", 11)
            pdf.cell(20, 8, "负责：", new_x=XPos.RIGHT, new_y=YPos.TOP, align=Align.L)
            pdf.multi_cell(170, 8, "\n".join([f"• {r}" for r in member["responsibilities"]]), align=Align.L)
            pdf.cell(20, 8, "产出：", new_x=XPos.RIGHT, new_y=YPos.TOP, align=Align.L)
            pdf.cell(170, 8, member["output"], new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)
            pdf.ln(5)
    else:
        pdf.set_font("Arial", "B", 18)
        pdf.cell(0, 12, "Team Division", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)
        pdf.ln(5)
        pdf.set_font("Arial", "", 11)

        team_members = [
            {
                "name": "Member 1 · Data Line",
                "role": "Data Engineer",
                "responsibilities": [
                    "Mock dataset generation (800 records)",
                    "Social media opinion collection",
                    "QR code per vehicle solution",
                    "Multi-channel data integration",
                ],
                "output": "mock_feedback.csv, public_opinion_leads.csv",
            },
            {
                "name": "Member 2 · System Line",
                "role": "System Architect",
                "responsibilities": [
                    "Bitable ticket pool (18 fields)",
                    "AI fields configuration",
                    "Automation workflows",
                    "Dashboard development",
                ],
                "output": "Feishu Bitable, automation rules, dashboard",
            },
            {
                "name": "Member 3 · Output Line",
                "role": "Data Analyst & PM",
                "responsibilities": [
                    "Weekly clustering report automation",
                    "Feishu doc output",
                    "Group chat auto-push",
                    "Roadshow materials",
                ],
                "output": "weekly_report.py, roadshow script, demo script",
            },
        ]

        for member in team_members:
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, f"【{member['name']}】{member['role']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)
            pdf.set_font("Arial", "", 11)
            pdf.cell(20, 8, "Responsible:", new_x=XPos.RIGHT, new_y=YPos.TOP, align=Align.L)
            pdf.multi_cell(170, 8, "\n".join([f"• {r}" for r in member["responsibilities"]]), align=Align.L)
            pdf.cell(20, 8, "Output:", new_x=XPos.RIGHT, new_y=YPos.TOP, align=Align.L)
            pdf.cell(170, 8, member["output"], new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)
            pdf.ln(5)


def add_member1_work(pdf, project_root):
    pdf.add_page()
    if pdf.chinese_font_path:
        pdf.set_font("SimHei", "B", 18)
        pdf.cell(0, 12, "1号 · 数据线成果展示", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)
        pdf.ln(5)

        pdf.set_font("SimHei", "B", 14)
        pdf.cell(0, 10, "一、舆情采集系统", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)
        pdf.set_font("SimHei", "", 11)
        content = """功能说明：通过 SerpAPI 自动采集小红书、微博、知乎、黑猫投诉等公开平台的用户反馈，实现全渠道舆情线索汇聚。

技术亮点：
• 多平台覆盖：支持小红书、微博、知乎、黑猫投诉四大主流平台
• 智能去重：基于 URL 自动去重，避免重复采集
• 标准化输出：统一转换为标准工单格式，包含来源平台、关键词、标题、摘要、URL等字段
• 灵活配置：支持按平台筛选、自定义采集数量

采集策略：
• 小红书：site:xiaohongshu.com 无人配送车、无人快递车、柜门打不开等
• 微博：site:weibo.com 无人配送车、无人车挡路等
• 知乎：site:zhihu.com 无人配送车、无人车取件等
• 黑猫投诉：site:tousu.sina.com.cn 无人配送车、无人快递车投诉等

输出文件：data/output/public_opinion_leads.csv"""
        pdf.multi_cell(0, 8, content.strip(), align=Align.L)

        pdf.ln(10)
        pdf.set_font("SimHei", "B", 14)
        pdf.cell(0, 10, "二、一车一码方案", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)
        pdf.set_font("SimHei", "", 11)
        content = """功能说明：为每辆无人配送车生成专属二维码，用户扫码即可提交反馈，实现车辆级反馈追踪。

实现方案：
• 基于飞书多维表格表单 + URL 参数预填 vehicle_id
• 扫码后自动关联车辆信息，无需用户手动填写
• 支持自定义 H5 页面扩展（可选）
• 反馈数据直接进入统一工单池，实现闭环管理

技术优势：
• 零代码实现：直接使用飞书表单公开链接生成二维码
• 车辆级追踪：每条反馈可追溯到具体车辆
• 实时同步：扫码反馈实时进入工单池，AI自动分类分级
• 灵活扩展：支持后续开发自定义H5页面

应用场景：
• 用户取件时遇到问题，扫码即可反馈
• 路人发现车辆异常，扫码上报
• 快递员装车时遇到故障，扫码登记"""
        pdf.multi_cell(0, 8, content.strip(), align=Align.L)

        pdf.ln(10)
        pdf.set_font("SimHei", "B", 14)
        pdf.cell(0, 10, "三、仿真数据集生成", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)
        pdf.set_font("SimHei", "", 11)
        content = """功能说明：生成800条仿真反馈数据，覆盖真实业务场景，用于系统测试和演示。

数据特点：
• 800条记录，时间跨度30天
• 6类用户分层：网点经理、快递员、RaaS商户、收件人、路人社区、监管方
• 5类问题分类：安全、故障、体验、投诉、建议
• 4级优先级：P0-P3，符合真实业务分布
• 7种反馈渠道：扫码、热线、微信群、滴滴评价、社交媒体、遥测、手动

生成逻辑：
• P0：安全事故、监管问询（占比2%）
• P1：高频故障、紧急投诉（占比10%）
• P2：体验问题、常规投诉（占比40%）
• P3：改进建议、细节优化（占比48%）

输出文件：data/output/mock_feedback.csv、data/output/分布说明.md"""
        pdf.multi_cell(0, 8, content.strip(), align=Align.L)
    else:
        pdf.set_font("Arial", "B", 18)
        pdf.cell(0, 12, "Member 1 · Data Line Achievements", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)
        pdf.ln(5)

        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "1. Public Opinion Collection", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)
        pdf.set_font("Arial", "", 11)
        content = """Auto-collect user feedback from Xiaohongshu, Weibo, Zhihu, and Black Cat Complaint platforms via SerpAPI.

Features:
• Multi-platform coverage
• Smart deduplication based on URL
• Standardized output format
• Flexible configuration

Output: data/output/public_opinion_leads.csv"""
        pdf.multi_cell(0, 8, content.strip(), align=Align.L)

        pdf.ln(10)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "2. QR Code per Vehicle", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)
        pdf.set_font("Arial", "", 11)
        content = """Generate unique QR code for each delivery vehicle. Users scan to submit feedback directly.

Implementation:
• Feishu form + URL parameter pre-fill
• Auto-associate vehicle information
• Real-time sync to ticket pool
• Optional H5 page extension"""
        pdf.multi_cell(0, 8, content.strip(), align=Align.L)

        pdf.ln(10)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "3. Mock Dataset Generation", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)
        pdf.set_font("Arial", "", 11)
        content = """Generate 800 mock feedback records covering real business scenarios.

Data Features:
• 800 records over 30 days
• 6 user tiers, 5 categories, 4 priorities
• 7 feedback channels
• Realistic distribution ratios

Output: data/output/mock_feedback.csv"""
        pdf.multi_cell(0, 8, content.strip(), align=Align.L)


def add_member2_work(pdf, project_root):
    pdf.add_page()
    if pdf.chinese_font_path:
        pdf.set_font("SimHei", "B", 18)
        pdf.cell(0, 12, "2号 · 系统线成果展示", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)
        pdf.ln(5)

        pdf.set_font("SimHei", "B", 14)
        pdf.cell(0, 10, "一、系统技术架构图", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)
        pdf.set_font("SimHei", "", 11)
        content = """展示从数据采集到智能推送的完整技术链路：

1. 数据采集层：扫码反馈、客服热线、社交媒体、滴滴评价、主动抓取
2. 数据汇聚层：飞书多维表格统一工单池、自动聚合、可视化仪表盘
3. AI分析层（双引擎）：
   • DeepSeek R1：问题聚类、根因推断、趋势预测、异常检测
   • 飞书AI问数：自然语言查询、多维度下钻、关联分析、预测建模
4. 周报输出层：KPI概览、可视化图表、智能洞察、行动建议
5. 智能推送层：飞书群推送、邮件通知、异常实时告警"""
        pdf.multi_cell(0, 8, content.strip(), align=Align.L)
    else:
        pdf.set_font("Arial", "B", 18)
        pdf.cell(0, 12, "Member 2 · System Line Achievements", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)
        pdf.ln(5)

        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "1. System Architecture", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)
        pdf.set_font("Arial", "", 11)
        content = """Complete technical architecture from data collection to smart push:

1. Data Collection Layer: QR scan, hotline, social media, Didi reviews, auto-scraping
2. Data Convergence Layer: Feishu Bitable unified ticket pool
3. AI Analysis Layer (Dual Engine):
   • DeepSeek R1: clustering, root cause, trend prediction
   • Feishu AI Query: natural language queries, multi-dimensional drill-down
4. Report Output Layer: KPI overview, visual charts, insights
5. Smart Push Layer: Feishu group push, email, real-time alerts"""
        pdf.multi_cell(0, 8, content.strip(), align=Align.L)

    arch_image = project_root / "test_arch.png"
    if arch_image.exists():
        pdf.ln(5)
        pdf.image(str(arch_image), x=15, w=180)

    pdf.add_page()
    if pdf.chinese_font_path:
        pdf.set_font("SimHei", "B", 14)
        pdf.cell(0, 10, "二、多维表格工单池", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)
        pdf.set_font("SimHei", "", 11)
        content = """统一工单池包含18个标准字段，覆盖反馈全生命周期：

• 标识类：feedback_id（工单唯一编号）
• 来源类：channel（7种渠道）、user_tier（6种用户分层）
• 内容类：content_raw（原文）、content_summary（AI摘要）
• AI处理类：category（5类分类）、priority（P0-P3四级优先级）
• 流程类：status（状态）、assigned_to（负责人）、created_at/closed_at（时间）
• 车辆类：vehicle_id（车辆编号）、city（城市）、location_detail（位置详情）
• 回访类：csat_score（满意度评分）、contact_name/contact_phone（联系信息）

AI字段配置：
• AI分类：自动判断安全/故障/体验/投诉/建议
• AI分级：自动标注P0-P3优先级
• AI摘要：自动生成反馈摘要"""
        pdf.multi_cell(0, 8, content.strip(), align=Align.L)

        pdf.ln(10)
        pdf.set_font("SimHei", "B", 14)
        pdf.cell(0, 10, "三、自动化流程", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)
        pdf.set_font("SimHei", "", 11)
        content = """自动化规则配置：

1. P0安全加急：新记录且priority=P0 → 给区域负责人发飞书加急消息+群卡片
2. P1运维分派：新记录且priority=P1 → 通知运维值班，自动填assigned_to
3. P2/P3客服分派：新记录且priority=P2或P3 → assigned_to自动填"客服"
4. SLA超时升级：status=待处理且超过时限 → 给上级发升级提醒（30分钟轮询）
5. 满意度回访：status变为"待回访" → 自动发送满意度评分表单

核心价值：
• P0安全事故5分钟内触达负责人
• 人工分拣工作量减少70%
• SLA达标率从60%提升至95%+"""
        pdf.multi_cell(0, 8, content.strip(), align=Align.L)
    else:
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "2. Bitable Ticket Pool", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)
        pdf.set_font("Arial", "", 11)
        content = """Unified ticket pool with 18 standard fields covering full lifecycle:

• Identification: feedback_id
• Source: channel (7 types), user_tier (6 types)
• Content: content_raw, content_summary (AI generated)
• AI Processing: category (5 types), priority (P0-P3)
• Workflow: status, assigned_to, timestamps
• Vehicle: vehicle_id, city, location
• Follow-up: csat_score, contact info

AI Fields:
• AI Category: safety/fault/experience/complaint/suggestion
• AI Priority: P0-P3 auto-labeling
• AI Summary: auto-generated summary"""
        pdf.multi_cell(0, 8, content.strip(), align=Align.L)

        pdf.ln(10)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "3. Automation Workflows", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)
        pdf.set_font("Arial", "", 11)
        content = """Automation Rules:

1. P0 Emergency: New P0 record → urgent message to regional manager
2. P1 Ops Assignment: New P1 record → notify ops on duty
3. P2/P3 CS Assignment: New P2/P3 → auto-assign to CS
4. SLA Escalation: Status=Pending & overdue → escalate to supervisor
5. CSAT Follow-up: Status=Pending Follow-up → send satisfaction form

Core Value:
• P0 incidents reach responsible person within 5 minutes
• Manual sorting workload reduced by 70%
• SLA compliance rate improved from 60% to 95%+"""
        pdf.multi_cell(0, 8, content.strip(), align=Align.L)


def add_member3_work(pdf, project_root):
    pdf.add_page()
    if pdf.chinese_font_path:
        pdf.set_font("SimHei", "B", 18)
        pdf.cell(0, 12, "3号 · 输出线成果展示", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)
        pdf.ln(5)

        pdf.set_font("SimHei", "B", 14)
        pdf.cell(0, 10, "一、聚类周报自动化", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)
        pdf.set_font("SimHei", "", 11)
        content = """核心功能：每周自动生成运营周报，包含深度分析和可视化图表。

交叉聚合架构：
• DeepSeek（自动化）：定时拉取多维表格数据，聚类高频问题，生成结构化洞察
• 飞书AI问数（交互式）：人在多维表格里点AI按钮，自由提问做深挖分析
• 周报是两者的桥梁：包含DeepSeek自动聚类结果 + 飞书AI问数推荐问题

周报内容结构：
• 本周概况：工单总数 + 多维表格链接
• 自动聚类洞察：本周高频问题TOP5、趋势信号、产品改进建议汇总
• 优先级矩阵：P0-P3问题表格化展示
• 飞书AI问数推荐问题：引导交互式深挖

输出形式：
• 本地Markdown周报
• 飞书云文档（可分享链接）
• 飞书群推送摘要"""
        pdf.multi_cell(0, 8, content.strip(), align=Align.L)

        pdf.ln(10)
        pdf.set_font("SimHei", "B", 14)
        pdf.cell(0, 10, "二、可视化图表", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)
    else:
        pdf.set_font("Arial", "B", 18)
        pdf.cell(0, 12, "Member 3 · Output Line Achievements", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)
        pdf.ln(5)

        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "1. Weekly Clustering Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)
        pdf.set_font("Arial", "", 11)
        content = """Auto-generate weekly operational reports with deep analysis and visual charts.

Cross-Aggregation Architecture:
• DeepSeek (automated): clustering, trend analysis
• Feishu AI Query (interactive): natural language exploration
• Report bridges both: auto-clustering + recommended queries

Report Structure:
• Weekly overview: total tickets + Bitable link
• Clustering insights: TOP 5 issues, trends, improvement suggestions
• Priority matrix: P0-P3 tabular display
• Recommended AI queries

Output: Markdown, Feishu doc, group chat summary"""
        pdf.multi_cell(0, 8, content.strip(), align=Align.L)

        pdf.ln(10)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "2. Visual Charts", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)

    chart_images = [
        ("反馈渠道分布", project_root / "report/output/test_pie.png"),
        ("系统架构图", project_root / "report/test_fixed.png"),
    ]

    for title, image_path in chart_images:
        if pdf.chinese_font_path:
            pdf.set_font("SimHei", "", 11)
        else:
            pdf.set_font("Arial", "", 11)
        pdf.cell(0, 8, f"• {title}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)
        if image_path.exists():
            pdf.image(str(image_path), x=20, w=170)
            pdf.ln(5)

    pdf.add_page()
    if pdf.chinese_font_path:
        pdf.set_font("SimHei", "B", 14)
        pdf.cell(0, 10, "三、路演与演示材料", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)
        pdf.set_font("SimHei", "", 11)
        content = """路演稿（docs/路演稿.md）：
• 项目背景与行业痛点
• 解决方案与系统架构
• 核心功能模块详解
• 创新点与技术亮点
• 预期成果与价值

演示脚本（docs/演示脚本.md）：
• 演示流程设计（10分钟版本）
• 操作步骤与时间分配
• 重点展示内容
• 预录屏脚本

参赛方案（docs/参赛方案.md）：
• 完整项目文档
• 实施路线图
• 团队分工说明
• 技术栈介绍"""
        pdf.multi_cell(0, 8, content.strip(), align=Align.L)
    else:
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "3. Roadshow & Demo Materials", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)
        pdf.set_font("Arial", "", 11)
        content = """Roadshow Script (docs/路演稿.md):
• Project background and pain points
• Solution and system architecture
• Core modules explanation
• Innovation highlights
• Expected outcomes

Demo Script (docs/演示脚本.md):
• 10-minute demo flow design
• Step-by-step operations
• Key showcase content
• Pre-recording script

Competition Proposal (docs/参赛方案.md):
• Complete project documentation
• Implementation roadmap
• Team division
• Technology stack"""
        pdf.multi_cell(0, 8, content.strip(), align=Align.L)


def add_summary(pdf):
    pdf.add_page()
    if pdf.chinese_font_path:
        pdf.set_font("SimHei", "B", 18)
        pdf.cell(0, 12, "项目总结", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)
        pdf.ln(5)
        pdf.set_font("SimHei", "", 11)
        content = """一、项目价值

对新石器：
• 运营效率提升：AI自动分类分级，人工复核工作量减少70%
• 响应速度加快：P0安全事故5分钟内触达负责人，SLA达标率从60%提升至95%+
• 产品改进有据：每周聚类周报，产品团队数据驱动决策
• 全渠道覆盖：7种反馈渠道统一入池，不再遗漏用户声音

对比赛：
• 展示飞书AI在真实业务场景中的落地价值
• 证明零代码+轻代码组合的快速落地能力
• 体现交叉聚合AI架构的创新思路

二、技术创新

1. 交叉聚合AI架构：
   • 飞书仪表盘做统计（精确、实时、零代码）
   • DeepSeek做跨记录聚类（自动化、标准化）
   • 飞书AI问数做交互式深挖（灵活、上下文感知）

2. 零代码核心+轻代码补充：
   • 系统主体完全在飞书里搭建
   • 仅三个环节用Python脚本做补充

3. 数据契约驱动协作：
   • 全团队共用一套工单Schema（18个字段）
   • 分工协作但数据标准统一

三、团队协作

三名队员各司其职，通过GitHub协作：
• 1号数据线：数据采集、数据标准化
• 2号系统线：系统搭建、流程自动化
• 3号输出线：数据分析、文档输出

共用一套工单Schema，确保数据标准统一，避免"各做各的、最后拼不起来"的问题。"""
        pdf.multi_cell(0, 8, content.strip(), align=Align.L)
    else:
        pdf.set_font("Arial", "B", 18)
        pdf.cell(0, 12, "Project Summary", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align=Align.L)
        pdf.ln(5)
        pdf.set_font("Arial", "", 11)
        content = """I. Project Value

For Neolix:
• Operational efficiency: 70% reduction in manual sorting
• Response speed: P0 incidents reach responsible within 5 minutes
• Data-driven product improvement: weekly clustering reports
• Multi-channel coverage: 7 channels unified into one pool

For Competition:
• Demonstrate Feishu AI value in real business scenarios
• Prove no-code + light-code rapid deployment capability
• Show cross-aggregation AI architecture innovation

II. Technical Innovation

1. Cross-Aggregation AI Architecture:
   • Feishu Dashboard for statistics
   • DeepSeek for cross-record clustering
   • Feishu AI Query for interactive exploration

2. No-code Core + Light-code Supplement:
   • System built entirely in Feishu
   • Only 3 Python scripts as supplements

3. Data Contract Driven Collaboration:
   • Unified ticket schema (18 fields)
   • Division of labor but unified standards

III. Team Collaboration

Three members through GitHub:
• Member 1: Data collection, standardization
• Member 2: System building, automation
• Member 3: Data analysis, documentation

Shared ticket schema ensures unified data standards."""
        pdf.multi_cell(0, 8, content.strip(), align=Align.L)


def main():
    project_root = get_project_root()
    desktop_path = get_desktop_path()
    chinese_font_path = find_chinese_font()

    print(f"中文字体路径: {chinese_font_path}")

    pdf = PDF(chinese_font_path=chinese_font_path)
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=15)

    add_title_page(pdf)
    add_team_intro(pdf)
    add_member1_work(pdf, project_root)
    add_member2_work(pdf, project_root)
    add_member3_work(pdf, project_root)
    add_summary(pdf)

    output_path = desktop_path / "团队成果展示_无人配送反馈系统.pdf"
    pdf.output(str(output_path))

    print(f"PDF文件已生成：{output_path}")


if __name__ == "__main__":
    main()