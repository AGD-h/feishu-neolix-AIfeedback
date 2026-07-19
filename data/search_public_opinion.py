import argparse
import csv
import os
import random
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv


SERPAPI_ENDPOINT = "https://serpapi.com/search.json"
OUTPUT_FIELDS = [
    "lead_id",
    "source_platform",
    "keyword",
    "title",
    "snippet",
    "url",
    "collected_at",
    "ai_relevant",
    "ai_user_tier",
    "ai_issue_type",
    "ai_confidence",
    "review_status",
    "review_note",
]
PLATFORM_LABELS = {
    "xhs": "小红书",
    "weibo": "微博",
    "zhihu": "知乎",
    "blackcat": "黑猫投诉",
}
KEYWORD_MATRIX = {
    "xhs": [
        "site:xiaohongshu.com 无人配送车",
        "site:xiaohongshu.com 无人快递车",
        "site:xiaohongshu.com 无人车 取件",
        "site:xiaohongshu.com 无人车 挡路",
        "site:xiaohongshu.com 无人车 柜门打不开",
        "site:xiaohongshu.com 顺丰 无人车",
        "site:xiaohongshu.com 无人车 小区",
        "site:xiaohongshu.com 无人车 配送",
    ],
    "weibo": [
        "site:weibo.com 无人配送车",
        "site:weibo.com 无人车 挡路",
        "site:weibo.com 无人车 取件",
    ],
    "zhihu": [
        "site:zhihu.com 无人配送车",
        "site:zhihu.com 无人车 取件",
    ],
    "blackcat": [
        "site:tousu.sina.com.cn 无人配送车",
        "site:tousu.sina.com.cn 无人快递车",
        "site:tousu.sina.com.cn 无人车 投诉",
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="公开舆情线索采集 Demo：通过 SerpAPI 搜索公开网页标题、摘要和 URL。"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="每个关键词最多采集多少条，默认 5。",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印采集结果，不写入 CSV 文件。",
    )
    parser.add_argument(
        "--platform",
        choices=["xhs", "weibo", "zhihu", "blackcat", "all"],
        default="all",
        help="选择采集平台：xhs / weibo / zhihu / blackcat / all，默认 all。",
    )
    return parser.parse_args()


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_serpapi_key(project_root: Path) -> str | None:
    load_dotenv(project_root / ".env")
    serpapi_key = os.getenv("SERPAPI_KEY", "").strip()
    if not serpapi_key:
        print("未找到 SERPAPI_KEY。")
        print("请先到 https://serpapi.com 注册账号，获取 API Key。")
        print("然后把下面这一行填入项目根目录的 .env 文件：")
        print("SERPAPI_KEY=你的SerpAPIKey")
        return None
    return serpapi_key


def get_selected_keywords(platform: str) -> list[tuple[str, str]]:
    if platform == "all":
        selected_platforms = ["xhs", "weibo", "zhihu", "blackcat"]
    else:
        selected_platforms = [platform]

    keywords = []
    for platform_key in selected_platforms:
        for keyword in KEYWORD_MATRIX[platform_key]:
            keywords.append((platform_key, keyword))
    return keywords


def detect_source_platform(url: str, fallback_platform_key: str) -> str:
    domain = urlparse(url).netloc.lower()
    if "xiaohongshu.com" in domain:
        return "小红书"
    if "weibo.com" in domain:
        return "微博"
    if "zhihu.com" in domain:
        return "知乎"
    if "tousu.sina.com.cn" in domain:
        return "黑猫投诉"
    return PLATFORM_LABELS[fallback_platform_key]


def search_keyword(serpapi_key: str, keyword: str, limit: int) -> list[dict]:
    params = {
        "engine": "google",
        "q": keyword,
        "hl": "zh-cn",
        "num": limit,
        "api_key": serpapi_key,
    }

    try:
        response = requests.get(SERPAPI_ENDPOINT, params=params, timeout=20)
    except requests.RequestException as exc:
        print(f"关键词请求失败：{keyword}")
        print(f"原因：{exc}")
        return []

    try:
        data = response.json()
    except ValueError:
        print(f"关键词返回内容不是合法 JSON：{keyword}")
        print(f"HTTP 状态码：{response.status_code}")
        return []

    if "error" in data:
        print(f"SerpAPI 返回错误：{keyword}")
        print(data["error"])
        return []

    return data.get("organic_results", [])


def build_lead(
    index: int,
    platform_key: str,
    keyword: str,
    result: dict,
    collected_at: str,
) -> dict | None:
    url = result.get("link", "").strip()
    if not url:
        return None

    today = datetime.now().strftime("%Y%m%d")
    return {
        "lead_id": f"LEAD-{today}-{index:04d}",
        "source_platform": detect_source_platform(url, platform_key),
        "keyword": keyword,
        "title": result.get("title", "").strip(),
        "snippet": result.get("snippet", "").strip(),
        "url": url,
        "collected_at": collected_at,
        "ai_relevant": "",
        "ai_user_tier": "",
        "ai_issue_type": "",
        "ai_confidence": "",
        "review_status": "待复核",
        "review_note": "",
    }


def collect_leads(serpapi_key: str, platform: str, limit: int) -> list[dict]:
    selected_keywords = get_selected_keywords(platform)
    leads = []
    seen_urls = set()

    for keyword_index, (platform_key, keyword) in enumerate(selected_keywords, start=1):
        results = search_keyword(serpapi_key, keyword, limit)
        added_count = 0
        collected_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for result in results:
            if added_count >= limit:
                break

            url = result.get("link", "").strip()
            if not url or url in seen_urls:
                continue

            lead = build_lead(
                index=len(leads) + 1,
                platform_key=platform_key,
                keyword=keyword,
                result=result,
                collected_at=collected_at,
            )
            if lead is None:
                continue

            seen_urls.add(url)
            leads.append(lead)
            added_count += 1

        print(f"关键词：{keyword}，新增线索 {added_count} 条")

        # 降低请求频率，避免短时间内连续请求搜索接口。
        if keyword_index < len(selected_keywords):
            time.sleep(random.uniform(1, 2))

    return leads


def write_csv(output_path: Path, leads: list[dict]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(leads)


def print_dry_run(leads: list[dict]) -> None:
    print("dry-run 模式：以下为本次采集结果预览，不会写入文件。")
    for lead in leads:
        print(
            f"{lead['lead_id']} | {lead['source_platform']} | "
            f"{lead['title']} | {lead['url']}"
        )


def main() -> None:
    args = parse_args()
    if args.limit <= 0:
        print("--limit 必须大于 0。")
        return

    project_root = get_project_root()
    serpapi_key = load_serpapi_key(project_root)
    if serpapi_key is None:
        return

    output_path = project_root / "data" / "output" / "public_opinion_leads.csv"
    leads = collect_leads(
        serpapi_key=serpapi_key,
        platform=args.platform,
        limit=args.limit,
    )

    print(f"总去重数量：{len(leads)} 条")
    print(f"输出路径：{output_path}")

    if args.dry_run:
        print_dry_run(leads)
        return

    write_csv(output_path, leads)
    print("CSV 写入完成。")


if __name__ == "__main__":
    main()
