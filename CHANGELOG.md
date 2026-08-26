# Changelog

本项目的所有重要变更都会记录在这个文件中。
格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0)，
本项目遵循 [语义化版本（Semantic Versioning）](https://semver.org/lang/zh-CN/)。

---

## [1.0.0] — 2026-08-09

> 🎉 **H5 模块首次完整交付** — 一车一码扫码反馈页（前端 5 页面 + Vercel Serverless Function 对接飞书多维表格）完整实现、测试、文档均已就绪。
> 对应 PR 分支：`feature/h5-feedback-page`

### Added — 新增功能

#### 📱 前端：一车一码 AI 反馈 H5（React 18 + TS + Vite + TailwindCSS）

- **5 个完整页面**
  - 首页 `HomePage`：展示扫码解析的车辆上下文（vid / 车型 / 城市 / 点位）、功能亮点介绍、开始反馈入口
  - 反馈表单 `FeedbackForm`：5-500 字文本域 + 字数统计 + 6 个快速问题标签 + 5 类问题分类选择 + 折叠式选填联系方式（姓名/电话/位置/允许联系）+ 字段校验
  - AI 分析中 `SubmittingPage`：4 步进度条动画（提交反馈 → AI 语义分析 → 识别分类优先级 → 生成工单通知负责人）+ 脉冲扫描光效
  - 结果页 `ResultPage`：成功对勾动画 + 彩带、P0-P3 优先级头卡（颜色区分）、工单号一键复制、AI 摘要、分享/复制按钮、优先级→响应时间映射（P0=5min / P1=30min / P2=2h / P3=24h）
  - 错误页 `ErrorPage`：失败提示 + 已重试次数、本地保存提示、**连续失败 ≥ 3 次弹出红色客服降级卡片**（400 电话 + 微信 Neolix-Support 均支持一键复制，含 `document.execCommand` 降级复制方案）
- **调试面板 `DebugPanel`**：页面右下角 🐛 瓢虫按钮触发，支持实时日志流查看（4 级别）+ 4 种 Mock 模式切换（成功/断网/500/超时）+ 日志计数 + 错误角标 + 清空/展开/收起
- **日志系统 `utils/logger.ts`**：4 级别 Logger（info/success/warn/error），同时写入内存环形队列 + 控制台 + 订阅者模式（供 DebugPanel 实时刷新），全局可通过 `(window as any).__logger` 访问
- **Mock AI 分类引擎（本地演示专用）**：`simulateAIAnalysis()` 5 类关键词匹配规则
  - 安全类（碰撞/事故/危险/撞到/压到/刮擦/翻车）→ P0 优先级
  - 故障类（故障/坏了/打不开/趴窝/失灵/没电/卡住）→ P1 优先级
  - 投诉类（投诉/不满/太差/赔偿/说法）→ P1 优先级
  - 建议类（建议/希望/能不能/优化/改进）→ P3 优先级
  - 其他（默认）→ 体验类 P2
- **双模式切换（`USE_REAL_API` 开关）**
  - `VITE_USE_REAL_API=false`（默认）：本地 Mock，无需网络和密钥，模拟延迟 2500ms 生成 `NEO+YYYYMMDD+4位随机数` 伪工单号
  - `VITE_USE_REAL_API=true`：真实调用 `/api/submit`（Serverless Function），`ticket_id` 为飞书多维表格 `record_id`
- **URL 参数失败场景模拟**：`?mock=network`（断网）、`?mock=server`/`?mock=500`（服务端错误）、`?mock=timeout`（8s 超时），调试面板也提供对应按钮

#### 🔌 后端：Vercel Serverless Function（对接飞书 API）

- **`h5/api/submit.ts`** — 接收 H5 POST 请求并写入飞书多维表格工单池
  - 请求校验：`method=POST` 校验（非 POST 返回 405）、`Content-Length>10KB` 返回 413（防 DoS）、缺失 `BITABLE_APP_TOKEN/TABLE_ID` 返回 500
  - 字段校验：缺 `vehicle_id` 或 `content_raw` 返回 400
  - 飞书鉴权：`POST /auth/v3/tenant_access_token/internal` 用 `FEISHU_APP_ID/SECRET` 换 `tenant_access_token`，带 10s `AbortController` 超时 + HTTP status 校验 + `code==0` 校验
  - 字段构建 `buildFields()`：9 字段映射（vehicle_id / content_raw / category / contact_name / contact_phone / contact_allowed / location_detail / channel=车身扫码 / status=待处理），`contact_allowed` boolean→"是"/"否"转换
  - 工单写入：`POST /bitable/v1/apps/{token}/tables/{id}/records` 新增记录，同样带 10s `AbortController` 超时 + HTTP status 校验 + `code==0` 校验
  - 统一错误响应：超时 → `504 飞书API响应超时`、飞书 code≠0（如 91402 未加协作者、10001 密钥错）→ `500 服务器错误`
  - CORS 预检处理：`OPTIONS` 返回 `204`，响应头含 `Access-Control-Allow-Origin: *`
  - 生产日志：成功/失败均打 console.log，含耗时 `ms` 和非敏感元数据（只打 vehicle_id、内容长度，不打 contact_phone 和 content_raw 全文脱敏）

#### 🧪 单元测试（17 项，全通过）

- **`h5/api/submit.test.ts`**（使用 Node.js 22+ 原生 `node:test` runner，`--experimental-strip-types`）
  - 正常提交流程 × 3：完整成功 / 仅必填字段 / `contact_allowed=false`
  - 环境变量校验 × 1：缺 `BITABLE_APP_TOKEN` → 500
  - 必填字段校验 × 3：缺 `vehicle_id` / 缺 `content_raw` / body=null
  - 飞书 API 错误 × 3：鉴权 code≠0 / 鉴权 HTTP 500 / 写入 code≠0
  - 超时处理 × 2：鉴权 AbortError → 504 / 写入 AbortError → 504
  - HTTP 方法 × 2：OPTIONS 204 / GET 405
  - 请求体大小 × 1：10KB+ → 413
  - 响应格式 × 2：成功响应字段完整 / 错误响应含 error 字段

#### 🚀 CI / CD

- **GitHub Actions 流水线（`.github/workflows/ci.yml`）**：`push` 和 `pull_request` 自动触发
  - Job `h5-build`：`ubuntu-latest` + Node 20，执行 `cd h5 && npm ci && npx tsc --noEmit && npm run build`，类型检查 + 构建产物保留 7 天
  - Job `python-check`：`ubuntu-latest` + Python 3.11，`find . -name "*.py" -not -path "./.git/*" | xargs python -m py_compile` 全仓库 Python 语法检查

#### ⚙️ 构建与部署配置

- **`vercel.json`**：Vercel 生产部署配置
  - `installCommand: cd h5 && npm install`
  - `buildCommand: cd h5 && npm install && npm run build`
  - `outputDirectory: h5/dist`
  - Serverless Functions 路由：`api/*.ts` 自动识别（Vercel Edge Functions / Serverless Functions 默认规则）
- **`h5/package.json`**：新增 `@types/node` devDependency，新增 `test` / `test:watch` 脚本
- **`h5/tsconfig.node.json`**：新增 `include: ["vite.config.ts", "api/*.ts"]` + `types: ["node"]`，为 submit.ts 提供 Node 类型
- **`h5/vite.config.ts`**：dev server `host: true` + `port: 3000`，手机局域网可访问
- **`h5/index.html`**：viewport 移动端适配（`viewport-fit=cover`, `maximum-scale=1`），favicon 改为 SVG
- **`h5/public/favicon.svg`**：新石器品牌色 + Truck 图标 SVG favicon（修复图片 404）

---

### Fixed — 修复

#### H5 前端修复

- **`logger.ts` TS2352 类型转换错误**：将 `(window as Record<string, unknown>).__logger = logger` 改为 `(window as unknown as Record<string, unknown>).__logger`（双重断言通过 strict 类型检查）
- **favicon 404**：原 `index.html` 引用 `/favicon.ico` 不存在，改为 SVG favicon + 本地文件
- **响应式视口适配**：原 viewport 缺 `viewport-fit=cover`，刘海屏/全面屏安全区未适配；补充 `viewport-fit=cover` + `maximum-scale=1`
- **`api.ts` 差异化错误提示**：原所有错误都弹统一文案，现拆分 4 类提示
  - `TypeError`（无网络）→ "网络连接失败，请检查网络设置后重试"
  - status=504 / 信息含"超时" → "服务器响应超时，请稍后重试"
  - 5xx 类 → "服务器异常，请稍后重试或联系管理员"
  - 其他 → `${serverError || '提交失败'}，请稍后重试`
- **前端 15s 超时**：新增 `AbortController` 信号，避免用户长时间等待

#### Serverless Function 修复

- **超时控制**：原 `submit.ts` 未设置 fetch 超时，飞书 API 异常时函数长时间挂起；新增 10s 超时 + AbortError 捕获返回 504
- **HTTP status 检查**：原只判断 `resp.json().code`，HTTP 5xx / 4xx 时 JSON 解析可能异常；新增 `if (!resp.ok) throw new Error(...)` 先拦截非 2xx
- **请求体大小限制**：原无上限可能被 DoS 攻击；新增 `Content-Length>10000` → 413 直接拒绝
- **环境变量缺失报错**：原无显式校验；新增 `BITABLE_APP_TOKEN / TABLE_ID` 缺省返回 500 "多维表格配置缺失"
- **必填字段校验**：原依赖前端校验，后端补 `vehicle_id / content_raw` 双保险校验 + 空字符串校验

#### 仓库级修复

- **`.gitignore` 扩充 21 条忽略规则**：补充 Python (`__pycache__/` / `.pytest_cache/` / `*.pyc`)、Node (`node_modules/` / `npm-debug.log*`)、Vite (`dist/` / `.vite/`)、IDE (`.idea/` / `.vscode/` / `.DS_Store`)、日志 (`*.log`)、AI 工具缓存目录 (`.agents/` / `.junie/` / `.qoder/` / `.trae/` 等 11 条)
- **仓库清理（移除误提交的 AI 缓存）**：删除 `.agents/`、`.junie/`、`.qoder/`、`.trae/` 四个 AI 助手缓存目录（数百个多余文件），保留源码与正常工作文件

---

### Changed — 变更

- **`h5/.env.example`**：废弃旧变量 `VITE_BITABLE_APP_TOKEN` / `VITE_BITABLE_TABLE_ID`，替换为新变量
  - `VITE_USE_REAL_API=true|false` — 模式开关
  - `VITE_FEISHU_API_BASE=` — 部署域名（留空=同域）
- **`h5/src/api.ts` 提交逻辑**：原单一路径，改为 `USE_REAL_API` 双分支切换；错误处理拆分 4 类；新增 15s `AbortController`
- **根目录 `README.md`**：原极简 5 行描述 → 扩充"h5/ 模块详细说明"章节（技术栈表 / 功能清单 / 数据流向图 / 部署形态 / 4 个文档入口链接）

---

### Documentation — 新增文档

| 文档 | 内容 |
|------|------|
| **[`h5/README.md`](h5/README.md)**（完全重写，216 行） | H5 架构总览 ASCII 框图、功能模块表、6 环境变量总表（前端 2 + Vercel 4）+ 切换逻辑树、9 字段映射关系表、6 错误码表（200/400/405/413/500/504）、失败场景模拟 URL 参数表、vercel.json 配置解读、构建部署步骤 |
| **[`h5/DEMO_GUIDE.md`](h5/DEMO_GUIDE.md)**（新增） | 演示操作手册：手机访问方法（Android/iOS）、4 个演示场景（正常提交流程 / 网络错误重试 / 超时场景 / 连续失败 3 次降级人工客服）、调试面板使用说明、二维码生成说明 |
| **[`LOCAL_TEST_GUIDE.md`](LOCAL_TEST_GUIDE.md)**（新增） | 本地模拟生产环境 6 步全流程测试：Vercel CLI 安装 → 项目关联 → Dashboard 配 4 密钥 → `vercel env pull` → `vercel dev` 本地联调 → `vercel --prod` 生产部署；含常见问题排查（91402 未加协作者、10001 密钥错、TypeScript 类型错、构建产物缺失、域名未生效） |
| **[`docs/H5_FEATURE_SPEC.md`](docs/H5_FEATURE_SPEC.md)**（新增） | Code Review 专用说明：5 模块总览、前端每个页面设计要点表、submit.ts 执行流程图 + 字段映射 + 错误码 + 安全要点、**31 个新增文件分类清单**（前端/后端/配置/文档）、4 种 reviewer 验证方式（npm test / dev demo / vercel 联调 / CI 绿标）、4 条已知限制和后续优化点、PR 8 个 commit 完整列表 |
| **根目录 `README.md`** | "开发与联调"新增 4 个文档入口跳转链接 |

---

## 格式说明

- 变更分类严格遵循：**Added**（新增）/ **Changed**（变更）/ **Deprecated**（弃用，暂无）/ **Removed**（移除，暂无）/ **Fixed**（修复）/ **Security**（安全，暂无）/ **Documentation**（文档）
- 版本号遵循 SemVer：`MAJOR.MINOR.PATCH`
  - MAJOR：不兼容的 API 变更
  - MINOR：向后兼容的功能新增
  - PATCH：向后兼容的错误修复

[1.0.0]: https://github.com/AGD-h/feishu-neolix-AIfeedback/pull/1