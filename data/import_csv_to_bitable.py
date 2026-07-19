# -*- coding: utf-8 -*-
"""
CSV 数据导入飞书多维表格（1号数据线辅助工具）

功能：
  1. 读取本地 CSV 文件（data/output/mock_feedback.csv）
  2. 将日期字段转换为飞书多维表格格式（毫秒时间戳）
  3. 批量上传到飞书多维表格

运行方式：
  python data/import_csv_to_bitable.py

依赖：需要在 .env 中配置飞书凭证
"""

import csv
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

# 常量配置
BATCH_SIZE = 50  # 每次批量创建的记录数
MAX_RETRIES = 3  # 重试次数
RETRY_DELAY = 5  # 重试间隔（秒）
TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
BITABLE_BATCH_CREATE_URL = "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"
BITABLE_RECORDS_URL = "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
CSV_PATH = os.path.join(os.path.dirname(__file__), "output", "mock_feedback.csv")


def load_env() -> Optional[Dict[str, str]]:
    """读取 .env 配置"""
    load_dotenv()
    env_names = ["FEISHU_APP_ID", "FEISHU_APP_SECRET", "BITABLE_APP_TOKEN", "BITABLE_TABLE_ID"]
    values = {name: os.getenv(name) for name in env_names}
    missing_vars = [name for name, value in values.items() if not value]
    
    if missing_vars:
        print("❌ 配置检查失败")
        print("原因：本地 .env 缺少以下变量：")
        for var_name in missing_vars:
            print(f"  - {var_name}")
        return None
    
    return values


def get_tenant_access_token(app_id: str, app_secret: str) -> Optional[str]:
    """获取飞书 tenant_access_token"""
    try:
        response = requests.post(
            TOKEN_URL,
            json={"app_id": app_id, "app_secret": app_secret},
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"❌ 获取 tenant_access_token 失败：{exc}")
        return None
    
    result = response.json()
    if result.get("code") != 0:
        print(f"❌ 飞书返回错误：code={result.get('code')}, msg={result.get('msg')}")
        return None
    
    return result.get("tenant_access_token")


def format_datetime(dt_str: str) -> Optional[int]:
    """将日期字符串转换为飞书多维表格格式（毫秒时间戳）"""
    if not dt_str:
        return None
    
    formats = ["%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(dt_str, fmt)
            return int(dt.timestamp() * 1000)
        except ValueError:
            continue
    
    print(f"⚠️ 日期格式解析失败：{dt_str}")
    return None


def read_csv(file_path: str) -> List[Dict[str, Any]]:
    """读取 CSV 文件"""
    records = []
    
    with open(file_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    
    print(f"✅ 从 CSV 读取到 {len(records)} 条记录")
    return records


def convert_to_bitable_format(csv_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """将 CSV 记录转换为飞书多维表格格式"""
    bitable_records = []
    
    for row in csv_records:
        fields = {
            "feedback_id": row.get("feedback_id", ""),
            "channel": row.get("channel", ""),
            "user_tier": row.get("user_tier", ""),
            "category": row.get("category", ""),
            "priority": row.get("priority", ""),
            "status": row.get("status", ""),
            "vehicle_id": row.get("vehicle_id", ""),
            "city": row.get("city", ""),
            "content_raw": row.get("content_raw", ""),
            "content_summary": row.get("content_summary", ""),
        }
        
        # 日期字段
        created_at = format_datetime(row.get("created_at", ""))
        if created_at:
            fields["created_at"] = created_at
        
        closed_at = format_datetime(row.get("closed_at", ""))
        if closed_at:
            fields["closed_at"] = closed_at
        
        # 人员字段（飞书多维表格人员字段需要用户ID，这里跳过，留空）
        # assigned_to 字段由飞书自动化流程在创建记录后自动填充
        
        # 数字字段
        csat_score = row.get("csat_score", "")
        if csat_score:
            try:
                fields["csat_score"] = int(csat_score)
            except ValueError:
                pass
        
        bitable_records.append({"fields": fields})
    
    return bitable_records


def delete_all_records(app_token: str, table_id: str, tenant_access_token: str) -> bool:
    """删除多维表格中所有记录"""
    url = BITABLE_RECORDS_URL.format(app_token=app_token, table_id=table_id)
    headers = {"Authorization": f"Bearer {tenant_access_token}"}
    
    print("🗑️ 正在获取所有记录ID...")
    
    # 获取所有记录ID
    record_ids = []
    page_token = ""
    
    while True:
        params = {"page_size": 500}
        if page_token:
            params["page_token"] = page_token
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"❌ 获取记录列表失败：{exc}")
            return False
        
        result = response.json()
        if result.get("code") != 0:
            print(f"❌ 飞书返回错误：code={result.get('code')}, msg={result.get('msg')}")
            return False
        
        data = result.get("data", {})
        records = data.get("items", [])
        
        for record in records:
            record_ids.append(record.get("record_id"))
        
        page_token = data.get("page_token")
        if not page_token:
            break
    
    if not record_ids:
        print("   ✅ 表格为空，无需删除")
        return True
    
    print(f"   找到 {len(record_ids)} 条记录，正在删除...")
    
    # 批量删除（每次删除50条）
    delete_url = url + "/batch_delete"
    success_count = 0
    
    for i in range(0, len(record_ids), 50):
        batch_ids = record_ids[i:i + 50]
        
        try:
            response = requests.post(
                delete_url,
                json={"record_ids": batch_ids},
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"❌ 删除失败：{exc}")
            return False
        
        result = response.json()
        if result.get("code") != 0:
            print(f"❌ 飞书返回错误：code={result.get('code')}, msg={result.get('msg')}")
            return False
        
        success_count += len(batch_ids)
    
    print(f"   ✅ 删除成功，共删除 {success_count} 条记录")
    return True


def batch_create_records(
    app_token: str, table_id: str, tenant_access_token: str, records: List[Dict[str, Any]]
) -> bool:
    """批量创建记录到飞书多维表格（带重试机制）"""
    url = BITABLE_BATCH_CREATE_URL.format(app_token=app_token, table_id=table_id)
    headers = {
        "Authorization": f"Bearer {tenant_access_token}",
        "Content-Type": "application/json",
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                url,
                json={"records": records},
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            try:
                error_detail = response.json()
                code = error_detail.get("code")
                msg = error_detail.get("msg")
                
                # 1254607 表示数据未准备好，需要重试
                if code == 1254607 and attempt < MAX_RETRIES - 1:
                    print(f"   ⏳ 数据未准备好，{RETRY_DELAY}秒后重试（{attempt+1}/{MAX_RETRIES}）")
                    time.sleep(RETRY_DELAY)
                    continue
                
                print(f"❌ 批量创建失败：{exc}")
                print(f"   错误详情：code={code}, msg={msg}")
            except:
                print(f"❌ 批量创建失败：{exc}")
            return False
        
        result = response.json()
        if result.get("code") != 0:
            code = result.get("code")
            msg = result.get("msg")
            
            # 1254607 表示数据未准备好，需要重试
            if code == 1254607 and attempt < MAX_RETRIES - 1:
                print(f"   ⏳ 数据未准备好，{RETRY_DELAY}秒后重试（{attempt+1}/{MAX_RETRIES}）")
                time.sleep(RETRY_DELAY)
                continue
            
            print(f"❌ 飞书返回错误：code={code}, msg={msg}")
            return False
        
        return True
    
    return False


def main():
    print("============================================")
    print("📥 CSV 数据导入飞书多维表格")
    print("============================================")
    
    # 加载配置
    config = load_env()
    if not config:
        return
    
    app_id = config["FEISHU_APP_ID"]
    app_secret = config["FEISHU_APP_SECRET"]
    app_token = config["BITABLE_APP_TOKEN"]
    table_id = config["BITABLE_TABLE_ID"]
    
    # 读取 CSV
    if not os.path.exists(CSV_PATH):
        print(f"❌ CSV 文件不存在：{CSV_PATH}")
        return
    
    csv_records = read_csv(CSV_PATH)
    if not csv_records:
        print("❌ CSV 文件为空")
        return
    
    # 获取访问令牌
    print("🔑 正在获取飞书访问令牌...")
    token = get_tenant_access_token(app_id, app_secret)
    if not token:
        return
    
    # 删除已有记录（尝试，失败则跳过）
    print("🗑️ 正在清理已有记录...")
    if not delete_all_records(app_token, table_id, token):
        print("⚠️ 清理记录失败，继续追加导入（可能会有重复数据）")
    
    # 转换格式
    print("🔄 正在转换数据格式...")
    bitable_records = convert_to_bitable_format(csv_records)
    
    # 分批上传
    total = len(bitable_records)
    success_count = 0
    
    print(f"📤 正在分批上传到多维表格（共 {total} 条，每批 {BATCH_SIZE} 条）...")
    
    for i in range(0, total, BATCH_SIZE):
        batch = bitable_records[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"  批次 {batch_num}/{total_batches}：正在上传 {len(batch)} 条记录...")
        
        if batch_create_records(app_token, table_id, token, batch):
            success_count += len(batch)
            print(f"    ✅ 批次 {batch_num} 上传成功")
        else:
            print(f"    ❌ 批次 {batch_num} 上传失败")
    
    print("============================================")
    print(f"📊 导入完成！")
    print(f"   总记录数：{total}")
    print(f"   成功上传：{success_count}")
    print(f"   失败数量：{total - success_count}")
    print("============================================")


if __name__ == "__main__":
    main()
