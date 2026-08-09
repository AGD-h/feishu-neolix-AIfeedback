# -*- coding: utf-8 -*-
"""
生成全国40强冲刺计划飞书文档
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import requests
from dotenv import load_dotenv

os.environ['NO_PROXY'] = 'open.feishu.cn,feishu.cn'
os.environ['no_proxy'] = 'open.feishu.cn,feishu.cn'
for k in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(k, None)

SESSION = requests.Session()
SESSION.trust_env = False

sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / 'report'))

from weekly_report import create_feishu_document

TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
DOC_TITLE = "全国40强冲刺计划（8/11-8/16）"
DEMO_SCRIPT_DOC = "https://acnacq48u535.feishu.cn/docx/T1Cqd5hT1oOxkexZGyTco0kmnbd"
COACH_DOC = "https://acnacq48u535.feishu.cn/docx/DD12d6H0dowctbxxjEmc41RCn0d"


def get_sprint_plan_content() -> str:
    md = f"""# 🎯 全国40强冲刺计划

| 项目 | 信息 |
|------|------|
| 目标 | 进入全国40强 |
| 截止时间 | 2026年8月16日 24:00 |
| 冲刺天数 | 6天（8月11日-8月16日） |
| 核心策略 | AI分析方向打深 + H5入口补齐短板 |
| 教练沟通材料 | {COACH_DOC} |
| Demo演示脚本 | {DEMO_SCRIPT_DOC} |

---

# 一、战略判断

## 照片反馈核心信号

| 信号 | 解读 | 我们的应对 |
|------|------|-----------|
| "做得太简单了" | 当前是MVP演示水平，缺产品完整度 | 从"能演示"升级到"像产品" |
| "第三方反馈web、qrcode" | 入口体验粗糙被点名 | 做品牌化H5反馈页+二维码系统 |
| "要么方向全，要么深度够深" | 评委选品逻辑 | 选深度路线：AI分析方向打穿 |

## 战略选择：一个方向打深 + 补关键短板

| 维度 | 选择 | 理由 |
|------|------|------|
| 主攻方向 | AI分析深度打穿 | 周报+AI聚类是核心差异化，跨周追踪+根因链是壁垒 |
| 必补短板 | H5反馈页+二维码系统 | 照片明确点名，不补直接丢分 |
| 不做的事 | 不再加新渠道/新模块 | 6天时间不够，分散精力 |

---

# 二、四大深度升级点

## 🔥 升级1：AI周报v2——从"报告"到"改进行动闭环"（最高优先级）

当前周报只看"本周"，增加四层深度：

| 新增模块 | 内容 | 评委价值 |
|---------|------|---------|
| 上周行动追踪表 | 上周TOP问题→本周状态（已解决/改善/持平/恶化） | 证明系统不是"看完就忘"，真正驱动改进 |
| 问题根因链分析 | "柜门打不开"→低温导致→锁具批次问题（三层根因） | 体现AI深度分析能力，不是关键词匹配 |
| 改进ROI优先级矩阵 | 按"影响用户数×频次×修复难度"排序 | 给产品经理可执行的优先级，不是泛泛建议 |
| 同类问题关联发现 | A问题关联B问题关联C问题→发现系统性缺陷 | 体现聚类价值，发现人看不到的关联 |

## 🔥 升级2：H5扫码反馈页（补照片点名短板）

替代简陋的飞书表单链接，做产品级反馈入口：

| 功能 | 说明 | 优先级 |
|------|------|--------|
| 品牌化UI | 新石器品牌色、专业视觉设计 | P0 |
| 一车一码 | URL参数带vehicle_id，扫码自动识别车辆 | P0 |
| 提交动画 | "AI正在分析..."加载动画，2秒展示AI分类结果 | P1 |
| 感谢页+工单状态 | 显示工单号、优先级、预计响应时间 | P1 |
| 二维码生成管理页 | 输入车牌号→生成二维码→下载PNG打印 | P2 |

## 🔥 升级3：管理驾驶舱仪表盘

在现有6张图表基础上，增加管理者视角：

| 新增图表 | 内容 |
|---------|------|
| 改进完成率趋势 | 每周提出的问题→下周解决率变化曲线 |
| 城市热力对比 | 哪个城市问题最多、哪款车故障最高 |
| 响应时间趋势 | P0/P1平均响应时间逐日变化 |

## 🔥 升级4：真实舆情数据打通

| 任务 | 说明 |
|------|------|
| SerpAPI真实采集 | 跑通小红书/微博/知乎/黑猫投诉真实数据采集 |
| AI清洗入池 | DeepSeek清洗为标准工单格式，导入多维表格 |
| 混合演示数据 | 仿真800条+真实数据混合，证明系统处理真实数据 |

---

# 三、6天冲刺时间线

## 8月10日（今天）—— 教练沟通日

| 时间 | 事项 |
|------|------|
| 14:00 | 教练沟通会（带话术清单，重点问3个方向问题） |
| 会后 | 整理教练反馈，调整冲刺计划细节 |
| 晚上 | 确认最终任务分配，准备第二天开工 |

## 8月11日（Day1）—— 周报深度升级

| 角色 | 任务 | 交付物 |
|------|------|--------|
| 1号 | 跑SerpAPI真实采集，测试API可用性，采集50-100条真实社媒数据 | 真实数据CSV文件 |
| 2号 | 多维表格增加字段：改进状态、根因标签、关联问题ID、上周问题标记 | 表结构更新 |
| 3号 | 重写周报v2 Prompt：增加跨周追踪、根因链、ROI排序、同类关联模块 | 周报v2脚本可运行 |

## 8月12日（Day2）—— H5反馈页开发

| 角色 | 任务 | 交付物 |
|------|------|--------|
| 1号 | 配合联调：测试H5提交→API写入多维表格全链路 | API联调通过 |
| 2号 | 配置飞书开放平台权限：H5应用的表单提交API权限、webhook配置 | 权限配置完成 |
| 3号 | 开发H5页面：React+Tailwind，含首页/反馈表单/提交动画/感谢页 | H5页面demo可运行 |

## 8月13日（Day3）—— 二维码系统+全链路联调

| 角色 | 任务 | 交付物 |
|------|------|--------|
| 1号 | 二维码生成工具：输入车牌号→生成带vehicle_id的二维码→下载PNG | 二维码PNG素材 |
| 2号 | 仪表盘增加管理视角图表（改进完成率、城市热力、响应时间趋势） | 仪表盘更新 |
| 3号 | 全链路联调：扫码→提交→AI分拣→入池→P0告警；修复所有bug | 端到端跑通 |

## 8月14日（Day4）—— 真实数据验证+深度打磨

| 角色 | 任务 | 交付物 |
|------|------|--------|
| 1号 | 真实舆情数据清洗（DeepSeek），导入工单池，和仿真数据混合做演示集 | 混合数据集 |
| 2号 | 自动化流程全链路测试：P0推送、SLA升级、满意度回访、定时触发 | 自动化流程稳定 |
| 3号 | 周报v2用混合数据跑通，调优Prompt质量；修复所有发现的问题 | 周报v2稳定可演示 |

## 8月15日（Day5）—— 录屏+路演材料升级

| 角色 | 任务 | 交付物 |
|------|------|--------|
| 1号 | 协助录屏：扫码提交流程、舆情采集流程演示 | 录屏素材 |
| 2号 | 协助录屏：AI分拣、仪表盘、自动化流程演示 | 录屏素材 |
| 3号 | 录屏：周报生成+AI问数交互；剪辑3分钟Demo视频；更新路演稿加入新功能 | 3分钟演示视频+路演稿v2 |

## 8月16日（Day6）—— 最终提交

| 时间 | 事项 |
|------|------|
| 上午 | 代码整理、GitHub提交、README更新、最终检查 |
| 下午 | 飞书系统配置备份、权限确认、最终演示彩排 |
| 晚上 | 提交材料打包（代码+文档+视频+PPT），24点前提交 |

---

# 四、优先级矩阵（时间不够砍什么）

| 优先级 | 功能 | 砍不砍 | 砍的代价 |
|--------|------|--------|---------|
| 🔴 P0 必须做 | 周报深度升级（跨周追踪+根因链） | ❌ 绝对不砍 | 核心差异化没了 |
| 🔴 P0 必须做 | H5反馈页（品牌UI+表单+提交动画） | ❌ 不砍 | 照片明确点名 |
| 🟠 P1 尽量做 | SerpAPI真实舆情数据跑通 | ⚠️ 可砍部分 | 没真实数据说服力弱，但仿真也能演示 |
| 🟠 P1 尽量做 | 管理驾驶舱新图表 | ⚠️ 可砍部分 | 现有6张图表演示够用 |
| 🟡 P2 有时间做 | 二维码管理后台页面 | ✅ 可砍 | 在线二维码生成器+Excel也能演示 |
| 🟡 P2 有时间做 | 反馈实时AI结果展示 | ✅ 可砍 | 锦上添花 |

---

# 五、明天教练会要问的3个问题

| # | 问题 | 目的 |
|---|------|------|
| 1 | 周报做"跨周改进行动追踪"vs"单次分析深度加深"，评委更看重哪个？ | 验证深度方向 |
| 2 | 花1.5天做品牌化H5反馈页值不值？还是投到其他地方性价比更高？ | 验证H5投入 |
| 3 | 从评委视角看，我们最大的短板/最容易被扣分的地方是什么？ | 发现盲区 |

> 详细话术和应对预案见：`docs/教练沟通会_提问话术.md`

---

# 六、风险与应对

| 风险 | 概率 | 应对 |
|------|------|------|
| 教练说方向错了，需要大改 | 中 | 8/10会后立刻调整计划，Day1按教练反馈重新分配任务 |
| H5开发比预想复杂，1.5天做不完 | 中 | 砍掉二维码管理后台，只做核心反馈页（首页+表单+感谢页） |
| SerpAPI被限流或拿不到有效真实数据 | 高 | 退回到仿真数据为主，准备好"因为合规原因我们用仿真+少量公开数据验证"的说辞 |
| DeepSeek API不稳定 | 低 | 准备好离线模式，周报生成可降级为基于规则的模板输出 |
| 某个队员时间不够/掉链子 | 低 | 任务有优先级，P0任务必须完成，P2任务可集体支援 |
| 飞书系统配置改坏了 | 低 | Day3前完成配置修改并做备份，之后不做大改 |

---

# 七、每日站会约定

冲刺期间每天晚上21:00在飞书群开10分钟站会：
1. 今天完成了什么
2. 明天做什么
3. 遇到什么卡点需要帮忙

不写长篇日报，口头同步+群里发一条消息即可。
"""
    return md


def get_tenant_access_token(app_id: str, app_secret: str) -> Optional[str]:
    try:
        resp = SESSION.post(
            TOKEN_URL,
            json={"app_id": app_id, "app_secret": app_secret},
            timeout=30,
        )
        data = resp.json()
        if data.get("code") == 0:
            return data["tenant_access_token"]
        else:
            print(f"❌ 获取token失败: {data.get('msg')}")
            return None
    except Exception as e:
        print(f"❌ 获取token异常: {e}")
        return None


def send_doc_to_chat(doc_url: str, token: str, title: str, chat_id: str) -> bool:
    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": f"🎯 {title}"},
            "template": "blue",
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**全国40强冲刺计划已制定完成（8/11-8/16）**\n\n6天冲刺，AI分析打深 + H5入口补齐，目标全国40强！\n\n📄 [点击查看完整冲刺计划]({doc_url})",
                },
            },
            {"tag": "hr"},
            {
                "tag": "div",
                "fields": [
                    {"is_short": True, "text": {"tag": "lark_md", "content": "**⏰ 截止时间**\n8月16日 24:00"}},
                    {"is_short": True, "text": {"tag": "lark_md", "content": "**🔥 主攻方向**\nAI分析深度打穿"}},
                    {"is_short": True, "text": {"tag": "lark_md", "content": "**🔧 必补短板**\nH5反馈页+二维码"}},
                    {"is_short": True, "text": {"tag": "lark_md", "content": "**📋 关键节点**\nDay1周报v2 / Day3联调 / Day5录屏"}},
                ],
            },
        ],
    }

    try:
        resp = SESSION.post(
            "https://open.feishu.cn/open-apis/im/v1/messages",
            params={"receive_id_type": "chat_id"},
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={
                "receive_id": chat_id,
                "msg_type": "interactive",
                "content": json.dumps(card, ensure_ascii=False),
            },
            timeout=30,
        )
        data = resp.json()
        if data.get("code") == 0:
            print(f"✅ 消息已发送到飞书群！消息ID: {data['data']['message_id']}")
            return True
        else:
            print(f"❌ 发送失败: {data.get('msg')}")
            return False
    except Exception as e:
        print(f"❌ 发送异常: {e}")
        return False


def main():
    print("=" * 60)
    print("🚀 全国40强冲刺计划 → 飞书文档")
    print("=" * 60)

    load_dotenv()
    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")
    chat_id = os.getenv("FEISHU_CHAT_ID")

    if not app_id or not app_secret:
        print("❌ 请在 .env 中配置 FEISHU_APP_ID 和 FEISHU_APP_SECRET")
        return

    print("🔑 获取飞书访问令牌...")
    token = get_tenant_access_token(app_id, app_secret)
    if not token:
        return
    print("✅ 获取token成功")

    print("📝 正在创建飞书文档...")
    md_content = get_sprint_plan_content()
    doc_url = create_feishu_document(
        title=DOC_TITLE,
        markdown_content=md_content,
        tenant_access_token=token,
    )

    if not doc_url:
        print("❌ 文档创建失败")
        return

    print(f"\n{'=' * 60}")
    print(f"🎉 飞书文档创建成功！")
    print(f"📄 文档标题: {DOC_TITLE}")
    print(f"🔗 文档链接: {doc_url}")
    print(f"{'=' * 60}\n")

    print("📤 正在发送到飞书群...")
    if chat_id:
        send_doc_to_chat(doc_url, token, DOC_TITLE, chat_id)
    else:
        print("⚠️ 未配置 FEISHU_CHAT_ID，跳过发送")


if __name__ == "__main__":
    main()
