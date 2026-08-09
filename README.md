# feishu-neolix-AIfeedback

2026 飞书 AI 先锋未来人才大赛参赛项目：依托飞书 AI 搭建无人配送全渠道用户反馈闭环运营体系（新石器无人车命题）。

## 目录结构

| 目录 | 负责人 | 内容 |
|------|--------|------|
| `data/` | 1号 · 数据线 | 仿真反馈数据集生成脚本、社媒舆情采集脚本 |
| [`h5/`](#h5一车一码扫码反馈h5) | 1号 · 数据线 | **一车一码扫码反馈页（已实现，含 Vercel Serverless Function 对接飞书 API）** |
| `report/` | 3号 · 输出线 | 聚类周报/日报生成模块 |
| `docs/` | 3号 · 输出线 | 数据分布说明、接口说明、方案文档 |

系统主体（工单池、AI 字段、自动化流程、回访、仪表盘）由 2号在飞书多维表格中零代码搭建，不在本仓库。

---

## `h5/`：一车一码扫码反馈 H5

**一车一码反馈入口是用户触达工单体系的最前端入口**，覆盖"车身扫码直接反馈"场景——
用户发现问题后，扫车辆身上的二维码即可提交反馈，无需下载 App 或拨打电话，
提交后实时返回 AI 识别结果与工单号，形成全渠道闭环。

### 技术栈

- **前端**：React 18 + TypeScript + Vite 5 + TailwindCSS 3 + Framer Motion
- **后端**：Vercel Serverless Function（TypeScript，零服务器运维）
- **数据层**：飞书多维表格 API（bitable/v1）
- **CI**：GitHub Actions（H5 构建 + Python 语法检查）

### 功能清单

| 模块 | 说明 |
|------|------|
| 📱 **5 个前端页面** | 首页、反馈表单、AI分析中、结果页、错误页 |
| 🏷️ **AI 自动分类** | 5类关键词规则（安全/故障/体验/投诉/建议）+ 4级优先级（P0-P3） |
| 🐛 **调试面板** | 实时日志 + Mock 模式切换（成功/断网/500/超时） |
| 🔁 **失败降级机制** | 连续失败 3 次后弹出「联系人工客服」卡片（电话+微信一键复制） |
| ⏱️ **超时控制** | 前端 15s + Serverless Function 10s 双层 AbortController |
| 🛡️ **错误码体系** | 400/405/413/500/504 统一响应，前端差异化提示 |
| 🧪 **单元测试** | 17 项测试覆盖后端全部分支（npm test 运行） |
| 🚀 **一键部署** | vercel.json 配置完毕，vercel --prod 即可上线 |

### 数据流向

```
用户扫码（车身二维码）
  ↓ URL 携带车辆信息 (?vid=&model=&city=&loc=)
H5 页面显示车辆上下文
  ↓ 用户填写反馈
前端 submitFeedback() [src/api.ts]
  ├─ USE_REAL_API=false（默认） → 本地 Mock 模拟 AI 分类，生成伪工单号
  └─ USE_REAL_API=true          → POST /api/submit
                                      ↓
                           Vercel Serverless Function [h5/api/submit.ts]
                             1. 校验字段 + 体大小限制
                             2. 获取 tenant_access_token（10s 超时）
                             3. 按 Schema 构建 fields
                             4. 写入飞书多维表格（10s 超时）
                             5. 返回 record_id 作为 ticket_id
                                      ↓
                                飞书多维表格工单池
                                （channel=车身扫码，status=待处理）
```

### 部署形态

```bash
# 根目录执行
vercel --prod
```

部署后：
- **前端静态资源** → Vercel CDN（H5 页面）
- **/api/submit** → Vercel Serverless Function（按需执行，免费额度内无需费用）
- **密钥** → Vercel 环境变量加密存储（不进入前端 bundle，杜绝泄露）

### 开发与联调

详见：
- [h5/README.md](h5/README.md) — H5 完整文档（架构、环境变量、字段映射、错误码）
- [LOCAL_TEST_GUIDE.md](LOCAL_TEST_GUIDE.md) — 本地模拟生产环境全流程测试指南
- [h5/DEMO_GUIDE.md](h5/DEMO_GUIDE.md) — 演示操作手册（手机访问、4 个场景演示步骤）

---

## 协作约定

1. 各自只改自己文件夹里的文件，直接在 `main` 分支提交推送。
2. Python 统一 3.11+，依赖写进 `requirements.txt`。
3. 密钥一律写在本地 `.env` 文件（已被 git 忽略），**永远不要提交真实密钥**。新增配置项时同步更新 `.env.example`。
4. 工单数据字段以团队技术方案中的 Schema 为唯一标准，改字段需三人同意。

## 快速开始

```bash
git clone <仓库地址>
cd feishu-neolix-AIfeedback
pip install -r requirements.txt
copy .env.example .env   # 然后填入自己的密钥
```