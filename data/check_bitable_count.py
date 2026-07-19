# -*- coding: utf-8 -*-
"""查看多维表格记录数"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app_id = os.getenv('FEISHU_APP_ID')
app_secret = os.getenv('FEISHU_APP_SECRET')
app_token = os.getenv('BITABLE_APP_TOKEN')
table_id = os.getenv('BITABLE_TABLE_ID')

response = requests.post(
    'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
    json={'app_id': app_id, 'app_secret': app_secret},
    timeout=10
)
token = response.json().get('tenant_access_token')

url = f'https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records'
response = requests.get(url, headers={'Authorization': f'Bearer {token}'}, params={'page_size': 1}, timeout=30)
result = response.json()
total = result.get('data', {}).get('total', 0)
print(f'当前记录数: {total}')
