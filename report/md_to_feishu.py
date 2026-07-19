# -*- coding: utf-8 -*-
"""
Markdown 转飞书文档 Block 结构转换器

支持的 Markdown 语法：
- # 标题（H1-H6）
- 普通段落
- **粗体**、*斜体*
- 无序列表（- 或 *）
- 有序列表（1. 2. 3.）
- 表格（| 列1 | 列2 |）
- 分隔线（---）
- 引用（> 开头）

用法：
    blocks = markdown_to_feishu_blocks(markdown_text)
    # 然后调用飞书 API 批量写入
"""

import re
from typing import List, Dict, Any


def markdown_to_feishu_blocks(md_text: str) -> List[Dict[str, Any]]:
    """将 Markdown 文本转换为飞书文档 block 列表"""
    lines = md_text.split('\n')
    blocks = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # 空行跳过
        if not line.strip():
            i += 1
            continue

        # --- 分隔线
        if re.match(r'^-{3,}$', line.strip()):
            blocks.append(_divider_block())
            i += 1
            continue

        # # 标题
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2).strip()
            blocks.append(_heading_block(text, level))
            i += 1
            continue

        # > 引用
        if line.startswith('> '):
            quote_lines = []
            while i < len(lines) and lines[i].startswith('> '):
                quote_lines.append(lines[i][2:].strip())
                i += 1
            blocks.append(_quote_block('\n'.join(quote_lines)))
            continue

        # 表格（检测表头行 | --- | --- |）
        if '|' in line and i + 1 < len(lines) and re.match(r'^[\s|:-]+$', lines[i + 1]):
            table_lines = [line]
            i += 2  # 跳过表头和分隔线
            while i < len(lines) and '|' in lines[i] and lines[i].strip():
                table_lines.append(lines[i])
                i += 1
            blocks.append(_table_block(table_lines))
            continue

        # 无序列表
        if re.match(r'^[\s]*[-*+]\s+', line):
            list_items = []
            while i < len(lines) and re.match(r'^[\s]*[-*+]\s+', lines[i]):
                item_text = re.sub(r'^[\s]*[-*+]\s+', '', lines[i]).strip()
                list_items.append(item_text)
                i += 1
            blocks.extend(_bullet_list_block(list_items))
            continue

        # 有序列表
        if re.match(r'^[\s]*\d+\.\s+', line):
            list_items = []
            while i < len(lines) and re.match(r'^[\s]*\d+\.\s+', lines[i]):
                item_text = re.sub(r'^[\s]*\d+\.\s+', '', lines[i]).strip()
                list_items.append(item_text)
                i += 1
            blocks.extend(_ordered_list_block(list_items))
            continue

        # 普通段落（合并连续的非空行）
        para_lines = []
        while i < len(lines) and lines[i].strip() and not _is_block_start(lines[i]):
            para_lines.append(lines[i].strip())
            i += 1
        if para_lines:
            blocks.append(_text_block(' '.join(para_lines)))
            continue

        # 其他情况，当成文本处理
        blocks.append(_text_block(line.strip()))
        i += 1

    return blocks


def _is_block_start(line: str) -> bool:
    """判断一行是否是某个 block 的开头"""
    if not line.strip():
        return True
    if re.match(r'^#{1,6}\s+', line):
        return True
    if re.match(r'^[\s]*[-*+]\s+', line):
        return True
    if re.match(r'^[\s]*\d+\.\s+', line):
        return True
    if line.startswith('> '):
        return True
    if re.match(r'^-{3,}$', line.strip()):
        return True
    if '|' in line:
        return True
    return False


def _make_text_elements(text: str) -> List[Dict[str, Any]]:
    """解析内联格式（粗体、斜体），返回 elements 列表"""
    elements = []

    # 统一的正则：先匹配粗体 **text**，再匹配斜体 *text*
    # 用一个组合正则，确保粗体优先匹配
    pattern = re.compile(r'(\*\*(.+?)\*\*|\*(.+?)\*)')

    pos = 0
    for match in pattern.finditer(text):
        # 普通文本
        if match.start() > pos:
            elements.append({
                "text_run": {
                    "content": text[pos:match.start()],
                    "text_element_style": {},
                }
            })

        if match.group(2):  # 粗体 **text**
            content = match.group(2)
            elements.append({
                "text_run": {
                    "content": content,
                    "text_element_style": {
                        "bold": True,
                    },
                }
            })
        elif match.group(3):  # 斜体 *text*
            content = match.group(3)
            elements.append({
                "text_run": {
                    "content": content,
                    "text_element_style": {
                        "italic": True,
                    },
                }
            })

        pos = match.end()

    # 剩余的普通文本
    if pos < len(text):
        elements.append({
            "text_run": {
                "content": text[pos:],
                "text_element_style": {},
            }
        })

    if not elements:
        elements = [{
            "text_run": {
                "content": text,
                "text_element_style": {},
            }
        }]

    return elements


def _heading_block(text: str, level: int) -> Dict[str, Any]:
    """标题 block"""
    # 飞书标题 block_type: 3=H1, 4=H2, 5=H3, ..., 8=H6
    block_type = 2 + level  # H1 -> 3, H2 -> 4, ...
    heading_key = f"heading{level}"
    return {
        "block_type": block_type,
        heading_key: {
            "elements": _make_text_elements(text),
            "style": {},
        },
    }


def _text_block(text: str) -> Dict[str, Any]:
    """普通文本 block (block_type 2)"""
    return {
        "block_type": 2,
        "text": {
            "elements": _make_text_elements(text),
            "style": {},
        },
    }


def _divider_block() -> Dict[str, Any]:
    """分隔线 block (block_type 22)"""
    return {
        "block_type": 22,
        "divider": {
            "style": {},
        },
    }


def _quote_block(text: str) -> Dict[str, Any]:
    """引用 block (block_type 15 = Quote)"""
    # text_run.content 不支持 \n，替换为空格
    text = text.replace('\n', ' ')
    return {
        "block_type": 15,
        "quote": {
            "elements": _make_text_elements(text),
        },
    }


def _bullet_list_block(items: List[str]) -> List[Dict[str, Any]]:
    """无序列表 — 返回一组 block，每个列表项是一个 bullet block (block_type 12)"""
    blocks = []
    for item in items:
        blocks.append({
            "block_type": 12,
            "bullet": {
                "elements": _make_text_elements(item),
                "style": {},
            },
        })
    return blocks


def _ordered_list_block(items: List[str]) -> List[Dict[str, Any]]:
    """有序列表 — 返回一组 block，每个列表项是一个 ordered block (block_type 13)"""
    blocks = []
    for item in items:
        blocks.append({
            "block_type": 13,
            "ordered": {
                "elements": _make_text_elements(item),
                "style": {},
            },
        })
    return blocks


def _table_block(table_lines: List[str]) -> Dict[str, Any]:
    """表格 — 转换为格式化文本，避免飞书表格 API 复杂结构"""
    rows = []
    for line in table_lines:
        line = line.strip()
        if line.startswith('|'):
            line = line[1:]
        if line.endswith('|'):
            line = line[:-1]
        cells = [c.strip() for c in line.split('|')]
        if all(re.match(r'^[:-]+$', c) for c in cells):
            continue
        rows.append(cells)

    if not rows:
        return _text_block("(表格解析失败)")

    # 计算每列宽度
    num_cols = max(len(r) for r in rows)
    col_widths = [0] * num_cols
    for row in rows:
        for ci, cell in enumerate(row):
            if ci < num_cols:
                # 中文字符按 2 宽度计算
                w = sum(2 if ord(c) > 127 else 1 for c in cell)
                col_widths[ci] = max(col_widths[ci], w)

    # 构建文本行
    text_lines = []
    for ri, row in enumerate(rows):
        parts = []
        for ci in range(num_cols):
            cell = row[ci] if ci < len(row) else ""
            w = sum(2 if ord(c) > 127 else 1 for c in cell)
            parts.append(cell + " " * (col_widths[ci] - w))
        text_lines.append(" | ".join(parts))
        if ri == 0:
            text_lines.append("-" * (sum(col_widths) + 3 * (num_cols - 1)))

    return _text_block("\n".join(text_lines))


# ============================================================
# 测试
# ============================================================

if __name__ == "__main__":
    test_md = """# 标题一

这是一段普通文本，里面有**粗体**和*斜体*。

## 标题二

- 无序列表项一
- 无序列表项二
- 无序列表项三

1. 有序列表项一
2. 有序列表项二
3. 有序列表项三

---

| 列1 | 列2 | 列3 |
|-----|-----|-----|
|  A  |  B  |  C  |
|  1  |  2  |  3  |

> 这是一段引用文字。

普通段落。
"""

    blocks = markdown_to_feishu_blocks(test_md)
    print(f"生成了 {len(blocks)} 个 blocks")
    import json
    print(json.dumps(blocks[0], indent=2, ensure_ascii=False))
    print("...")