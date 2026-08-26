# 飞书 x 新石器无人车 — 全渠道用户反馈 AI 闭环

> 2026 飞书 AI 先锋未来人才大赛 · 新石器命题
>
> 依托飞书多维表格 + AI 能力，实现"扫码反馈 → AI 分类聚类 → 工单分发 → 回访跟进 → 每周洞察"的**用户反馈全链路闭环**。

---

## 📌 目录

- [一、架构总览](#一架构总览)
- [二、目录结构 & 分工](#二目录结构--分工)
- [三、快速开始（3 步跑起来）](#三快速开始3-步跑起来)
- [四、H5 前端：一车一码扫码反馈页](#四h5-前端一车一码扫码反馈页)
  - [4.1 技术栈](#41-技术栈)
  - [4.2 页面一览](#42-页面一览)
  - [4.3 一车一码参数用法](#43-一车一码参数用法)
  - [4.4 AI 分类 & 优先级规则（Mock）](#44-ai-分类--优先级规则mock)
  - [4.5 调试面板 & 失败场景模拟](#45-调试面板--失败场景模拟)
  - [4.6 连续失败 3 次降级策略](#46-连续失败-3-次降级策略)
- [五、后端：Vercel Serverless Function × 飞书 API](#五后端vercel-serverless-function--飞书-api)
  - [5.1 数据流向图](#51-数据流向图)
  - [5.2 submit.ts 执行流程](#52-submitts-执行流程)
  - [5.3 字段映射关系](#53-字段映射关系)
  - [5.4 错误码体系](#54-错误码体系)
  - [5.5 安全要点](#55-安全要点)
- [六、双模式切换（Mock / 真实 API）](#六双模式切换mock--真实-api)
- [七、环境变量总表（6 个）](#七环境变量总表6-个)
- [八、部署说明](#八部署说明)
  - [8.1 GitHub Actions CI / CD](#81-github-actions-ci--cd)
  - [8.2 Vercel 生产部署](#82-vercel-生产部署)
- [九、验证方式（3 种）](#九验证方式3-种)
  - [9.1 跑单元测试（17 项全通过）](#91-跑单元测试17-项全通过)
  - [9.2 本地 Demo 演示（无需密钥）](#92-本地-demo-演示无需密钥)
  - [9.3 真实飞书 API 联调（vercel dev）](#93-真实飞书-api-联调vercel-dev)
- [十、CHANGELOG 摘要 · v1.0.0](#十changelog-摘要--v100)
- [十一、文档索引（5 份配套文档）](#十一文档索引5-份配套文档)
- [十二、协作约定](#十二协作约定)

---

## 一、架构总览

```
            ┌───────────────────────── 全渠道反馈入口 ──────────────────────────┐
            │                                                                   │
   ┌──────────────┐  ┌──────────────────┐  ┌──────────────────┐                 │
   │ 车身扫码 H5  │  │ 客服电话/IM记录   │  │  社媒舆情抓取    │  ... 线下问卷   │
   │   (本 PR ✅)  │  │   (2号零代码搭建) │  │  (1号爬虫脚本)   │                 │
   └───────┬──────┘  └─────────┬────────┘  └────────┬─────────┘                 │
           │                   │                    │                            │
           └───────────────────┴────────────────────┘                            │
                               ↓                                                 │
                   ┌──────────────────────────┐                                  │
                   │   飞书多维表格 工单池     │  ← 本系统的数据底座              │
                   │  (AI 自动分类 / 优先级)   │    (2号零代码搭建)                │
                   └──────────┬───────────────┘                                  │
                              ↓                                                  │
              ┌───────────────┴────────────────┐                                 │
              ↓                                ↓                                 │
    ┌────────────────────┐          ┌────────────────────┐                      │
    │ 自动化流程 & 回访   │          │  聚类周报 / 洞察   │                      │
    │   (2号飞书集成)     │          │   (3号 Python脚本) │                      │
    └────────────────────┘          └────────────────────┘                      │
                                                                                │
            └───────────────────────────────────────────────────────────────────┘
```

本仓库交付 H5（一车一码前端 + Serverless Function 后端）和 Python 数据脚本两部分。
工单池主体、AI 字段、自动化流程、回访、仪表盘由 2号在飞书多维表格中零代码搭建，不在本仓库。

---

## 二、目录结构 & 分工

| 目录 / 文件 | 负责人 | 内容 |
|-------------|--------|------|
| `data/` | 1号 · 数据线 | 仿真数据集 + 社媒舆情采集脚本 |
| **`h5/`** | 1号 · 数据线 | **一车一码 AI 反馈 H5（前端 + 后端，本 PR 完整实现 ✅）** |
| `report/` | 3号 · 输出线 | DeepSeek 聚类周报 / 日报生成 |
| `docs/` | 全员 | 方案文档、接口说明、Code Review 专用说明 |
| `scripts/` | 1号 | 工具脚本（飞书鉴权验证、单条反馈写入）|
| [`CHANGELOG.md`](CHANGELOG.md) | — | 变更日志（Added / Fixed / Changed / Documentation 完整分类）|
| [`vercel.json`](vercel.json) | — | Vercel 部署配置 |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | — | CI 流水线（H5 构建 + Python 语法检查）|
| [`.env.example`](.env.example) | — | Python 脚本环境变量模板 |

---

## 三、快速开始（3 步跑起来）

> 想直接看 H5 Demo 不用飞书密钥，3 条命令：

```bash
# 1. 克隆仓库
git clone https://github.com/AGD-h/feishu-neolix-AIfeedback.git
cd feishu-neolix-AIfeedback

# 2. 启动 H5 本地开发服务
cd h5
npm install
npm run dev
# → http://localhost:3000/?vid=NX-TEST-001&city=北京&loc=望京SOHO

# 3. （可选）跑 17 项后端单元测试
npm test
```

演示时默认走 **Mock 模式**（本地模拟 AI 分类，无需任何密钥和后端网络）。
需要对接真实飞书 API 看 **第七章（环境变量）** 和 **第九章第 3 节（vercel dev 联调）**。

---

## 四、H5 前端：一车一码扫码反馈页

### 4.1 技术栈

| 类别 | 选型 | 作用 |
|------|------|------|
| 框架 | **React 18** + **TypeScript 5.3** | 组件化 + 类型安全 |
| 构建 | **Vite 5** | HMR 热更新、构建速度快 |
| 样式 | **TailwindCSS 3.4** | 原子化 CSS + 自定义新石器品牌色板 (neolix-50 → neolix-700) |
| 动效 | **Framer Motion 11** | 页面切换动画、AI 分析中脉冲/扫描光效 |
| 图标 | **lucide-react 0.400** | 轻量 SVG 图标库 |
| 二维码 | **qrcode.react 3.1** | 生成演示二维码 |
| 测试 | **Node.js node:test**（原生） | 17 项 Serverless Function 单元测试 |

### 4.2 页面一览

| # | 页面组件 | 核心场景 | 设计要点 |
|---|---------|---------|---------|
| 1 | **[HomePage](h5/src/components/HomePage.tsx)** | 扫码进入 → 显示车辆上下文 → 开始反馈 | URL 参数预填车辆信息（车牌/车型/城市/点位），卡车图标 + 品牌色 Banner |
| 2 | **[FeedbackForm](h5/src/components/FeedbackForm.tsx)** | 用户填写反馈正文 + 分类 + 联系方式 | 5-500 字字数统计、6 个快捷标签（急停/绕路/颠簸/关不上门/态度/其他）、5 类问题分类选择、折叠式选填（姓名/电话/位置/允许联系） |
| 3 | **[SubmittingPage](h5/src/components/SubmittingPage.tsx)** | 提交中 → AI 分析 → 生成工单（4步动画）| 主旋转圈 + 脉冲环 + 扫描光效，提交内容预览（>50字截断）|
| 4 | **[ResultPage](h5/src/components/ResultPage.tsx)** | 提交成功 → 显示工单号 + AI 结论 | ✅ 对勾动画 + 彩带、P0-P3 优先级颜色头卡、工单号一键复制、响应时间映射（P0=5min / P1=30min / P2=2h / P3=24h） |
| 5 | **[ErrorPage](h5/src/components/ErrorPage.tsx)** | 提交失败 → 重试引导 / 降级人工 | 错误原因 + 已重试次数，"本地已保存你的反馈"提示（给用户安全感），**连续失败 ≥ 3 次弹出红色客服卡片**（400电话 + 微信一键复制） |
| 6 | **[DebugPanel](h5/src/components/DebugPanel.tsx)** | 演示辅助 + 开发调试 | 页面右下角 🐛 瓢虫按钮打开，实时日志流（info/success/warn/error 4 级别）+ 4 模式按钮切换（成功/断网/500/超时）+ 日志计数 + 错误角标 |

全局状态集中在 [App.tsx](h5/src/App.tsx)，页面切换 `page: 'home' | 'form' | 'submitting' | 'result' | 'error'`。

### 4.3 一车一码参数用法

用户扫描贴在车身上的二维码 → 浏览器带参数打开 H5，自动预填上下文：

```
https://your-domain.com/
  ?vid=NEOLIX001      # 车辆编号（必填）
  &model=新石器X3     # 车型（选填）
  &city=北京           # 所在城市（选填）
  &loc=望京SOHO       # 具体位置（选填）
```

### 4.4 AI 分类 & 优先级规则（Mock）

**演示模式（USE_REAL_API=false）下本地模拟 AI 分析逻辑**：

| 匹配关键词示例 | 分类 | 优先级 | 预计响应时间 |
|---------------|------|--------|-------------|
| 碰撞 / 事故 / 危险 / 撞到 / 压到 / 刮擦 / 翻车 | 安全 | **P0** | 5 分钟内 |
| 故障 / 坏了 / 打不开 / 趴窝 / 失灵 / 没电 / 卡住 | 故障 | **P1** | 30 分钟内 |
| 投诉 / 不满 / 太差 / 赔偿 / 说法 | 投诉 | **P1** | 30 分钟内 |
| 建议 / 希望 / 能不能 / 优化 / 改进 | 建议 | **P3** | 24 小时内 |
| 其他（无关键词命中） | 体验 | **P2** | 2 小时内 |

成功后生成**伪工单号**格式：`NEO + YYYYMMDD + 4 位随机数`，例如 `NEO202608091234`。

### 4.5 调试面板 & 失败场景模拟

两种方式切换 Mock 模式：

**方式 A：URL 参数（分享链接用）**
| URL | 触发场景 | 前端提示 |
|-----|---------|---------|
| `?mock=network` 或 `?mock=fail` | 模拟断网 | "网络连接失败，请检查网络设置后重试" |
| `?mock=server` 或 `?mock=500` | 模拟服务器 500 | "服务器异常，请稍后重试或联系管理员" |
| `?mock=timeout` | 模拟 8 秒超时 | "请求超时，请检查网络信号后重试" |

**方式 B：调试面板按钮（现场演示用）**
点击页面右下角 🐛 瓢虫按钮 → 顶部 4 个按钮点一下就切换，面板内还能看到实时日志流。

### 4.6 连续失败 3 次降级策略

失败计数逻辑在 [App.tsx `handleSubmit` 回调](h5/src/App.tsx)：

```
失败 +1 → 失败 ≥ 3 次？
  ├── 是 → ErrorPage 显示红色"建议联系人工客服"卡片
  │         客服电话 400-xxx-xxxx  ✂ 一键复制
  │         客服微信 Neolix-Support ✂ 一键复制（含 execCommand 降级方案）
  │
  └── 否 → 仅显示重试按钮

成功一次 → 失败计数自动 reset = 0
```

---

## 五、后端：Vercel Serverless Function × 飞书 API

> 为什么用 Serverless Function？
> - **零运维**：不用买服务器、不用装 Nginx、不用管 SSL
> - **按需计费**：免费额度够用，没流量就不花钱
> - **密钥安全**：SECRET 只在 Node 环境读，不会打包进前端 bundle 泄露
> - **部署简单**：跟前端一起 `vercel --prod`，代码推上去 30 秒完事

### 5.1 数据流向图

```
H5 React 前端 submitFeedback()  [h5/src/api.ts]
  │
  ├─┬─ VITE_USE_REAL_API=false（默认，演示用）
  │ │   └─→ simulateAIAnalysis() 本地关键词匹配，2500ms 返回伪工单号
  │ │
  │ └─ VITE_USE_REAL_API=true（生产）
  │     └─→ fetch POST ${VITE_FEISHU_API_BASE}/api/submit
  │            └─ AbortController 15s 超时 + 4 类差异化错误提示
  │
  └─────────────────────────┐
                            ▼
        Vercel Serverless Function  [h5/api/submit.ts]
          1. CORS 预检处理（OPTIONS → 204）
          2. 方法校验（非 POST → 405）
          3. 体大小限制（>10KB → 413）
          4. 环境变量校验（缺BITABLE_APP_TOKEN/TABLE_ID → 500）
          5. 解析 JSON + 必填字段校验（缺 vehicle_id/content_raw → 400）
          6. getTenantToken()  ← 飞书鉴权接口，10s 超时
          7. buildFields()   ← 构建 9 列字段 Schema
          8. createRecord()  ← bitable/v1 写入工单，10s 超时
          9. 返回标准化 JSON（成功 200 / 超时 504 / 飞书错 500）
                            │
                            ▼
                  飞书多维表格工单池
                  columns: vehicle_id | content_raw | category | channel(车身扫码)
                           | status(待处理) | contact_name/phone | location_detail
```

### 5.2 submit.ts 执行流程

| 步骤 | 操作 | 失败返回 | 耗时限制 |
|------|------|---------|---------|
| 1 | OPTIONS 预检 | 204（成功，仅返回 CORS 头）| — |
| 2 | `request.method !== 'POST'` | **405** 方法不允许 | — |
| 3 | `Content-Length > 10000` | **413** 请求体过大 | — |
| 4 | 缺 `process.env.BITABLE_APP_TOKEN` 或 `TABLE_ID` | **500** 多维表格配置缺失 | — |
| 5 | JSON 解析 + 字段校验：`vehicle_id.trim()` 或 `content_raw.trim()` 空 | **400** 缺少必填字段 | — |
| 6 | `getTenantToken()` 调飞书 `/auth/v3/tenant_access_token/internal` | HTTP 非 2xx → **500**；`code != 0` → **500**；AbortError → **504** | **10s** 超时 |
| 7 | `buildFields()` 构建 fields dict，boolean 转 "是"/"否" | — | — |
| 8 | `createRecord()` 调飞书 `/bitable/v1/apps/{token}/tables/{id}/records` | HTTP 非 2xx → **500**；`code != 0`（如 91402 未加协作者）→ **500**；AbortError → **504** | **10s** 超时 |
| 9 | 返回 200 + 标准化工单结果 | — | — |

### 5.3 字段映射关系

| 前端提交 `FeedbackSubmitData` | Serverless 处理 | 飞书多维表格列名 | 默认值 |
|-------------------------------|----------------|------------------|--------|
| `vehicle_id` (string) | 直接传递 | `vehicle_id` | **必填** |
| `content_raw` (string) | 直接传递 | `content_raw` | **必填** |
| `category?` (string) | 可选，存在才写入 | `category` | 不填则后续 AI 自动打标 |
| `contact_name?` (string) | 可选 | `contact_name` | — |
| `contact_phone?` (string) | 可选 | `contact_phone` | — |
| `contact_allowed?` (boolean) | `true → '是'` / `false → '否'` | `contact_allowed` | — |
| `location_detail?` (string) | 可选 | `location_detail` | — |
| — | **固定值** `'车身扫码'` | `channel` | 来源渠道标识 |
| — | **固定值** `'待处理'` | `status` | 工单初始状态 |

### 5.4 错误码体系

| HTTP | 内部触发条件 | 返回 JSON | 前端展示提示 |
|------|-------------|-----------|-------------|
| **200** | 正常写入多维表格 | `{ ticket_id, category, priority, summary, estimated_response_time, status }` | 跳转结果页，显示工单号 + AI 摘要 |
| **400** | 缺 vehicle_id / content_raw 或空字符串 / JSON 解析失败 | `{ error: "缺少必填字段 vehicle_id 和 content_raw" }` | （前端表单已拦截，一般不会触发）|
| **405** | 请求 method 不是 POST/OPTIONS | `{ error: "仅支持 POST 请求" }` | — |
| **413** | 请求体大小 > 10 KB | `{ error: "请求体过大，请缩短反馈内容后重试" }` | 直接显示提示 |
| **500** | 飞书返回 code ≠ 0（如 91402 未加协作者、10001 密钥错）| `{ error: "服务器错误: 飞书鉴权失败 (code=10001)..." }` | "服务器异常，请稍后重试或联系管理员" |
| **504** | AbortController 触发 10s 超时（AbortError）| `{ error: "飞书API响应超时，请稍后重试" }` | "服务器响应超时，请稍后重试" |

### 5.5 安全要点

1. **密钥不进前端 bundle**：`FEISHU_APP_SECRET` 只通过 Vercel 环境变量注入 Serverless 运行时，前端打包产物里搜索不到任何 secret
2. **请求体 DoS 防护**：`Content-Length > 10KB` 直接在步骤 3 返回 413，不走飞书 API，避免超大 body 拖垮函数计费
3. **CORS 预检显式处理**：OPTIONS 返回 204 + 标准 CORS 头，生产环境可把 `*` 收紧为具体域名
4. **日志脱敏**：console.log 只打 `vehicle_id`、`body.length` 这种非敏感元数据，绝不打用户的 `content_raw` 全文和 `contact_phone`
5. **双层超时**：前端 15s + 后端 10s，任何一层卡住都会被 AbortController 及时中止

---

## 六、双模式切换（Mock / 真实 API）

```
h5/.env.local 里的 VITE_USE_REAL_API 决定：
  │
  ├── false（默认值，.env.example 就这么写）
  │     ├── 优点：零配置、打开即演示、可断网演示、可模拟 4 种失败场景
  │     ├── 适用场景：比赛现场 Demo、UI 调试、前端开发
  │     └── 工单号：NEO + 日期 + 4 位随机（伪）
  │
  └── true
        ├── 优点：真实写入飞书多维表格工单池，ticket_id = 飞书 record_id
        ├── 适用场景：生产环境、真实用户反馈、联调测试
        └── 前置条件：Vercel 配好 4 个密钥（FEISHU_APP_ID / FEISHU_APP_SECRET /
                    BITABLE_APP_TOKEN / BITABLE_TABLE_ID），参见第七章
```

**为什么设计成双模式？**
- 演示环境往往信号差 + 不能配密钥，必须能"开箱即用"
- 生产环境要真实写入工单池
- 一行环境变量切换，代码零改动，方便对比

---

## 七、环境变量总表（6 个）

### 第 1 组 · H5 前端环境变量（写在 `h5/.env.local`，开发者本地配）

| 变量名 | 说明 | 可选值 | 默认值 |
|--------|------|--------|--------|
| **`VITE_USE_REAL_API`** | 是否调用真实 Serverless Function | `'true'` / `'false'` | `'false'` |
| **`VITE_FEISHU_API_BASE`** | API 基础前缀（跨域部署时填 Vercel 域名）| 留空（同域）或 `https://xxx.vercel.app` | 留空 |

### 第 2 组 · Vercel 平台环境变量（在 vercel.com Dashboard 配置，绝不进代码）

| 变量名 | 说明 | 来源渠道 |
|--------|------|---------|
| **`FEISHU_APP_ID`** | 飞书自建应用 App ID | 飞书开发者后台 → 凭证与基础信息 |
| **`FEISHU_APP_SECRET`** | 飞书自建应用 App Secret | 同上，**泄露=失去对应用的控制权**，高度敏感 |
| **`BITABLE_APP_TOKEN`** | 工单多维表格的 app_token | 打开飞书多维表格 → URL 中 `/base/` 后面那段（到下个 `/` 之前）|
| **`BITABLE_TABLE_ID`** | 工单数据表的 table_id | 同一 URL 中 `table=` 参数的值 |

> 💡 提醒：多维表格 → 更多 → 添加协作者 → 把飞书自建应用加为协作者（只读不够，需可编辑），否则飞书 API 会报 `code=91402`。

---

## 八、部署说明

### 8.1 GitHub Actions CI / CD

每次 push 或提 PR 自动触发，配置文件 [`.github/workflows/ci.yml`](.github/workflows/ci.yml)：

| Job | 环境 | 做什么 | 通过条件 |
|-----|------|--------|---------|
| **h5-build** | `ubuntu-latest` + Node 20 | `cd h5 && npm ci && npx tsc --noEmit && npm run build` | TypeScript strict 零报错 + Vite 构建成功 |
| **python-check** | `ubuntu-latest` + Python 3.11 | `find . -name "*.py" -not -path "./.git/*" \| xargs python -m py_compile` | 所有 Python 文件语法正确 |

构建产物自动保留 7 天作审计；PR 页会显示 **All checks have passed** 绿标。

### 8.2 Vercel 生产部署

[`vercel.json`](vercel.json) 已配好，一条命令搞定：

```bash
# 仓库根目录执行
cd feishu-neolix-AIfeedback

# 首次部署（会引导关联项目）
vercel

# 后续正式生产部署
vercel --prod
```

部署完成会得到：
- 前端：`https://your-project.vercel.app/` → 扫码后给用户用
- API：`https://your-project.vercel.app/api/submit` → H5 前端调用（同域，无 CORS 烦恼）

---

## 九、验证方式（3 种）

### 9.1 跑单元测试（17 项全通过）

```bash
cd h5
npm test
```

预期输出：`ℹ tests 17 | suites 1 | pass 17 | fail 0`

**覆盖范围（17 项分 9 组）**：
- ✅ 正常提交流程（完整 / 仅必填 / contact_allowed=false）× 3
- ✅ 环境变量缺失（缺 BITABLE_APP_TOKEN）→ 500 × 1
- ✅ 必填字段校验（缺 vehicle_id / 缺 content_raw / body=null）× 3
- ✅ 飞书 API 异常（鉴权 code≠0 / 鉴权 HTTP 500 / 写入 code≠0）× 3
- ✅ 超时处理（鉴权 AbortError → 504 / 写入 AbortError → 504）× 2
- ✅ HTTP 方法（OPTIONS 204 / GET 405）× 2
- ✅ 请求体大小（10KB+ → 413）× 1
- ✅ 响应格式校验（成功字段全 / 错误含 error 字段）× 2

### 9.2 本地 Demo 演示（无需密钥）

```bash
cd h5
npm install
npm run dev
```

打开 `http://localhost:3000/?vid=NX-TEST-001&city=北京&loc=望京SOHO` 就能跑。

**推荐演示 4 个场景**：
1. 正常提交 → 看 P0-P3 优先级颜色 + 工单号复制
2. 🐛 调试面板切「断网」模式 → 提交失败 → 按重试 3 次 → 看红色客服降级卡片
3. 再切回「成功」模式 → 重试一次 → 跳成功页，失败计数自动清零
4. `window.__setMockMode('timeout')` → 看超时提示

### 9.3 真实飞书 API 联调（vercel dev）

6 步从零到真写入飞书（详见 [`LOCAL_TEST_GUIDE.md`](LOCAL_TEST_GUIDE.md)）：

```bash
# 1. 安装 Vercel CLI
npm i -g vercel

# 2. 关联项目（选正确的团队和项目）
vercel link

# 3. 在 vercel.com Dashboard 配置 4 个密钥：
#    FEISHU_APP_ID / FEISHU_APP_SECRET / BITABLE_APP_TOKEN / BITABLE_TABLE_ID

# 4. 把远端配置拉到本地 .env.local
vercel env pull .env.local

# 5. 开启本地 Vercel dev server（前后端一起）
vercel dev
#   → http://localhost:3000

# 6. 提交反馈 → 打开飞书多维表格，确认是否多了一条 record_id 匹配的记录
```

---

## 十、CHANGELOG 摘要 · v1.0.0

> 完整变更日志见 [`CHANGELOG.md`](CHANGELOG.md)（Keep a Changelog 1.1.0 规范，Added / Fixed / Changed / Documentation 四大类 142 行）。

### 本次里程碑交付

| 维度 | 交付内容 |
|------|---------|
| **📱 前端** | 5 页面（首页/表单/AI分析中/结果/错误）+ 调试面板 + 日志系统 + Mock AI 分类 + 双模式切换 + 连续失败 3 次降级 |
| **🔌 后端** | Vercel Serverless Function 对接飞书 bitable/v1 + 9 字段映射 + 400/405/413/500/504 六错误码 + 双层超时 + 日志脱敏 |
| **🧪 测试** | 17 项后端单元测试（全部通过） |
| **🛠️ 配置** | vercel.json + Vite + TypeScript + TailwindCSS 品牌色板 + CI/CD 流水线 + 27 条 gitignore |
| **📄 文档** | CHANGELOG + 根 README（本文件，一站式） + h5/README + H5_FEATURE_SPEC_CodeReview + LOCAL_TEST_GUIDE + DEMO_GUIDE（5 份）|
| **🐛 修复** | logger TS2352 类型错 / favicon 404 / 移动端视口适配 / 请求体大小限制 / HTTP status 检查 / 环境变量校验 等 13 项 |

---

## 十一、文档索引（5 份配套文档）

按"什么人 → 看什么"分：

| 角色 | 看什么文档 | 内容 |
|------|-----------|------|
| **Code Reviewer** | **[`docs/H5_FEATURE_SPEC.md`](docs/H5_FEATURE_SPEC.md)** | 新增功能 + 31 个新增文件分类清单 + 验证方式 |
| **比赛现场 Demo** | **[`h5/DEMO_GUIDE.md`](h5/DEMO_GUIDE.md)** | 手机访问步骤 + 4 个演示场景脚本 |
| **联调开发** | **[`LOCAL_TEST_GUIDE.md`](LOCAL_TEST_GUIDE.md)** | 6 步 vercel dev + 真实飞书 API 联调 + 常见问题排查 |
| **深度维护** | **[`h5/README.md`](h5/README.md)** | 架构图 + 环境变量 + 字段映射 + 错误码 + 部署步骤 |
| **版本追溯** | **[`CHANGELOG.md`](CHANGELOG.md)** | 每次版本所有 Added/Fixed/Changed/Documentation 完整清单 |

---

## 十二、协作约定

1. 每人只改自己负责目录里的文件，直接在 `main` 分支提交推送。
2. Python 统一 3.11+，新增依赖写入 `requirements.txt`。
3. 密钥一律写本地 `.env`（已 git 忽略），**禁止提交真实密钥**；新增配置项时同步更新 `.env.example`。
4. 工单数据字段以团队技术方案中的 Schema 为唯一标准，改字段需三人同意。

---

**版本**：`1.0.0` (2026-08-09) · 首次完整交付
**PR 分支**：`feature/h5-feedback-page` → [查看 PR](https://github.com/AGD-h/feishu-neolix-AIfeedback/pull/1)