# 新石器无人车用户反馈H5

React + TypeScript + Vite + TailwindCSS + Framer Motion

## 快速开始

```bash
cd h5
npm install
npm run dev
```

访问 http://localhost:3000

## 一车一码使用方式

通过URL参数预填车辆信息：

```
https://your-domain.com/?vid=NEOLIX001&model=新石器X3&city=北京&loc=望京SOHO
```

| 参数 | 说明 | 必填 |
|------|------|------|
| `vid` | 车辆ID/编号 | 是 |
| `model` | 车型名称 | 否 |
| `city` | 所在城市 | 否 |
| `loc` | 具体位置 | 否 |

## 功能模块

- **首页**：车辆信息展示、功能介绍、开始反馈入口
- **反馈表单**：问题描述（含快速选择标签）、问题类型选择、联系方式选填
- **AI分析中**：动画展示AI分析过程（提交→分析→分类→生成工单→通知负责人）
- **结果页**：工单号、AI识别的分类/优先级、预计响应时间、状态追踪
- **错误页**：网络异常时的重试引导

## 对接飞书API

在 `.env` 文件中配置：

```
VITE_FEISHU_API_BASE=你的后端API地址
VITE_BITABLE_APP_TOKEN=多维表格AppToken
VITE_BITABLE_TABLE_ID=数据表TableID
```

不配置时使用本地模拟AI分析，方便Demo演示。

## 构建部署

```bash
npm run build
```

构建产物在 `dist/` 目录，可部署到 Vercel/Netlify/阿里云OSS 等静态托管。
