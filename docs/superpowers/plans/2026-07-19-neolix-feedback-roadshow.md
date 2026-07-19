# 新石器无人车反馈闭环路演 PPT Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 生成一份 16:9、10 页主讲 + 4 页备份、可编辑且具有连续分镜动态感的新石器无人车反馈闭环路演 PPTX，并将其封装为个人演示模板。

**Architecture:** 使用 `@oai/artifact-tool` 的 JavaScript ES module 从零创建演示文稿；真实飞书截图以原始 PNG 嵌入，标题、流程、焦点框、图表和说明保持 PowerPoint 可编辑。动态感通过连续分镜、焦点切换和 OOXML 淡入/推进转场实现，最终经过逐页 PNG 渲染、布局检测和人工视觉检查。

**Tech Stack:** Bundled Node.js、`@oai/artifact-tool`、PowerShell `System.IO.Compression`、Microsoft Word COM、Poppler、Presentations 容器工具、Template Creator。

## Global Constraints

- 最终文件：`E:/cursor project/feishu/feishu-neolix-AIfeedback/outputs/新石器无人车_飞书AI用户反馈闭环路演.pptx`。
- 临时工作区：`C:/Users/asus/AppData/Local/Temp/codex-presentations/019f795b-042b-7d22-841b-fad36ff0bcb0/neolix-feedback-deck/tmp`。
- 画布固定为 1280 × 720；背景 `#0A1118`，主文字 `#EDF3F6`，蓝色 `#73A7FF`，绿色 `#72D6A0`，橙色 `#FF9B54`。
- 主标题不小于 35 pt，正文不小于 18 pt；标题框不得换行。
- 只使用 PRD、路演稿和真实截图支持的事实，不虚构上线效果、客户数据或性能指标。
- 输入 Word 和仓库既有文件保持不变；不修改工单 Schema。
- 页面以全幅画面或左右主次构图为主，不做卡片墙，不使用夸张霓虹、渐变球和长段文字。

---

### Task 1: 建立素材清单与工作区

**Files:**
- Create: `C:/Users/asus/AppData/Local/Temp/codex-presentations/019f795b-042b-7d22-841b-fad36ff0bcb0/neolix-feedback-deck/tmp/source-notes.txt`
- Create: `C:/Users/asus/AppData/Local/Temp/codex-presentations/019f795b-042b-7d22-841b-fad36ff0bcb0/neolix-feedback-deck/tmp/assets/`

**Interfaces:**
- Consumes: `D:/WeChat/software/xwechat_files/wxid_b929hwkdqtyd22_27d9/msg/file/2026-07/截图.docx` 与仓库 `docs/` 内 PRD、路演稿、演示脚本。
- Produces: 原始截图 `image1.png` 至 `image22.png`、统一素材绝对路径表、来源说明。

- [ ] **Step 1: 初始化 artifact-tool 工作区**

```powershell
& 'C:/Users/asus/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe' `
  'C:/Users/asus/.codex/plugins/cache/openai-primary-runtime/presentations/26.715.12143/skills/presentations/container_tools/setup_artifact_tool_workspace.mjs' `
  --workspace 'C:/Users/asus/AppData/Local/Temp/codex-presentations/019f795b-042b-7d22-841b-fad36ff0bcb0/neolix-feedback-deck/tmp'
```

Expected: 工作区存在 `package.json` 和可解析的 `@oai/artifact-tool`。

- [ ] **Step 2: 提取 DOCX 原始媒体**

使用 `System.IO.Compression.ZipFile` 读取 `word/media/*`，复制到 `tmp/assets/feishu/`，并核对共 22 张 PNG。

```powershell
(Get-ChildItem 'C:/Users/asus/AppData/Local/Temp/codex-presentations/019f795b-042b-7d22-841b-fad36ff0bcb0/neolix-feedback-deck/tmp/assets/feishu' -File -Filter '*.png').Count
```

Expected: `22`。

- [ ] **Step 3: 写入来源清单**

`source-notes.txt` 必须记录：PRD、路演稿、演示脚本、截图 Word、保留截图编号、舍弃截图编号，以及后续网络图片的页面 URL 和使用页码。

- [ ] **Step 4: 验证主讲素材**

```powershell
$assetRoot = 'C:/Users/asus/AppData/Local/Temp/codex-presentations/019f795b-042b-7d22-841b-fad36ff0bcb0/neolix-feedback-deck/tmp/assets/feishu'
Get-Item (Join-Path $assetRoot 'image4.png'),(Join-Path $assetRoot 'image5.png'),(Join-Path $assetRoot 'image6.png'),(Join-Path $assetRoot 'image7.png'),(Join-Path $assetRoot 'image8.png'),(Join-Path $assetRoot 'image9.png'),(Join-Path $assetRoot 'image10.png'),(Join-Path $assetRoot 'image12.png'),(Join-Path $assetRoot 'image13.png'),(Join-Path $assetRoot 'image22.png')
```

Expected: 十个文件全部存在且长度大于 10 KB。

### Task 2: 编写 14 页可编辑演示文稿

**Files:**
- Create: `C:/Users/asus/AppData/Local/Temp/codex-presentations/019f795b-042b-7d22-841b-fad36ff0bcb0/neolix-feedback-deck/tmp/build-deck.mjs`
- Create: `C:/Users/asus/AppData/Local/Temp/codex-presentations/019f795b-042b-7d22-841b-fad36ff0bcb0/neolix-feedback-deck/tmp/preview/`
- Create: `E:/cursor project/feishu/feishu-neolix-AIfeedback/outputs/新石器无人车_飞书AI用户反馈闭环路演.pptx`

**Interfaces:**
- Consumes: Task 1 的素材绝对路径与 `source-notes.txt`。
- Produces: `buildDeck(): Promise<Presentation>`，14 页演示文稿、逐页预览、布局 JSON、蒙太奇和 PPTX。

- [ ] **Step 1: 先写结构断言并验证失败**

在 `build-deck.mjs` 底部加入以下检查，再运行尚未完整实现的模块：

```js
if (presentation.slides.items.length !== 14) {
  throw new Error(`期望 14 页，实际 ${presentation.slides.items.length} 页`);
}
```

Run:

```powershell
& 'C:/Users/asus/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe' 'C:/Users/asus/AppData/Local/Temp/codex-presentations/019f795b-042b-7d22-841b-fad36ff0bcb0/neolix-feedback-deck/tmp/build-deck.mjs'
```

Expected: FAIL，提示页数不是 14 或缺少构建函数。

- [ ] **Step 2: 实现主题与基础组件**

模块必须定义并复用以下接口：

```js
const W = 1280;
const H = 720;
const C = { bg: '#0A1118', panel: '#0F1D29', text: '#EDF3F6', muted: '#94A6B2', blue: '#73A7FF', green: '#72D6A0', orange: '#FF9B54', line: '#29404F' };
function addTitle(slide, title, eyebrow, pageNo) {}
function addText(slide, text, position, style = {}) {}
function addSignalLine(slide, points, color = C.blue) {}
async function addImage(slide, path, position, options = {}) {}
function addFocusFrame(slide, position, label, color = C.blue) {}
function addFooter(slide, pageNo, section) {}
```

所有对象设置稳定 `name`，便于 inspect 与布局检查。

- [ ] **Step 3: 实现 10 页主讲**

必须按设计稿逐页实现：封面、六入口、完整闭环、统一工单底座、AI 分派、P0 处理链路、自动闭环、仪表盘预留页、问题回流产品、结尾收束。第 8 页在缺少仪表盘截图时使用明确的“待替换截图位”，不伪造真实仪表盘数据。

每页加入演讲者备注，备注仅包含该页 20–35 秒口播提示，不显示在画面上。

- [ ] **Step 4: 实现 4 页答辩备份**

必须实现：系统边界、双 AI 分工、自动化证据、复用与落地。备份页使用较高信息密度，但正文仍不小于 18 pt。

- [ ] **Step 5: 导出可编辑 PPTX 与预览**

```js
for (const [index, slide] of presentation.slides.items.entries()) {
  const stem = `slide-${String(index + 1).padStart(2, '0')}`;
  await writeBlob(`${PREVIEW_DIR}/${stem}.png`, await presentation.export({ slide, format: 'png', scale: 2 }));
  await fs.writeFile(`${LAYOUT_DIR}/${stem}.layout.json`, await (await slide.export({ format: 'layout' })).text());
}
await writeBlob(`${QA_DIR}/deck-montage.webp`, await presentation.export({ format: 'webp', montage: true, scale: 1 }));
const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(FINAL_PPTX);
```

Expected: 14 张 PNG、14 个布局 JSON、1 张蒙太奇和 1 个 PPTX。

### Task 3: 增加页面转场与连续分镜

**Files:**
- Create: `C:/Users/asus/AppData/Local/Temp/codex-presentations/019f795b-042b-7d22-841b-fad36ff0bcb0/neolix-feedback-deck/tmp/add-transitions.ps1`
- Modify: `E:/cursor project/feishu/feishu-neolix-AIfeedback/outputs/新石器无人车_飞书AI用户反馈闭环路演.pptx`

**Interfaces:**
- Consumes: Task 2 导出的 PPTX。
- Produces: 保持对象可编辑、包含轻量转场的 PPTX。

- [ ] **Step 1: 写入转场补丁脚本**

脚本将 PPTX 复制为临时 ZIP，逐个修改 `ppt/slides/slideN.xml`：主讲页使用 `p:fade`，第 2→3、5→6、8→9 页使用 `p:push dir="l"`，备份页使用 `p:fade`。转场节点必须插入在 `p:clrMapOvr` 之后、`p:timing` 之前；若已有 `p:transition`，先替换而不是重复插入。

- [ ] **Step 2: 执行补丁并验证结构**

```powershell
& 'C:/Users/asus/AppData/Local/Temp/codex-presentations/019f795b-042b-7d22-841b-fad36ff0bcb0/neolix-feedback-deck/tmp/add-transitions.ps1' -PptxPath 'E:/cursor project/feishu/feishu-neolix-AIfeedback/outputs/新石器无人车_飞书AI用户反馈闭环路演.pptx'
```

Expected: 14 个 slide XML 各包含且仅包含一个 `p:transition`。

- [ ] **Step 3: 用 PowerPoint 打开并重新保存测试副本**

使用 Word/PowerPoint COM 只读打开原文件并另存测试副本，确认文件未损坏；测试副本保存在 `tmp/qa/roundtrip.pptx`，不覆盖最终文件。

### Task 4: 全稿渲染与质量验证

**Files:**
- Create: `C:/Users/asus/AppData/Local/Temp/codex-presentations/019f795b-042b-7d22-841b-fad36ff0bcb0/neolix-feedback-deck/tmp/qa/final-render/`
- Create: `C:/Users/asus/AppData/Local/Temp/codex-presentations/019f795b-042b-7d22-841b-fad36ff0bcb0/neolix-feedback-deck/tmp/qa/qa-ledger.txt`
- Modify: `C:/Users/asus/AppData/Local/Temp/codex-presentations/019f795b-042b-7d22-841b-fad36ff0bcb0/neolix-feedback-deck/tmp/build-deck.mjs`（仅修复发现的问题）

**Interfaces:**
- Consumes: Task 3 的最终 PPTX。
- Produces: 逐页 PNG、蒙太奇、布局检查结果和人工 QA 记录。

- [ ] **Step 1: 运行越界检测**

```powershell
& 'C:/Users/asus/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' `
  'C:/Users/asus/.codex/plugins/cache/openai-primary-runtime/presentations/26.715.12143/skills/presentations/container_tools/slides_test.py' `
  'E:/cursor project/feishu/feishu-neolix-AIfeedback/outputs/新石器无人车_飞书AI用户反馈闭环路演.pptx'
```

Expected: 无越界对象。

- [ ] **Step 2: 渲染全部页面**

```powershell
& 'C:/Users/asus/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' `
  'C:/Users/asus/.codex/plugins/cache/openai-primary-runtime/presentations/26.715.12143/skills/presentations/container_tools/render_slides.py' `
  'E:/cursor project/feishu/feishu-neolix-AIfeedback/outputs/新石器无人车_飞书AI用户反馈闭环路演.pptx'
```

Expected: 共 14 张渲染图。

- [ ] **Step 3: 逐页视觉检查**

逐页检查标题换行、文字遮挡、截图裁切、中文字体、焦点框位置、颜色对比和页面节奏，并将每页结论写入 `qa-ledger.txt`。发现问题后回到 Task 2 修复、重新导出、重新添加转场并再渲染。

- [ ] **Step 4: 完成内容核验**

检查主讲页只使用有来源的事实；检查第 8 页和第 9 页缺图位置明确可替换；检查 10 页主讲 + 4 页备份顺序正确。

### Task 5: 创建个人演示模板并交付

**Files:**
- Create: `C:/Users/asus/.codex/skills/artifact-template-neolix-feedback-roadshow*/`
- Read-only: `E:/cursor project/feishu/feishu-neolix-AIfeedback/outputs/新石器无人车_飞书AI用户反馈闭环路演.pptx`

**Interfaces:**
- Consumes: 已通过 Task 4 的最终 PPTX 与第一页预览 PNG。
- Produces: 个人 `presentation` 模板技能和最终 PPTX。

- [ ] **Step 1: 生成并检查模板预览**

使用最终 PPTX 的第一页渲染图作为 `preview.png`；确认其非空、未裁切、能代表深色无人车运营台视觉。

- [ ] **Step 2: 创建模板技能**

```powershell
& 'C:/Users/asus/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe' `
  'C:/Users/asus/.codex/plugins/cache/openai-primary-runtime/template-creator/26.715.12143/skills/template-creator/scripts/create-template-skill.mjs' `
  --reference-path 'E:/cursor project/feishu/feishu-neolix-AIfeedback/outputs/新石器无人车_飞书AI用户反馈闭环路演.pptx' `
  --preview-path 'C:/Users/asus/AppData/Local/Temp/codex-presentations/019f795b-042b-7d22-841b-fad36ff0bcb0/neolix-feedback-deck/tmp/preview/slide-01.png' `
  --display-name '新石器反馈闭环路演' `
  --description '用于无人配送、飞书 AI 和运营闭环主题的科技感比赛路演演示。'
```

Expected: JSON 返回新模板的 `skillName`、`skillPath`、`displayName` 和 `artifactKind=presentation`。

- [ ] **Step 3: 验证模板包**

检查模板目录包含 `SKILL.md`、`artifact-template.json`、`agents/openai.yaml`、`assets/reference.pptx` 和 `assets/preview.png`，且不存在 staging/backup 目录。

- [ ] **Step 4: 最终交付检查**

确认最终 PPTX 文件存在、大小大于 500 KB、可被 PowerPoint 打开、14 页齐全；最终回复只链接 PPTX，并按 Template Creator 要求展示模板卡片。
