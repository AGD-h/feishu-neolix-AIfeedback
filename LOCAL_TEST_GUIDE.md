# 本地模拟生产环境全流程测试指南

## 架构说明

```
H5 前端 (localhost:3000) ──POST /api/submit──▶ Vercel Serverless Function
                                                  │
                                                  ├── 获取飞书 tenant_access_token
                                                  ├── 构建多维表格字段
                                                  └── 写入工单记录 → 飞书多维表格
```

## 前置条件

1. 飞书自建应用已创建，并已开通以下权限：
   - `bitable:app`（多维表格读写）
   - 应用已被添加为多维表格的**协作者**

2. 已安装 Node.js ≥ 18

---

## 步骤一：创建本地环境变量文件

在 `h5/` 目录下创建 `.env.local`：

```bash
# 在 h5/ 目录下
cp .env.example .env.local
```

然后编辑 `.env.local`，填入真实值：

```env
# 开启真实 API 模式（不再使用 Mock）
VITE_USE_REAL_API=true

# Vercel 部署时留空（同域调用），本地测试也留空
VITE_FEISHU_API_BASE=
```

---

## 步骤二：安装 Vercel CLI

```bash
npm install -g vercel
```

验证安装：

```bash
vercel --version
```

---

## 步骤三：关联 Vercel 项目

在项目根目录（`feishu-neolix-AIfeedback/`）执行：

```bash
vercel link
```

按提示选择或创建 Vercel 项目。

---

## 步骤四：配置 Vercel 环境变量

在 Vercel Dashboard 或通过 CLI 配置以下环境变量：

```bash
vercel env add FEISHU_APP_ID
# 输入：你的飞书 App ID

vercel env add FEISHU_APP_SECRET
# 输入：你的飞书 App Secret

vercel env add BITABLE_APP_TOKEN
# 输入：多维表格的 app_token（URL 中 /base/ 后面的字符串）

vercel env add BITABLE_TABLE_ID
# 输入：工单表的 table_id（URL 中 table= 参数的值）
```

**本地开发时**，还需要拉取环境变量到本地：

```bash
vercel env pull .env.local
```

这会自动将 Vercel 上配置的环境变量写入 `.env.local`。

---

## 步骤五：启动本地开发环境

```bash
# 在项目根目录（feishu-neolix-AIfeedback/）
vercel dev
```

Vercel Dev 会同时启动：
- H5 前端（Vite dev server）
- API Serverless Function（`/api/submit`）

访问 `http://localhost:3000` 即可看到 H5 页面。

---

## 步骤六：验证全流程

### 6.1 运行单元测试

```bash
cd h5
npm test
```

应该看到 17 个测试全部通过：

```
✔ submit.ts Serverless Function
  ✔ 正常提交流程 (3 tests)
  ✔ 环境变量校验
  ✔ 必填字段校验 (3 tests)
  ✔ 飞书 API 错误处理 (3 tests)
  ✔ 超时处理 (2 tests)
  ✔ HTTP 方法校验 (2 tests)
  ✔ 请求体大小限制
  ✔ 响应格式 (2 tests)
ℹ tests 17 | pass 17 | fail 0
```

### 6.2 浏览器手动测试

1. 打开 `http://localhost:3000`
2. 填写反馈内容（≥ 5 个字）
3. 点击"提交反馈"
4. 观察页面内调试面板（右下角瓢虫按钮），确认日志显示：
   - `📡 发送请求到 /api/submit`
   - `响应状态: HTTP 200`
   - `✅ 后端返回成功`

### 6.3 验证飞书多维表格

打开飞书多维表格，确认新记录已写入，字段包括：
- `channel` = "车身扫码"
- `vehicle_id` = 你填写的车辆 ID
- `content_raw` = 你填写的反馈内容
- `status` = "待处理"

### 6.4 模拟失败场景

在 URL 后添加参数测试不同场景：

| URL | 场景 | 预期结果 |
|-----|------|---------|
| `?mock=network` | 网络错误 | 显示"网络连接失败" |
| `?mock=server` | 服务器 500 | 显示"服务器异常" |
| `?mock=timeout` | 超时 | 显示"请求超时" |

连续失败 3 次后，页面会弹出"建议联系人工客服"卡片。

---

## 常见问题

### Q: `vercel dev` 报错 "Environment variables not found"
**A:** 确保已执行 `vercel env pull .env.local`，且 Vercel Dashboard 中已配置所有环境变量。

### Q: 飞书返回 91402 错误
**A:** 多维表格未添加应用为协作者。在飞书多维表格右上角 → 添加协作者 → 搜索应用名称 → 添加。

### Q: 飞书返回 10001 错误
**A:** FEISHU_APP_ID 或 FEISHU_APP_SECRET 配置错误，检查 `.env.local`。

### Q: 前端请求一直显示 Mock 模式
**A:** 检查 `.env.local` 中 `VITE_USE_REAL_API=true` 是否生效。重启 `vercel dev`。

---

## 部署到生产环境

```bash
# 部署到 Vercel
vercel --prod
```

部署后 Vercel 会返回一个 URL（如 `https://your-project.vercel.app`），前端和 API 自动同域部署。