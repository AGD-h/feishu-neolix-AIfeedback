# report — 3号 · 输出线

聚类周报/日报生成模块。

## 功能特性

1. **数据读取**：从飞书多维表格读取近7天工单数据
2. **AI 聚类分析**：调用 DeepSeek 对高频问题进行智能聚类
3. **报告生成**：自动生成结构化的周报文档
4. **飞书推送**：产出飞书文档并推送到团队群

## 文件结构

```
report/
├── weekly_report.py    # 主程序：周报生成逻辑
└── output/             # 本地报告输出目录（自动创建）
    └── weekly_report_YYYYMMDD.md
```

## 配置要求

在项目根目录的 `.env` 文件中配置以下变量：

```ini
# DeepSeek API 凭证
DEEPSEEK_API_KEY=your_deepseek_api_key

# 飞书自建应用凭证
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret

# 飞书多维表格配置（由 2号提供）
BITABLE_APP_TOKEN=your_bitable_token
BITABLE_TABLE_ID=your_table_id

# 飞书群配置（用于周报推送，可选）
FEISHU_CHAT_ID=your_chat_id
```

## 运行方式

```bash
cd report
python weekly_report.py
```

## 输出内容

### 本地输出
- `output/weekly_report_YYYYMMDD.md`：Markdown 格式的周报文件

### 飞书输出
- 自动创建飞书文档，包含：
  - 本周概况（工单总数、分类分布、优先级分布、渠道分布）
  - 原始反馈列表（最多显示50条）
  - AI 聚类分析结果（高频问题Top3、改进建议、优先级排序）

## 报告结构示例

```markdown
# 📊 无人配送反馈聚类周报

生成时间：2024年01月15日 10:30

## 📈 本周概况

本周共收到 **156** 条用户反馈，数据覆盖近7天。

### 分类分布
| 类别 | 数量 | 占比 |
|------|------|------|
| 故障 | 45 | 28.8% |
| 体验 | 38 | 24.4% |
...

## 🤖 AI 聚类分析结果

### 高频问题汇总

**P0 安全类**：
- 问题1：车辆在小区门口与电动车剐蹭（发生3起）
- 改进建议：优化路口感知算法，增加行人优先策略

...
```

## 依赖说明

需要安装以下 Python 包：
- requests >= 2.32
- python-dotenv >= 1.0
- openai >= 1.40

这些已在 `report` 目录的 `requirements.txt` 中声明。
