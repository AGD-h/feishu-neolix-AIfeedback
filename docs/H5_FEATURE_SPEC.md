# H5 前后端新增功能说明（for Code Review）

> 本文档汇总本次 PR 中 H5 模块新增的全部功能、文件、配置变更和验证方式，
> 方便 reviewer 快速查阅。对应分支：`feature/h5-feedback-page`

---

## 1. 功能总览

本次 PR 在 H5 方向上实现了 **"一车一码扫码反馈页 + Vercel Serverless Function 对接飞书多维表格"**，
核心交付物可分为 5 大块：

| # | 模块 | 说明 | 关键文件 |
|---|------|------|---------|
| 1 | 📱 H5 前端（5 页面 + 调试面板） | React 18 + TS + TailwindCSS + Framer Motion，响应式移动端页面 | `src/components/*.tsx` |
| 2 | 🏷️ 前端本地 Mock AI 分析 | 5类关键词匹配 + 4级优先级，不依赖后端即可演示 | `src/api.ts` (simulateAIAnalysis) |
| 3 | 🔌 Serverless Function（真实后端） | Vercel 无服务器函数，调用飞书 API 写入多维表格 | `api/submit.ts` |
| 4 | 🛡️ 错误处理 & 降级机制 | 超时控制、错误码体系、连续失败 3 次降级人工客服 | `api/submit.ts` + `src/api.ts` + `ErrorPage.tsx` |
| 5 | 🧪 单元测试 & 部署配置 & CI | 17项单元测试、vercel.json、GitHub Actions CI | `api/submit.test.ts`、`vercel.json`、`.github/workflows/ci.yml` |

---

## 2. 前端功能明细

### 2.1 页面一览

| 页面 | 文件 | 核心功能 | 设计要点 |
|------|------|---------|---------|
| **首页 HomePage** | `src/components/HomePage.tsx` | 展示车辆信息（车牌/车型/城市/点位）、功能亮点、开始反馈入口按钮 | URL 参数 ?vid= 预填车辆上下文，模拟扫码场景 |
| **反馈表单 FeedbackForm** | `src/components/FeedbackForm.tsx` | ① 文本域 + 字数统计(5-500字) ② 6个快速问题标签 ③ 5类问题分类选择 ④ 联系方式选填(姓名/电话/位置/允许联系) | 字段校验(content<5字标红)、分类选中态颜色区分、折叠式高级选填 |
| **AI分析中 SubmittingPage** | `src/components/SubmittingPage.tsx` | 4步进度条动画（1.提交反馈 2.AI语义分析 3.识别分类优先级 4.生成工单通知负责人） | 主旋转圈+脉冲环+扫描光效，内容长度>50截断预览 |
| **结果页 ResultPage** | `src/components/ResultPage.tsx` | ① 成功对勾动画+彩带 ② P0-P3优先级头卡（颜色区分） ③ 工单号（一键复制） ④ AI摘要 ⑤ 分享/复制按钮 | 优先级→响应时间映射：P0-5min P1-30min P2-2h P3-24h |
| **错误页 ErrorPage** | `src/components/ErrorPage.tsx` | ① 失败提示+已重试次数 ② 本地保存提示（给用户安全感）③ 连续失败≥3次弹出红色客服卡片 ④ 重新提交 / 返回首页按钮 | 客服电话(400-xxx-xxxx) + 微信(Neolix-Support) 均支持一键复制，含降级复制方案(document.execCommand) |
| **调试面板 DebugPanel** | `src/components/DebugPanel.tsx` | ① 实时日志流（4级别 info/success/warn/error） ② 4模式切换（成功/断网/500/超时）③ 日志计数+错误角标 ④ 清空/展开/收起 | 右下角瓢虫🐛按钮触发，Demo演示必备工具 |

### 2.2 状态管理（App.tsx）

单文件集中式状态（无 Redux/Zustand，用 useState 足够）：

```
useState<AppPage> page        — 页面切换：home/form/submitting/result/error
useState<QRCodeData> qrData  — 扫码解析的车辆上下文
useState<FeedbackSubmitData> — 待提交的表单数据（失败重试用）
useState<FeedbackResult>     — 提交成功返回的工单结果
useState<string> errorMsg    — 错误提示文案
useState<number> failCount   — 连续失败计数（成功→清零，失败→+1，≥3→触发降级）
```

### 2.3 前端本地 Mock 模式（VITE_USE_REAL_API=false，默认）

无需任何后端即可完整演示整个流程：

**AI 关键词分类规则**（在 `api.ts::simulateAIAnalysis` 中）：

| 匹配关键词示例 | 分类 | 优先级 | 响应时间 |
|---------------|------|--------|---------|
| 碰撞/事故/危险/撞到/压到/刮擦/翻车 | 安全 | P0 | 5 分钟内 |
| 故障/坏了/打不开/趴窝/失灵/没电/卡住 | 故障 | P1 | 30 分钟内 |
| 投诉/不满/太差/赔偿/说法 | 投诉 | P1 | 30 分钟内 |
| 建议/希望/能不能/优化/改进 | 建议 | P3 | 24 小时内 |
| 其他 | 体验 | P2 | 2 小时内 |

**Mock 模拟延迟**：2500ms（成功）/ 1200ms（断网）/ 1500ms（500）/ 8000ms（超时）

**工单号格式**：`NEO + YYYYMMDD + 4位随机数`（例如 `NEO202608091234`）

---

## 3. 后端功能明细（Vercel Serverless Function）

### 3.1 submit.ts 执行流程

```
handler(request)
  │
  ├─→ method == OPTIONS → 返回 204 CORS 预检
  │
  ├─→ method != POST → 返回 405 方法不允许（含日志）
  │
  ├─→ Content-Length > 10KB → 返回 413 请求体过大（防 DoS）
  │
  ├─→ BITABLE_APP_TOKEN/TABLE_ID 缺 → 返回 500 多维表格配置缺失
  │
  └─→ try {
        request.json() 解析 body
        ├─→ 缺 vehicle_id 或 content_raw → 返回 400 缺少必填字段
        │
        ├─→ getTenantToken()  （fetch 10s 超时 + HTTP状态码校验 + code==0 校验）
        │   └─→ 失败 → catch 返回 504 超时 / 500 其他错误
        │
        ├─→ buildFields(body)  （9字段构建，见下方字段映射表）
        │
        └─→ createRecord()  （fetch 10s 超时 + HTTP状态码校验 + code==0 校验）
            └─→ 成功 → 返回 200 + 标准化工单结果
                失败 → catch 返回 504 超时 / 500 其他错误
      }
```

### 3.2 字段映射关系（Schema）

| 前端提交 | SF 处理 | 写入飞书列 | 说明 |
|---------|--------|-----------|------|
| `vehicle_id` | 直接传递 | `vehicle_id` | 必填 |
| `content_raw` | 直接传递 | `content_raw` | 必填 |
| `category` | 可选→仅存在时写入 | `category` | 不填则后续AI自动打标 |
| `contact_name` | 可选 | `contact_name` | — |
| `contact_phone` | 可选 | `contact_phone` | — |
| `contact_allowed` | boolean→"是"/"否" | `contact_allowed` | — |
| `location_detail` | 可选 | `location_detail` | — |
| — | 固定值"车身扫码" | `channel` | 来源渠道标识 |
| — | 固定值"待处理" | `status` | 初始工单状态 |

### 3.3 错误码体系

| HTTP | 内部触发条件 | 返回 JSON | 前端提示 |
|------|-------------|-----------|---------|
| 200 | 正常写入 | `{ ticket_id, category, priority, summary, estimated_response_time, status }` | 跳转结果页 |
| 400 | 缺 vehicle_id / content_raw / JSON 解析失败 | `{ error: "缺少必填字段..." }` | 前端表单先拦截了，一般不会到这 |
| 405 | method != POST | `{ error: "仅支持 POST 请求" }` | — |
| 413 | Content-Length > 10000 | `{ error: "请求体过大，请缩短反馈内容" }` | 直接显示 |
| 500 | 飞书返回 code != 0（如 91402 未加协作者、10001 密钥错）| `{ error: "服务器错误: [xxx] ..." }` | "服务器异常，请稍后重试或联系管理员" |
| 504 | AbortError（10s 超时触发） | `{ error: "飞书API响应超时..." }` | "服务器响应超时，请稍后重试" |

### 3.4 安全要点

1. **密钥不进前端 bundle**：FEISHU_APP_SECRET 只在 Vercel 环境变量注入，`process.env` 只在 Node 环境读，H5 打包结果里没有
2. **请求体大小限制**：>10KB 直接返回 413，避免攻击者发超大 body 拖垮函数
3. **CORS 预检**：显式处理 OPTIONS + 响应头 `Access-Control-Allow-Origin: *`，当前允许全域名（后续上线可收紧为具体域名）
4. **日志脱敏**：日志只打 vehicle_id、内容长度等非敏感元数据，不打 contact_phone 和 content_raw 全文

---

## 4. 双模式切换逻辑

```
VITE_USE_REAL_API 环境变量决定模式：
  ├── false（默认）→ 前端 src/api.ts 走 Mock 模式
  │                     ├─ 本地 simulateAIAnalysis() 算分类/优先级
  │                     └─ 生成 NEO 前缀伪工单号
  │
  └── true             → 前端 fetch ${VITE_FEISHU_API_BASE}/api/submit
                         └─→ Vercel Serverless Function 真实写入飞书
                               └─ ticket_id = 飞书 record_id
```

**为什么设计成双模式？**
- 演示时不需要网络和真实密钥，打开即可演示
- 真实部署时一行配置切换，代码零改动
- 失败场景模拟（?mock= 或调试面板）只有 Mock 模式下生效

---

## 5. 新增文件清单（本 PR）

### 5.1 前端 H5 页面（首次引入）

| 文件 | 作用 |
|------|------|
| `h5/src/App.tsx` | 总入口，状态管理 + 页面路由切换 + 失败计数 |
| `h5/src/main.tsx` | React DOM 挂载 |
| `h5/src/index.css` | Tailwind 基础样式 + 自定义动画类 |
| `h5/src/types.ts` | FeedbackSubmitData / FeedbackResult 等 TypeScript 类型定义 |
| `h5/src/components/HomePage.tsx` | 首页 |
| `h5/src/components/FeedbackForm.tsx` | 反馈表单 |
| `h5/src/components/SubmittingPage.tsx` | AI分析中动画 |
| `h5/src/components/ResultPage.tsx` | 提交成功结果 |
| `h5/src/components/ErrorPage.tsx` | 提交失败重试 & 连续失败降级 |
| `h5/src/components/Header.tsx` | 品牌 Header |
| `h5/src/components/DebugPanel.tsx` | 调试面板（日志 + Mock 切换） |
| `h5/src/utils/logger.ts` | 4 级别 Logger（内存队列 + 控制台 + 订阅者） |
| `h5/src/api.ts` | submitFeedback() 提交入口（Mock/真实切换 + 15s 超时 + 错误差异化提示） |

### 5.2 Serverless Function + 测试

| 文件 | 作用 |
|------|------|
| `h5/api/submit.ts` | Vercel Serverless Function，飞书 API 对接核心 |
| `h5/api/submit.test.ts` | 17 项单元测试（Node.js 原生 test runner） |

### 5.3 配置 & 部署文件

| 文件 | 作用 |
|------|------|
| `vercel.json` | Vercel 构建/部署配置（cd h5 → install → build） |
| `.github/workflows/ci.yml` | GitHub Actions CI：H5 构建 + TSC 类型检查 + Python 语法检查 |
| `h5/package.json` | 新增 `test` / `test:watch` 脚本 + 依赖 `@types/node` |
| `h5/tailwind.config.js` | 自定义 neolix 品牌色板（-50 到 -700）|
| `h5/postcss.config.js` | PostCSS + TailCSS + Autoprefixer |
| `h5/vite.config.ts` | Vite dev server 配置（host 暴露 + 端口） |
| `h5/tsconfig.json` | TypeScript 编译配置（React strict 模式）|
| `h5/tsconfig.node.json` | 补充 vite.config + api/*.ts 的类型范围 + node types |
| `h5/index.html` | viewport fit=cover 移动端适配 + favicon.svg |
| `h5/public/favicon.svg` | 新石器品牌 favicon（无图片 404 问题） |
| `h5/.env.example` | 前端环境变量模板（USE_REAL_API / FEISHU_API_BASE） |
| `.gitignore` | 补充 Node、Python、Vite、IDE、AI缓存的忽略规则 |

### 5.4 文档

| 文件 | 作用 |
|------|------|
| `h5/README.md` | H5 完整文档（架构图、功能清单、环境变量、字段映射、错误码、部署）|
| `h5/DEMO_GUIDE.md` | 演示操作手册（手机访问、4个演示场景、调试面板使用）|
| `LOCAL_TEST_GUIDE.md` | 本地模拟生产环境全流程测试（Vercel CLI + 真实飞书 API 联调）|
| 本文件 `H5_FEATURE_SPEC.md` | Code Review 专用功能说明（就是你在看的这一份）|

---

## 6. 验证方式（供 reviewer 核对）

### 6.1 跑单元测试

```bash
cd h5
npm test
```

预期输出：`ℹ tests 17 | pass 17 | fail 0`（Node ≥ 22 需要 `--experimental-strip-types`，已写进 package.json 的脚本里）

覆盖的 17 项用例分类：
- 正常提交流程：3 项（完整成功/仅必填字段/contact_allowed=false）
- 环境变量校验：1 项（缺 BITABLE_APP_TOKEN → 500）
- 必填字段校验：3 项（缺 vehicle_id / 缺 content_raw / body=null）
- 飞书 API 错误：3 项（鉴权 code !=0 / 鉴权 HTTP 500 / 写入 code !=0）
- 超时处理：2 项（鉴权 AbortError → 504 / 写入 AbortError → 504）
- HTTP 方法：2 项（OPTIONS 204 / GET 405）
- 请求体大小：1 项（10KB+ → 413）
- 响应格式：2 项（成功响应字段全 / 错误响应有 error 字段）

### 6.2 前端本地跑 Demo

```bash
cd h5
npm install
npm run dev
```

打开 `http://localhost:3000/?vid=NX-TEST-001&city=北京&loc=望京`
（Mock 模式，无需要配置任何密钥）

可演示的场景：
1. 正常提交流程 → 看工单成功页
2. 调试点 🐛 切「断网」模式 → 提交失败 → 连续重试 3 次 → 看红色客服卡片
3. 切「成功」模式 → 再点重试 → 成功跳转，失败计数清零
4. 打开控制台 → `__setMockMode('timeout')` → 看超时提示

### 6.3 生产联调（对接真实飞书）

详见 [LOCAL_TEST_GUIDE.md](../LOCAL_TEST_GUIDE.md)，6 步：
1. 配 `h5/.env.local`：`VITE_USE_REAL_API=true`
2. `npm i -g vercel`
3. `vercel link` 关联项目
4. 在 Vercel Dashboard 配置 4 个密钥：FEISHU_APP_ID / FEISHU_APP_SECRET / BITABLE_APP_TOKEN / BITABLE_TABLE_ID
5. `vercel env pull .env.local`
6. `vercel dev` → 打开 http://localhost:3000 → 提交后检查飞书多维表格是否有新记录

### 6.4 CI 状态检查

PR 页有 GitHub Actions 绿标：
- `h5-build`：npm ci + tsc --noEmit + npm run build（类型检查+构建通过）
- `python-check`：find *.py | xargs python -m py_compile（Python 语法 OK）

---

## 7. 已知限制 & 后续可优化点

| # | 内容 | 说明 |
|---|------|------|
| 1 | CORS 目前允许 * | 生产环境如果只允许特定域名，可在 submit.ts 的 json() 辅助函数里把 Access-Control-Allow-Origin 改为具体域名 |
| 2 | token 每次请求都重新获取 | 飞书 tenant_access_token 有效期 2 小时，后续可用 lru 缓存减少重复鉴权（目前量级小可忽略）|
| 3 | Serverless Function 里 AI 分类还没做 | 目前 SF 端返回 `category: "待AI识别" / priority: "待AI判定"`，真实 AI 分类后续走周报脚本统一批处理或新增 AI Function |
| 4 | 调试面板在生产环境 | 目前 DebugPanel 组件默认挂在 App.tsx 底部，如果要纯生产模式可以注释掉那一行 |

---

## 8. Commit 列表（本 PR）

```
4f7d55a docs: 完善h5前后端架构说明+环境变量总表+字段映射+错误码文档
84e78b8 feat(h5): 完善错误处理+超时控制+17项单元测试+本地测试指南
3d31caf feat(h5): 接入Vercel Serverless Function对接飞书API
b47a455 ci: 添加GitHub Actions CI流水线 + 补充清理缓存目录
a90b688 fix(h5): 添加favicon图标，修复404问题
ce5c1bb chore: 完善.gitignore
78b632f chore: 项目清理 - 移除AI缓存/临时文件
56f7eee feat(h5): 实现一车一码AI反馈H5前端页面
```