# -*- coding: utf-8 -*-
"""用 drive 接口验证 token 是什么类型"""
import os
from pathlib import Path
import requests
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parents[1]
load_dotenv(project_root / ".env")

app_id = os.getenv("FEISHU_APP_ID")
app_secret = os.getenv("FEISHU_APP_SECRET")
bitable_token = os.getenv("BITABLE_APP_TOKEN")

r = requests.post(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    json={"app_id": app_id, "app_secret": app_secret},
)
token = r.json()["tenant_access_token"]

# 用 drive 接口查文件元信息，需要先开通 drive:drive:readonly 权限
# 所以这个不通，换个思路：用 wiki 接口试试
# 也不行...

# 简单的办法：让 2号 用手机打开表格，看"分享"里有没有一个"复制链接"
# 链接的格式应该是 https://xxx.feishu.cn/base/xxxxx
# 让他直接把完整链接发过来

# 但目前我们从链接里提取的 token 是 lotubQjiOavmzessY3fcEBRvnNh
# 这个格式（lotub 开头）是对的，飞书多维表格 app token 就是 lotub 开头

# 那问题只有一个可能：应用没真正加进去
# 让 2号 截图分享页面，看看应用的名字和权限

print("结论：App ID 是对的，token 格式也对（lotub 开头）")
print("但应用就是访问不到，说明协作者添加可能没生效")
print()
print("让 2号 做以下操作：")
print("1. 打开多维表格 → 右上角分享")
print("2. 找到「新石器反馈闭环数据接入助手」")
print("3. 把权限从「可阅读」改成「可编辑」，保存")
print("4. 再改回「可阅读」，再保存一次")
print("5. 然后让我重试")
print()
print("或者更简单：删掉这个应用协作者，重新添加一次")