# -*- coding: utf-8 -*-
"""
创建教练沟通会飞书幻灯片
"""

import json
import subprocess
import os
import sys
from pathlib import Path


def run_lark_cli(cmd_args, as_user=True):
    """运行lark-cli命令"""
    full_cmd = ["lark-cli"] + cmd_args
    if as_user:
        full_cmd.extend(["--as", "user"])
    
    print(f"执行: {' '.join(full_cmd)}")
    result = subprocess.run(full_cmd, capture_output=True, text=True, encoding='utf-8')
    
    if result.returncode != 0:
        print(f"❌ 命令执行失败: {result.stderr}")
        return None
    
    try:
        # 尝试从输出中提取JSON
        output = result.stdout.strip()
        # 查找JSON开始位置
        json_start = output.find('{')
        if json_start >= 0:
            json_str = output[json_start:]
            return json.loads(json_str)
        return {"raw_output": output}
    except json.JSONDecodeError:
        return {"raw_output": result.stdout}


def create_slide_xml(slide_num):
    """生成第N页的XML"""
    
    # 公共命名空间
    ns = 'xmlns="http://www.larkoffice.com/sml/2.0"'
    
    if slide_num == 1:
        # 封面页
        return f'''<slide {ns}>
  <style>
    <fill>
      <fillColor color="linear-gradient(135deg,rgba(26,26,46,1) 0%,rgba(22,33,62,1) 50%,rgba(15,52,96,1) 100%)"/>
    </fill>
  </style>
  <data>
    <!-- 装饰形状 -->
    <shape type="rect" topLeftX="0" topLeftY="0" width="10" height="540">
      <fill><fillColor color="rgb(102,126,234)"/></fill>
    </shape>
    <shape type="rect" topLeftX="700" topLeftY="100" width="200" height="200">
      <fill><fillColor color="rgba(124,58,237,0.2)"/></fill>
    </shape>
    
    <!-- 主标题 -->
    <shape type="text" topLeftX="80" topLeftY="140" width="800" height="160">
      <content textType="title" color="rgb(255,255,255)" textAlign="center">
        <p>依托飞书 AI 的无人配送</p>
        <p>全渠道用户反馈闭环运营体系</p>
      </content>
    </shape>
    
    <!-- 分隔线 -->
    <line startX="380" startY="320" endX="580" endY="320">
      <border color="rgb(102,126,234)" width="3"/>
    </line>
    
    <!-- 副标题 -->
    <shape type="text" topLeftX="80" topLeftY="340" width="800" height="50">
      <content textType="sub-headline" color="rgb(160,174,192)" textAlign="center">
        <p>第一次教练沟通材料</p>
      </content>
    </shape>
    
    <!-- 队伍信息 -->
    <shape type="text" topLeftX="80" topLeftY="420" width="800" height="40">
      <content textType="body" color="rgb(226,232,240)" textAlign="center" fontSize="18">
        <p>新石器 AI 反馈先锋队 | 2026年8月10日</p>
      </content>
    </shape>
  </data>
</slide>'''
    
    elif slide_num == 2:
        # 战队分工 & 技术栈
        return f'''<slide {ns}>
  <style>
    <fill><fillColor color="rgb(248,250,252)"/></fill>
  </style>
  <data>
    <!-- 左侧装饰条 -->
    <shape type="rect" topLeftX="0" topLeftY="0" width="8" height="540">
      <fill><fillColor color="rgb(102,126,234)"/></fill>
    </shape>
    
    <!-- 标题 -->
    <shape type="text" topLeftX="60" topLeftY="40" width="840" height="60">
      <content textType="headline" color="rgb(26,26,46)">
        <p>1. 战队分工 &amp; 技术栈</p>
      </content>
    </shape>
    
    <!-- 卡片1：1号 数据线 -->
    <shape type="rect" topLeftX="60" topLeftY="130" width="260" height="340" rx="12">
      <fill><fillColor color="rgb(255,255,255)"/></fill>
      <border color="rgb(226,232,240)" width="1"/>
    </shape>
    <shape type="text" topLeftX="80" topLeftY="150" width="220" height="40">
      <content textType="sub-headline" color="rgb(102,126,234)" fontSize="24">
        <p>🚗 1号 · 数据线</p>
      </content>
    </shape>
    <shape type="text" topLeftX="80" topLeftY="200" width="220" height="30">
      <content textType="body" color="rgb(71,85,105)" bold="true" fontSize="16">
        <p>负责模块</p>
      </content>
    </shape>
    <shape type="text" topLeftX="80" topLeftY="230" width="220" height="100">
      <content textType="body" color="rgb(51,65,85)" fontSize="15">
        <p>▸ 仿真数据集生成</p>
        <p>▸ 社媒舆情采集清洗</p>
        <p>▸ 一车一码扫码反馈</p>
      </content>
    </shape>
    <shape type="text" topLeftX="80" topLeftY="330" width="220" height="30">
      <content textType="body" color="rgb(71,85,105)" bold="true" fontSize="16">
        <p>技术栈</p>
      </content>
    </shape>
    <shape type="text" topLeftX="80" topLeftY="360" width="220" height="90">
      <content textType="body" color="rgb(51,65,85)" fontSize="15">
        <p>▸ Python / pandas</p>
        <p>▸ requests / DeepSeek API</p>
        <p>▸ 飞书表单（零代码）</p>
      </content>
    </shape>
    
    <!-- 卡片2：2号 系统线 -->
    <shape type="rect" topLeftX="350" topLeftY="130" width="260" height="340" rx="12">
      <fill><fillColor color="rgb(255,255,255)"/></fill>
      <border color="rgb(226,232,240)" width="1"/>
    </shape>
    <shape type="text" topLeftX="370" topLeftY="150" width="220" height="40">
      <content textType="sub-headline" color="rgb(102,126,234)" fontSize="24">
        <p>⚙️ 2号 · 系统线</p>
      </content>
    </shape>
    <shape type="text" topLeftX="370" topLeftY="200" width="220" height="30">
      <content textType="body" color="rgb(71,85,105)" bold="true" fontSize="16">
        <p>负责模块</p>
      </content>
    </shape>
    <shape type="text" topLeftX="370" topLeftY="230" width="220" height="100">
      <content textType="body" color="rgb(51,65,85)" fontSize="15">
        <p>▸ 多维表格工单池搭建</p>
        <p>▸ AI字段配置</p>
        <p>▸ 自动化流程 &amp; 仪表盘</p>
      </content>
    </shape>
    <shape type="text" topLeftX="370" topLeftY="330" width="220" height="30">
      <content textType="body" color="rgb(71,85,105)" bold="true" fontSize="16">
        <p>技术栈</p>
      </content>
    </shape>
    <shape type="text" topLeftX="370" topLeftY="360" width="220" height="90">
      <content textType="body" color="rgb(51,65,85)" fontSize="15">
        <p>▸ 飞书多维表格（零代码）</p>
        <p>▸ 飞书AI字段 &amp; 自动化</p>
        <p>▸ 飞书仪表盘可视化</p>
      </content>
    </shape>
    
    <!-- 卡片3：3号 输出线 -->
    <shape type="rect" topLeftX="640" topLeftY="130" width="260" height="340" rx="12">
      <fill><fillColor color="rgb(255,255,255)"/></fill>
      <border color="rgb(226,232,240)" width="1"/>
    </shape>
    <shape type="text" topLeftX="660" topLeftY="150" width="220" height="40">
      <content textType="sub-headline" color="rgb(102,126,234)" fontSize="24">
        <p>📊 3号 · 输出线</p>
      </content>
    </shape>
    <shape type="text" topLeftX="660" topLeftY="200" width="220" height="30">
      <content textType="body" color="rgb(71,85,105)" bold="true" fontSize="16">
        <p>负责模块</p>
      </content>
    </shape>
    <shape type="text" topLeftX="660" topLeftY="230" width="220" height="100">
      <content textType="body" color="rgb(51,65,85)" fontSize="15">
        <p>▸ 聚类周报自动生成</p>
        <p>▸ 飞书文档 &amp; 群推送</p>
        <p>▸ 路演材料 &amp; 团队PDF</p>
      </content>
    </shape>
    <shape type="text" topLeftX="660" topLeftY="330" width="220" height="30">
      <content textType="body" color="rgb(71,85,105)" bold="true" fontSize="16">
        <p>技术栈</p>
      </content>
    </shape>
    <shape type="text" topLeftX="660" topLeftY="360" width="220" height="90">
      <content textType="body" color="rgb(51,65,85)" fontSize="15">
        <p>▸ Python / openpyxl</p>
        <p>▸ 飞书开放平台API</p>
        <p>▸ markdown / 数据可视化</p>
      </content>
    </shape>
  </data>
</slide>'''
    
    elif slide_num == 3:
        # 命题理解 & 落地思路
        return f'''<slide {ns}>
  <style>
    <fill><fillColor color="rgb(248,250,252)"/></fill>
  </style>
  <data>
    <!-- 左侧装饰条 -->
    <shape type="rect" topLeftX="0" topLeftY="0" width="8" height="540">
      <fill><fillColor color="rgb(102,126,234)"/></fill>
    </shape>
    
    <!-- 标题 -->
    <shape type="text" topLeftX="60" topLeftY="40" width="840" height="60">
      <content textType="headline" color="rgb(26,26,46)">
        <p>2. 命题理解 &amp; 落地思路</p>
      </content>
    </shape>
    
    <!-- 痛点1：7个渠道 -->
    <shape type="rect" topLeftX="60" topLeftY="120" width="260" height="120" rx="12">
      <fill><fillColor color="rgb(254,243,199)"/></fill>
    </shape>
    <shape type="text" topLeftX="60" topLeftY="135" width="260" height="60">
      <content textType="headline" color="rgb(220,38,38)" textAlign="center" fontSize="48" bold="true">
        <p>7个</p>
      </content>
    </shape>
    <shape type="text" topLeftX="70" topLeftY="195" width="240" height="40">
      <content textType="body" color="rgb(120,53,15)" textAlign="center" fontSize="14">
        <p>反馈渠道分散</p>
        <p>运营来回切换</p>
      </content>
    </shape>
    
    <!-- 痛点2：70%时间 -->
    <shape type="rect" topLeftX="350" topLeftY="120" width="260" height="120" rx="12">
      <fill><fillColor color="rgb(254,243,199)"/></fill>
    </shape>
    <shape type="text" topLeftX="350" topLeftY="135" width="260" height="60">
      <content textType="headline" color="rgb(220,38,38)" textAlign="center" fontSize="48" bold="true">
        <p>70%</p>
      </content>
    </shape>
    <shape type="text" topLeftX="360" topLeftY="195" width="240" height="40">
      <content textType="body" color="rgb(120,53,15)" textAlign="center" fontSize="14">
        <p>时间耗在人工分类分级</p>
        <p>响应效率低</p>
      </content>
    </shape>
    
    <!-- 痛点3：0条回流 -->
    <shape type="rect" topLeftX="640" topLeftY="120" width="260" height="120" rx="12">
      <fill><fillColor color="rgb(254,243,199)"/></fill>
    </shape>
    <shape type="text" topLeftX="640" topLeftY="135" width="260" height="60">
      <content textType="headline" color="rgb(220,38,38)" textAlign="center" fontSize="48" bold="true">
        <p>0条</p>
      </content>
    </shape>
    <shape type="text" topLeftX="650" topLeftY="195" width="240" height="40">
      <content textType="body" color="rgb(120,53,15)" textAlign="center" fontSize="14">
        <p>反馈止于工单</p>
        <p>无法回流产品</p>
      </content>
    </shape>
    
    <!-- 核心解决方案 -->
    <shape type="text" topLeftX="60" topLeftY="265" width="840" height="40">
      <content textType="sub-headline" color="rgb(102,126,234)" fontSize="22">
        <p>💡 核心解决方案：零代码为主，轻代码为辅</p>
      </content>
    </shape>
    
    <!-- 架构流程 -->
    <shape type="rect" topLeftX="60" topLeftY="315" width="195" height="100" rx="8">
      <fill><fillColor color="rgb(219,234,254)"/></fill>
    </shape>
    <shape type="text" topLeftX="60" topLeftY="335" width="195" height="30">
      <content textType="body" color="rgb(30,64,175)" textAlign="center" bold="true" fontSize="16">
        <p>📥 数据采集层</p>
      </content>
    </shape>
    <shape type="text" topLeftX="70" topLeftY="365" width="175" height="40">
      <content textType="caption" color="rgb(30,64,175)" textAlign="center" fontSize="12">
        <p>7渠道统一接入</p>
      </content>
    </shape>
    
    <shape type="text" topLeftX="260" topLeftY="350" width="30" height="30">
      <content textType="headline" color="rgb(102,126,234)" textAlign="center" fontSize="24">
        <p>→</p>
      </content>
    </shape>
    
    <shape type="rect" topLeftX="295" topLeftY="315" width="195" height="100" rx="8">
      <fill><fillColor color="rgb(219,234,254)"/></fill>
    </shape>
    <shape type="text" topLeftX="295" topLeftY="335" width="195" height="30">
      <content textType="body" color="rgb(30,64,175)" textAlign="center" bold="true" fontSize="16">
        <p>🗄️ 数据汇聚层</p>
      </content>
    </shape>
    <shape type="text" topLeftX="305" topLeftY="365" width="175" height="40">
      <content textType="caption" color="rgb(30,64,175)" textAlign="center" fontSize="12">
        <p>飞书多维表格工单池</p>
      </content>
    </shape>
    
    <shape type="text" topLeftX="495" topLeftY="350" width="30" height="30">
      <content textType="headline" color="rgb(102,126,234)" textAlign="center" fontSize="24">
        <p>→</p>
      </content>
    </shape>
    
    <shape type="rect" topLeftX="530" topLeftY="315" width="195" height="100" rx="8">
      <fill><fillColor color="rgb(219,234,254)"/></fill>
    </shape>
    <shape type="text" topLeftX="530" topLeftY="335" width="195" height="30">
      <content textType="body" color="rgb(30,64,175)" textAlign="center" bold="true" fontSize="16">
        <p>🧠 AI分析层</p>
      </content>
    </shape>
    <shape type="text" topLeftX="540" topLeftY="365" width="175" height="40">
      <content textType="caption" color="rgb(30,64,175)" textAlign="center" fontSize="12">
        <p>DeepSeek + 飞书AI双引擎</p>
      </content>
    </shape>
    
    <shape type="text" topLeftX="730" topLeftY="350" width="30" height="30">
      <content textType="headline" color="rgb(102,126,234)" textAlign="center" fontSize="24">
        <p>→</p>
      </content>
    </shape>
    
    <shape type="rect" topLeftX="765" topLeftY="315" width="135" height="100" rx="8">
      <fill><fillColor color="rgb(219,234,254)"/></fill>
    </shape>
    <shape type="text" topLeftX="765" topLeftY="335" width="135" height="30">
      <content textType="body" color="rgb(30,64,175)" textAlign="center" bold="true" fontSize="16">
        <p>📤 输出层</p>
      </content>
    </shape>
    <shape type="text" topLeftX="775" topLeftY="365" width="115" height="40">
      <content textType="caption" color="rgb(30,64,175)" textAlign="center" fontSize="12">
        <p>周报+群推送+告警</p>
      </content>
    </shape>
    
    <shape type="text" topLeftX="60" topLeftY="440" width="840" height="50">
      <content textType="body" color="rgb(51,65,85)" fontSize="14">
        <p>以飞书多维表格为核心载体，工单池、AI字段、自动化、仪表盘零代码搭建；仅仿真数据、舆情清洗、聚类周报三个环节用Python轻代码补充。</p>
      </content>
    </shape>
  </data>
</slide>'''
    
    elif slide_num == 4:
        # 当前进度
        return f'''<slide {ns}>
  <style>
    <fill><fillColor color="rgb(248,250,252)"/></fill>
  </style>
  <data>
    <!-- 左侧装饰条 -->
    <shape type="rect" topLeftX="0" topLeftY="0" width="8" height="540">
      <fill><fillColor color="rgb(102,126,234)"/></fill>
    </shape>
    
    <!-- 标题 -->
    <shape type="text" topLeftX="60" topLeftY="40" width="840" height="60">
      <content textType="headline" color="rgb(26,26,46)">
        <p>3. 当前进度</p>
      </content>
    </shape>
    
    <!-- 左侧：已完成 -->
    <shape type="rect" topLeftX="60" topLeftY="120" width="400" height="380" rx="12">
      <fill><fillColor color="rgb(236,253,245)"/></fill>
    </shape>
    <shape type="text" topLeftX="80" topLeftY="135" width="360" height="35">
      <content textType="sub-headline" color="rgb(5,150,105)" fontSize="20">
        <p>✅ 已完成</p>
      </content>
    </shape>
    <shape type="text" topLeftX="80" topLeftY="175" width="360" height="300">
      <content textType="body" color="rgb(6,78,59)" fontSize="14" lineSpacing="1.6">
        <p>✓ 800条仿真数据（7渠道×6分层×5类型）</p>
        <p>✓ 多维表格工单池搭建（18字段Schema）</p>
        <p>✓ AI字段配置（分类/分级/摘要）</p>
        <p>✓ 聚类周报脚本（DeepSeek+飞书文档）</p>
        <p>✓ 23个可视化图表</p>
        <p>✓ 路演稿 + 演示脚本 + 架构图</p>
        <p>✓ 团队成果展示PDF</p>
        <p>✓ 代码提交至GitHub</p>
        <p>✓ 飞书文档/幻灯片生成</p>
      </content>
    </shape>
    
    <!-- 右侧上：进行中 -->
    <shape type="rect" topLeftX="500" topLeftY="120" width="400" height="170" rx="12">
      <fill><fillColor color="rgb(255,251,235)"/></fill>
    </shape>
    <shape type="text" topLeftX="520" topLeftY="135" width="360" height="35">
      <content textType="sub-headline" color="rgb(217,119,6)" fontSize="20">
        <p>🔄 进行中</p>
      </content>
    </shape>
    <shape type="text" topLeftX="520" topLeftY="175" width="360" height="100">
      <content textType="body" color="rgb(120,53,15)" fontSize="14" lineSpacing="1.6">
        <p>⟳ 舆情采集脚本测试优化</p>
        <p>⟳ 一车一码飞书表单配置</p>
        <p>⟳ 系统联调与Demo打磨</p>
        <p>⟳ 教练沟通会准备</p>
      </content>
    </shape>
    
    <!-- 右侧下：待完成 -->
    <shape type="rect" topLeftX="500" topLeftY="310" width="400" height="190" rx="12">
      <fill><fillColor color="rgb(249,250,251)"/></fill>
    </shape>
    <shape type="text" topLeftX="520" topLeftY="325" width="360" height="35">
      <content textType="sub-headline" color="rgb(107,114,128)" fontSize="20">
        <p>📋 待完成</p>
      </content>
    </shape>
    <shape type="text" topLeftX="520" topLeftY="365" width="360" height="120">
      <content textType="body" color="rgb(55,65,81)" fontSize="14" lineSpacing="1.6">
        <p>○ 周报定时任务部署</p>
        <p>○ 飞书群推送完整测试</p>
        <p>○ 预录视频备份</p>
        <p>○ 最终路演彩排</p>
      </content>
    </shape>
  </data>
</slide>'''
    
    elif slide_num == 5:
        # 期待教练指导
        return f'''<slide {ns}>
  <style>
    <fill>
      <fillColor color="linear-gradient(135deg,rgba(102,126,234,1) 0%,rgba(118,75,162,1) 100%)"/>
    </fill>
  </style>
  <data>
    <!-- 标题 -->
    <shape type="text" topLeftX="60" topLeftY="40" width="840" height="60">
      <content textType="headline" color="rgb(255,255,255)">
        <p>4. 希望教练重点指导的方向</p>
      </content>
    </shape>
    
    <!-- 卡片1：方案架构 -->
    <shape type="rect" topLeftX="60" topLeftY="120" width="400" height="130" rx="12">
      <fill><fillColor color="rgba(255,255,255,0.95)"/></fill>
    </shape>
    <shape type="text" topLeftX="80" topLeftY="135" width="360" height="35">
      <content textType="sub-headline" color="rgb(190,24,93)" fontSize="20">
        <p>🏗️ 方案架构</p>
      </content>
    </shape>
    <shape type="text" topLeftX="80" topLeftY="170" width="360" height="70">
      <content textType="body" color="rgb(131,24,67)" fontSize="14" lineSpacing="1.5">
        <p>交叉聚合AI架构（DeepSeek+飞书AI问数）设计是否合理？分工边界是否清晰？是否有遗漏的核心AI能力？</p>
      </content>
    </shape>
    
    <!-- 卡片2：演示Demo -->
    <shape type="rect" topLeftX="500" topLeftY="120" width="400" height="130" rx="12">
      <fill><fillColor color="rgba(255,255,255,0.95)"/></fill>
    </shape>
    <shape type="text" topLeftX="520" topLeftY="135" width="360" height="35">
      <content textType="sub-headline" color="rgb(190,24,93)" fontSize="20">
        <p>🎬 演示Demo</p>
      </content>
    </shape>
    <shape type="text" topLeftX="520" topLeftY="170" width="360" height="70">
      <content textType="body" color="rgb(131,24,67)" fontSize="14" lineSpacing="1.5">
        <p>3分钟Demo如何快速展示"扫码→AI分拣→P0告警→周报推送"完整闭环？哪些是必看亮点？</p>
      </content>
    </shape>
    
    <!-- 卡片3：创新亮点 -->
    <shape type="rect" topLeftX="60" topLeftY="270" width="400" height="130" rx="12">
      <fill><fillColor color="rgba(255,255,255,0.95)"/></fill>
    </shape>
    <shape type="text" topLeftX="80" topLeftY="285" width="360" height="35">
      <content textType="sub-headline" color="rgb(190,24,93)" fontSize="20">
        <p>💡 创新亮点</p>
      </content>
    </shape>
    <shape type="text" topLeftX="80" topLeftY="320" width="360" height="70">
      <content textType="body" color="rgb(131,24,67)" fontSize="14" lineSpacing="1.5">
        <p>"零代码+轻代码"如何突出差异化？飞书AI价值如何更好呈现给评委？</p>
      </content>
    </shape>
    
    <!-- 卡片4：商业价值 -->
    <shape type="rect" topLeftX="500" topLeftY="270" width="400" height="130" rx="12">
      <fill><fillColor color="rgba(255,255,255,0.95)"/></fill>
    </shape>
    <shape type="text" topLeftX="520" topLeftY="285" width="360" height="35">
      <content textType="sub-headline" color="rgb(190,24,93)" fontSize="20">
        <p>📈 商业价值</p>
      </content>
    </shape>
    <shape type="text" topLeftX="520" topLeftY="320" width="360" height="70">
      <content textType="body" color="rgb(131,24,67)" fontSize="14" lineSpacing="1.5">
        <p>量化指标（人工分拣降70%、P0响应提速6倍）是否可信？可复用性如何论证？</p>
      </content>
    </shape>
    
    <!-- 致谢 -->
    <shape type="text" topLeftX="60" topLeftY="430" width="840" height="80">
      <content textType="headline" color="rgb(255,255,255)" textAlign="center" fontSize="24">
        <p>🙏 感谢教练指导！</p>
      </content>
      <content textType="body" color="rgba(255,255,255,0.9)" textAlign="center" fontSize="16">
        <p>期待您的宝贵建议，帮助我们把方案打磨得更好</p>
      </content>
    </shape>
  </data>
</slide>'''
    
    else:
        return None


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 创建教练沟通会飞书幻灯片")
    print("=" * 60)
    
    # 步骤1：创建空白PPT
    print("\n📝 步骤1：创建空白演示文稿...")
    result = run_lark_cli([
        "slides", "+create",
        "--title", "新石器AI反馈先锋队 - 第一次教练沟通材料"
    ])
    
    if not result or result.get("code", -1) != 0:
        print(f"❌ 创建PPT失败: {result}")
        # 尝试从raw_output解析
        if result and "raw_output" in result:
            print(f"原始输出: {result['raw_output']}")
        return
    
    pres_id = result.get("data", {}).get("xml_presentation_id")
    if not pres_id:
        print(f"❌ 未获取到presentation_id: {result}")
        return
    
    print(f"✅ 演示文稿创建成功，ID: {pres_id}")
    
    # 步骤2：逐页添加幻灯片
    for page_num in range(1, 6):
        print(f"\n📄 步骤2.{page_num}：添加第{page_num}页...")
        xml_content = create_slide_xml(page_num)
        
        if not xml_content:
            print(f"⚠️  第{page_num}页XML生成失败，跳过")
            continue
        
        # 使用jq和lark-cli添加页面
        # 将XML写入临时文件避免转义问题
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', encoding='utf-8', delete=False) as f:
            f.write(xml_content)
            temp_xml = f.name
        
        try:
            # 使用xml_presentation.slide create API
            slide_result = run_lark_cli([
                "slides", "xml_presentation.slide", "create",
                "--params", json.dumps({"xml_presentation_id": pres_id}),
                "--data", json.dumps({"slide": {"content": xml_content}})
            ])
            
            if slide_result and slide_result.get("code", -1) == 0:
                print(f"✅ 第{page_num}页添加成功")
            else:
                print(f"⚠️  第{page_num}页添加可能有问题: {slide_result}")
        finally:
            os.unlink(temp_xml)
    
    # 完成
    print("\n" + "=" * 60)
    print("🎉 飞书幻灯片创建完成！")
    print(f"📄 演示文稿ID: {pres_id}")
    print(f"🔗 访问链接: https://acnacq48u535.feishu.cn/slides/{pres_id}")
    print("=" * 60)
    
    return pres_id


if __name__ == "__main__":
    main()
