# -*- coding: utf-8 -*-
"""
使用python-pptx创建教练沟通会PPTX文件
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pathlib import Path


def add_slide(prs, layout_index):
    """添加幻灯片"""
    slide_layout = prs.slide_layouts[layout_index]
    slide = prs.slides.add_slide(slide_layout)
    return slide


def set_shape_color(shape, rgb):
    """设置形状填充颜色"""
    fill = shape.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(*rgb)
    shape.line.fill.background()


def add_text_box(slide, left, top, width, height, text, font_size=14, 
                 font_color=(0,0,0), bold=False, align=PP_ALIGN.LEFT):
    """添加文本框"""
    txBox = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = txBox.text_frame
    tf.word_wrap = True
    
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.color.rgb = RGBColor(*font_color)
    p.alignment = align
    
    return txBox


def create_presentation():
    """创建演示文稿"""
    # 创建演示文稿 (16:9)
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(5.625)
    
    # ========================================
    # 第1页：封面
    # ========================================
    slide = add_slide(prs, 6)  # 空白布局
    
    # 深蓝色渐变背景（用矩形模拟）
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(10), Inches(5.625))
    set_shape_color(bg, (26, 26, 46))
    
    # 左侧蓝色装饰条
    accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.12), Inches(5.625))
    set_shape_color(accent, (102, 126, 234))
    
    # 主标题
    add_text_box(slide, 0.8, 1.5, 8.4, 1.8, 
                 "依托飞书AI的无人配送\n全渠道用户反馈闭环运营体系",
                 font_size=32, font_color=(255, 255, 255), bold=True, align=PP_ALIGN.CENTER)
    
    # 分隔线
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(3.8), Inches(3.2), Inches(2.4), Inches(0.04))
    set_shape_color(line, (102, 126, 234))
    
    # 副标题
    add_text_box(slide, 0.8, 3.5, 8.4, 0.5, "第一次教练沟通材料",
                 font_size=20, font_color=(160, 174, 192), align=PP_ALIGN.CENTER)
    
    # 队伍信息
    add_text_box(slide, 0.8, 4.4, 8.4, 0.4, "新石器 AI 反馈先锋队 | 2026年8月10日",
                 font_size=14, font_color=(226, 232, 240), align=PP_ALIGN.CENTER)
    
    # ========================================
    # 第2页：战队分工 & 技术栈
    # ========================================
    slide = add_slide(prs, 6)
    
    # 浅灰白背景
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(10), Inches(5.625))
    set_shape_color(bg, (248, 250, 252))
    
    # 左侧装饰条
    accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.08), Inches(5.625))
    set_shape_color(accent, (102, 126, 234))
    
    # 标题
    add_text_box(slide, 0.5, 0.3, 9, 0.6, "1. 战队分工 & 技术栈",
                 font_size=28, font_color=(26, 26, 46), bold=True)
    
    # 三栏卡片
    card_data = [
        {
            "title": "🚗 1号 · 数据线",
            "modules": ["仿真数据集生成", "社媒舆情采集清洗", "一车一码扫码反馈"],
            "tech": ["Python / pandas", "requests / DeepSeek API", "飞书表单（零代码）"]
        },
        {
            "title": "⚙️ 2号 · 系统线",
            "modules": ["多维表格工单池搭建", "AI字段配置（分类/分级/摘要）", "自动化流程 & 仪表盘"],
            "tech": ["飞书多维表格（零代码）", "飞书AI字段 & 自动化", "飞书仪表盘可视化"]
        },
        {
            "title": "📊 3号 · 输出线",
            "modules": ["聚类周报自动生成", "飞书文档 & 群推送", "路演材料 & 团队PDF"],
            "tech": ["Python / openpyxl", "飞书开放平台API", "markdown / 数据可视化"]
        }
    ]
    
    card_width = 2.9
    card_height = 3.8
    card_gap = 0.35
    start_x = 0.5
    
    for i, card in enumerate(card_data):
        x = start_x + i * (card_width + card_gap)
        y = 1.2
        
        # 卡片背景
        card_bg = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), 
                                         Inches(card_width), Inches(card_height))
        set_shape_color(card_bg, (255, 255, 255))
        card_bg.line.color.rgb = RGBColor(226, 232, 240)
        card_bg.line.width = Pt(1)
        
        # 卡片标题
        add_text_box(slide, x + 0.2, y + 0.2, card_width - 0.4, 0.5, card["title"],
                     font_size=18, font_color=(102, 126, 234), bold=True)
        
        # 负责模块标题
        add_text_box(slide, x + 0.2, y + 0.8, card_width - 0.4, 0.3, "负责模块",
                     font_size=12, font_color=(71, 85, 105), bold=True)
        
        # 模块列表
        module_text = "\n".join([f"▸ {m}" for m in card["modules"]])
        add_text_box(slide, x + 0.2, y + 1.1, card_width - 0.4, 1.2, module_text,
                     font_size=12, font_color=(51, 65, 85))
        
        # 技术栈标题
        add_text_box(slide, x + 0.2, y + 2.3, card_width - 0.4, 0.3, "技术栈",
                     font_size=12, font_color=(71, 85, 105), bold=True)
        
        # 技术栈列表
        tech_text = "\n".join([f"▸ {t}" for t in card["tech"]])
        add_text_box(slide, x + 0.2, y + 2.6, card_width - 0.4, 1.0, tech_text,
                     font_size=12, font_color=(51, 65, 85))
    
    # ========================================
    # 第3页：命题理解 & 落地思路
    # ========================================
    slide = add_slide(prs, 6)
    
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(10), Inches(5.625))
    set_shape_color(bg, (248, 250, 252))
    
    accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.08), Inches(5.625))
    set_shape_color(accent, (102, 126, 234))
    
    add_text_box(slide, 0.5, 0.3, 9, 0.6, "2. 命题理解 & 落地思路",
                 font_size=28, font_color=(26, 26, 46), bold=True)
    
    # 三大痛点
    pain_points = [
        {"num": "7个", "title": "反馈渠道分散", "desc": "运营来回切换\n响应慢、遗漏多"},
        {"num": "70%", "title": "人工分拣效率低", "desc": "时间耗在分类分级\nP0事故易遗漏"},
        {"num": "0条", "title": "反馈无法回流", "desc": "止于工单系统\n产品凭感觉决策"}
    ]
    
    pain_width = 2.8
    pain_start_x = 0.5
    for i, pp in enumerate(pain_points):
        x = pain_start_x + i * (pain_width + 0.25)
        y = 1.1
        
        pain_bg = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y),
                                         Inches(pain_width), Inches(1.3))
        set_shape_color(pain_bg, (254, 243, 199))
        
        # 大数字
        add_text_box(slide, x, y + 0.1, pain_width, 0.6, pp["num"],
                     font_size=40, font_color=(220, 38, 38), bold=True, align=PP_ALIGN.CENTER)
        
        # 描述
        add_text_box(slide, x + 0.1, y + 0.75, pain_width - 0.2, 0.5, pp["desc"],
                     font_size=12, font_color=(120, 53, 15), align=PP_ALIGN.CENTER)
    
    # 核心解决方案
    add_text_box(slide, 0.5, 2.6, 9, 0.4, "💡 核心解决方案：零代码为主，轻代码为辅",
                 font_size=18, font_color=(102, 126, 234), bold=True)
    
    # 架构流程
    arch_steps = ["📥 数据采集层", "🗄️ 数据汇聚层", "🧠 AI分析层", "📤 输出推送层"]
    arch_descs = ["7渠道统一接入", "飞书多维表格工单池", "DeepSeek+飞书AI双引擎", "周报+群推送+告警"]
    step_width = 2.0
    step_start_x = 0.5
    
    for i, (step, desc) in enumerate(zip(arch_steps, arch_descs)):
        x = step_start_x + i * (step_width + 0.3)
        y = 3.2
        
        step_bg = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y),
                                         Inches(step_width), Inches(1.1))
        set_shape_color(step_bg, (219, 234, 254))
        
        add_text_box(slide, x, y + 0.15, step_width, 0.4, step,
                     font_size=14, font_color=(30, 64, 175), bold=True, align=PP_ALIGN.CENTER)
        
        add_text_box(slide, x + 0.1, y + 0.55, step_width - 0.2, 0.4, desc,
                     font_size=10, font_color=(30, 64, 175), align=PP_ALIGN.CENTER)
        
        # 箭头
        if i < len(arch_steps) - 1:
            arrow_x = x + step_width + 0.05
            add_text_box(slide, arrow_x, y + 0.3, 0.2, 0.4, "→",
                         font_size=20, font_color=(102, 126, 234), bold=True, align=PP_ALIGN.CENTER)
    
    # 说明文字
    add_text_box(slide, 0.5, 4.5, 9, 0.6, 
                 "以飞书多维表格为核心载体，工单池、AI字段、自动化、仪表盘零代码搭建；仅仿真数据、舆情清洗、聚类周报三个环节用Python轻代码补充。",
                 font_size=11, font_color=(51, 65, 85))
    
    # ========================================
    # 第4页：当前进度
    # ========================================
    slide = add_slide(prs, 6)
    
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(10), Inches(5.625))
    set_shape_color(bg, (248, 250, 252))
    
    accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.08), Inches(5.625))
    set_shape_color(accent, (102, 126, 234))
    
    add_text_box(slide, 0.5, 0.3, 9, 0.6, "3. 当前进度",
                 font_size=28, font_color=(26, 26, 46), bold=True)
    
    # 已完成（绿色）
    done_bg = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(1.1),
                                     Inches(4.2), Inches(4.2))
    set_shape_color(done_bg, (236, 253, 245))
    
    add_text_box(slide, 0.7, 1.25, 3.8, 0.4, "✅ 已完成",
                 font_size=18, font_color=(5, 150, 105), bold=True)
    
    done_items = [
        "800条仿真数据（7渠道×6分层×5类型）",
        "多维表格工单池搭建（18字段Schema）",
        "AI字段配置（分类/分级/摘要）",
        "聚类周报脚本（DeepSeek+飞书文档）",
        "23个可视化图表",
        "路演稿 + 演示脚本 + 架构图",
        "团队成果展示PDF",
        "代码提交至GitHub",
        "飞书文档/幻灯片生成"
    ]
    done_text = "\n".join([f"✓ {item}" for item in done_items])
    add_text_box(slide, 0.7, 1.7, 3.8, 3.4, done_text,
                 font_size=12, font_color=(6, 78, 59))
    
    # 进行中（橙色）
    progress_bg = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(5.1), Inches(1.1),
                                         Inches(4.4), Inches(1.9))
    set_shape_color(progress_bg, (255, 251, 235))
    
    add_text_box(slide, 5.3, 1.25, 4.0, 0.4, "🔄 进行中",
                 font_size=18, font_color=(217, 119, 6), bold=True)
    
    progress_items = [
        "舆情采集脚本测试优化",
        "一车一码飞书表单配置",
        "系统联调与Demo打磨",
        "教练沟通会准备"
    ]
    progress_text = "\n".join([f"⟳ {item}" for item in progress_items])
    add_text_box(slide, 5.3, 1.7, 4.0, 1.2, progress_text,
                 font_size=12, font_color=(120, 53, 15))
    
    # 待完成（灰色）
    todo_bg = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(5.1), Inches(3.2),
                                     Inches(4.4), Inches(2.1))
    set_shape_color(todo_bg, (249, 250, 251))
    
    add_text_box(slide, 5.3, 3.35, 4.0, 0.4, "📋 待完成",
                 font_size=18, font_color=(107, 114, 128), bold=True)
    
    todo_items = [
        "周报定时任务部署",
        "飞书群推送完整测试",
        "预录视频备份",
        "最终路演彩排"
    ]
    todo_text = "\n".join([f"○ {item}" for item in todo_items])
    add_text_box(slide, 5.3, 3.8, 4.0, 1.4, todo_text,
                 font_size=12, font_color=(55, 65, 81))
    
    # ========================================
    # 第5页：期待教练指导
    # ========================================
    slide = add_slide(prs, 6)
    
    # 蓝紫色渐变背景
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(10), Inches(5.625))
    set_shape_color(bg, (102, 126, 234))
    
    add_text_box(slide, 0.5, 0.3, 9, 0.6, "4. 希望教练重点指导的方向",
                 font_size=28, font_color=(255, 255, 255), bold=True)
    
    # 四个方向卡片
    guide_data = [
        {"icon": "🏗️", "title": "方案架构", "desc": "交叉聚合AI架构（DeepSeek+飞书AI问数）设计是否合理？分工边界是否清晰？"},
        {"icon": "🎬", "title": "演示Demo", "desc": "3分钟Demo如何快速展示完整闭环？哪些是必看亮点？演示顺序如何安排？"},
        {"icon": "💡", "title": "创新亮点", "desc": "\"零代码+轻代码\"如何突出差异化？飞书AI价值如何更好呈现给评委？"},
        {"icon": "📈", "title": "商业价值", "desc": "量化指标（人工分拣降70%、P0响应提速6倍）是否可信？可复用性如何论证？"}
    ]
    
    guide_positions = [
        (0.5, 1.1), (5.1, 1.1), (0.5, 3.0), (5.1, 3.0)
    ]
    
    for i, (guide, pos) in enumerate(zip(guide_data, guide_positions)):
        x, y = pos
        card_bg = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y),
                                         Inches(4.4), Inches(1.6))
        set_shape_color(card_bg, (255, 255, 255))
        
        add_text_box(slide, x + 0.2, y + 0.15, 4.0, 0.4, f"{guide['icon']} {guide['title']}",
                     font_size=18, font_color=(190, 24, 93), bold=True)
        
        add_text_box(slide, x + 0.2, y + 0.6, 4.0, 0.9, guide['desc'],
                     font_size=12, font_color=(131, 24, 67))
    
    # 致谢
    add_text_box(slide, 0.5, 4.9, 9, 0.5, "🙏 感谢教练指导！期待您的宝贵建议",
                 font_size=20, font_color=(255, 255, 255), bold=True, align=PP_ALIGN.CENTER)
    
    # ========================================
    # 保存文件
    # ========================================
    output_path = Path(__file__).parent.parent / "docs" / "教练沟通材料.pptx"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(output_path))
    
    print(f"✅ PPTX文件创建成功！")
    print(f"📄 文件路径: {output_path}")
    print(f"📊 共 {len(prs.slides)} 页幻灯片")
    
    return str(output_path)


if __name__ == "__main__":
    create_presentation()
