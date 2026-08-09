# 新石器无人车用户反馈 H5

React 18 + TypeScript + Vite 5 + TailwindCSS 3 + Framer Motion

---

## 快速开始

```bash
cd h5
npm install
npm run dev
```

访问 http://localhost:3000

---

## 架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                         H5 前端 (React)                         │
│  ┌──────────┐   ┌────────────┐   ┌────────────┐   ┌──────────┐ │
│  │ 首页     │ → │ 反馈表单    │ → │ AI分析中    │ → │ 结果页    │ │
│  └──────────┘   └────────────┘   └────────────┘   └──────────┘ │
│                          ↓                                      │
│              submitFeedback()  [api.ts]                         │
│         USE_REAL_API=true?    ↓ USE_REAL_API=false?            │
│              ↓                       ↓                          │
│     POST /api/submit         本地 Mock 模拟 AI 分析             │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│               Vercel Serverless Function                        │
│  [h5/api/submit.ts]                                             │
│    1. 校验必填字段 + 请求体大小限制                               │
│    2. 调用飞书 tenant_access_token 接口鉴权                      │
│    3. 按 Schema 构建多维表格字段                                  │
│    4. 调用飞书 bitable/v1 接口写入工单记录                       │
│    5. 返回标准化工单结果 (含 record_id 作为 ticket_id)           │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ▼
        飞书多维表格工单池
        (channel=车身扫码, status=待处理)
```

**部署方式**：前端页面 + Serverless Function 一并部署到 Vercel（`vercel --prod`），
部署后前端和 API 自动同域，无需额外 CORS 配置。

---

## 一车一码使用方式

通过 URL 参数预填车辆信息（模拟扫码后的上下文）：

```
https://your-domain.com/?vid=NEOLIX001&model=新石器X3&city=北京&loc=望京SOHO
```

| 参数 | 说明 | 必填 |
|------|------|------|
| `vid` | 车辆ID/编号 | 是 |
| `model` | 车型名称 | 否 |
| `city` | 所在城市 | 否 |
| `loc` | 具体位置 | 否 |

---

## 功能模块

| 页面 | 文件 | 说明 |
|------|------|------|
| **首页** | [components/HomePage.tsx](components/HomePage.tsx) | 车辆信息展示、功能介绍、开始反馈入口 |
| **反馈表单** | [components/FeedbackForm.tsx](components/FeedbackForm.tsx) | 问题描述（含快速选择标签）、问题类型选择、联系方式选填、字段长度校验 |
| **AI分析中** | [components/SubmittingPage.tsx](components/SubmittingPage.tsx) | 4步动画（提交→分析→分类→生成工单→通知负责人） |
| **结果页** | [components/ResultPage.tsx](components/ResultPage.tsx) | 工单号、AI识别的分类/优先级、预计响应时间、状态追踪、工单号复制 |
| **错误页** | [components/ErrorPage.tsx](components/ErrorPage.tsx) | 网络异常重试引导、连续失败3次后弹出「建议联系人工客服」卡片（客服电话+微信一键复制） |
| **调试面板** | [components/DebugPanel.tsx](components/DebugPanel.tsx) | 实时日志、模拟模式切换（成功/断网/500/超时）、错误计数 |

---

## 运行单元测试

```bash
cd h5
npm test
```

覆盖 Serverless Function 的 17 项测试用例（正常流程、环境变量校验、必填字段、飞书API错误、超时、HTTP方法、请求体大小、响应格式）。

---

## 环境变量说明

本项目涉及 **6 个环境变量**，分为两组：

### 第一组：H5 前端环境变量（`h5/.env.local`，开发者本地配置）

| 变量名 | 说明 | 可选值 | 默认值 |
|--------|------|--------|--------|
| `VITE_USE_REAL_API` | 是否调用真实 Serverless Function 写入飞书 | `true` / `false` | `false` |
| `VITE_FEISHU_API_BASE` | API 基础地址 | 留空（同域）或 Vercel 部署域名 | 留空 |

> 当 `VITE_USE_REAL_API=false`（默认）时，使用本地 Mock 模拟 AI 分析，无需任何后端即可演示。

### 第二组：Vercel 平台环境变量（在 vercel.com Dashboard 配置，不提交到代码）

| 变量名 | 说明 | 来源 |
|--------|------|------|
| `FEISHU_APP_ID` | 飞书自建应用 App ID | 飞书开发者后台 → 凭证与基础信息 |
| `FEISHU_APP_SECRET` | 飞书自建应用 App Secret | 同上，**绝不能泄露到前端代码** |
| `BITABLE_APP_TOKEN` | 多维表格 app_token | 多维表格 URL 中 `/base/` 后面的字符串 |
| `BITABLE_TABLE_ID` | 工单表 table_id | 多维表格 URL 中 `table=` 参数的值 |

### 配置切换逻辑

```
VITE_USE_REAL_API=false
  └──→ 前端本地 Mock 模式（无需网络，AI 分类本地计算）
      └──→ 适用：Demo 演示、UI 调试、失败场景模拟

VITE_USE_REAL_API=true
  └──→ 前端调用 /api/submit (Serverless Function)
      └──→ 后端用 Vercel 环境变量中的密钥调用飞书 API，写入多维表格
          └──→ 适用：生产环境、真实数据联调
```

---

## 字段映射关系（前端 → Serverless Function → 飞书多维表格）

| 前端字段名 | 类型 | Serverless Function 字段 | 飞书列名 | 默认值 |
|-----------|------|-------------------------|---------|--------|
| `vehicle_id` | string | `vehicle_id` | vehicle_id | 必填，无默认 |
| `content_raw` | string | `content_raw` | content_raw | 必填，无默认 |
| `category` | string（选填） | `category` | category | 不填则飞书侧留空，后续 AI 自动打标 |
| `contact_name` | string（选填） | `contact_name` | contact_name | 不填不写入 |
| `contact_phone` | string（选填） | `contact_phone` | contact_phone | 不填不写入 |
| `contact_allowed` | boolean（选填） | `contact_allowed` | contact_allowed | 不填不写入；true→"是"，false→"否" |
| `location_detail` | string（选填） | `location_detail` | location_detail | 不填不写入 |
| — | — | `channel` | channel | 固定值："车身扫码" |
| — | — | `status` | status | 固定值："待处理" |

---

## Serverless Function 错误码

`/api/submit` 接口可能返回的 HTTP 状态码：

| 状态码 | 说明 | 触发条件 | 前端提示 |
|--------|------|---------|---------|
| 200 | 成功 | 数据正常写入多维表格 | 跳转到结果页，显示工单号 |
| 400 | 缺少必填字段 | `vehicle_id` 或 `content_raw` 缺失/为空 | 表单校验拦截（前端已阻止） |
| 405 | 方法不允许 | 请求不是 POST | 前端不会触发 |
| 413 | 请求体过大 | Content-Length > 10KB | "请求体过大，请缩短反馈内容" |
| 500 | 服务器错误 | 飞书API返回错误码（如91402）、网络异常 | "服务器异常，请稍后重试或联系管理员" |
| 504 | 飞书API超时 | 鉴权或写入接口 10s 内未响应 | "服务器响应超时，请稍后重试" |

---

## 演示用失败场景模拟

### URL 参数方式

| 参数 | 场景 | 预期错误提示 |
|------|------|-------------|
| `?mock=network` 或 `?mock=fail` | 网络断开 | "网络连接失败，请检查网络设置后重试" |
| `?mock=server` 或 `?mock=500` | 服务器 500 | "服务器异常，请稍后重试或联系管理员" |
| `?mock=timeout` | 请求超时（8s） | "请求超时，请检查网络信号后重试" |

### 调试面板方式（推荐）

点击页面右下角 🐛 按钮打开调试面板，直接切换模式按钮即可。

连续失败 3 次后，[ErrorPage.tsx](components/ErrorPage.tsx) 会弹出红色客服卡片，
包含客服电话和微信的一键复制按钮。

---

## 对接真实飞书 API（完整流程）

详见仓库根目录 [LOCAL_TEST_GUIDE.md](../LOCAL_TEST_GUIDE.md)，
涵盖：Vercel CLI 安装、项目关联、环境变量配置、`vercel dev` 本地联调、`vercel --prod` 生产部署。

---

## 构建与部署

```bash
# 本地生产构建（验证）
npm run build

# 或直接通过 Vercel 部署
cd ..   # 回到仓库根目录
vercel --prod
```

Vercel 会读取根目录下的 [vercel.json](../vercel.json)：
- `installCommand` = `cd h5 && npm install`
- `buildCommand` = `cd h5 && npm install && npm run build`
- `outputDirectory` = `h5/dist`

部署后：
- 前端页面：`https://your-project.vercel.app/`
- API 接口：`https://your-project.vercel.app/api/submit`

---

## 其他说明

- 页面底部的调试面板（🐛）为演示和联调工具，生产环境如有需要可在 [App.tsx](App.tsx#L162-L162) 中移除 `<DebugPanel />` 组件。
- 失败计数（连续失败 3 次提示）在提交成功后自动清零，逻辑见 [App.tsx handleSubmit](App.tsx#L86-L100)。
- 本地上传超大反馈内容时 Serverless Function 会直接返回 413，防止 DoS。