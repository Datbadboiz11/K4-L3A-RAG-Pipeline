"""
Task 2 — Crawl bài viết/thông báo.

Hướng dẫn:
    1. Điền tối thiểu 5 URL công khai vào ARTICLE_URLS.
    2. Crawl từng URL bằng Crawl4AI.
    3. Lưu mỗi bài thành một JSON trong data/landing/news/.
    4. Giữ đủ url, title, date_crawled và content_markdown.

Cài browser trước khi chạy:
    python -m playwright install chromium
    
-> Dùng Firecrawl or bất cứ công cụ nào bạn quen    
"""

import asyncio
from datetime import datetime
import json
from pathlib import Path
import sys

import urllib3
import requests
from bs4 import BeautifulSoup

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

ARTICLE_URLS = [
    "https://tuyensinh.ptit.edu.vn/thong-bao-bang-quy-doi-tuong-duong-giua-cac-phuong-thuc-xet-tuyen-dai-hoc-he-chinh-quy-nam-2026/",
    "https://tuyensinh.ptit.edu.vn/thong-bao-phuong-thuc-tuyen-sinh-dai-hoc-he-chinh-quy-nam-2025/",
    "https://tuyensinh.ptit.edu.vn/thong-bao-diem-chuan-trung-tuyen-vao-dai-hoc-he-chinh-quy-nam-2026/",
    "https://tuyensinh.ptit.edu.vn/gioi-thieu/chinh-sach-hoc-bong/",
    "https://tuyensinh.ptit.edu.vn/thong-bao-ve-viec-nhap-hoc-dai-hoc-chinh-quy-nam-2026-co-so-dao-tao-phia-bac-bvh/",
]


def html_to_markdown(soup: BeautifulSoup) -> str:
    """Chuyển đổi thẻ HTML bài viết sang định dạng Markdown sạch."""
    content_el = (
        soup.find("article")
        or soup.find("div", class_="entry-content")
        or soup.find("div", class_="elementor-widget-theme-post-content")
        or soup.body
    )
    if not content_el:
        return ""

    # Loại bỏ các thẻ không liên quan
    for tag in content_el.find_all(
        ["script", "style", "nav", "header", "footer", "noscript", "svg", "form"]
    ):
        tag.decompose()

    # Chuyển đổi bảng sang Markdown table
    for table in content_el.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue
        md_table: list[str] = []
        for r_idx, row in enumerate(rows):
            cols = [
                c.get_text(separator=" ")
                .strip()
                .replace("\n", " ")
                .replace("|", "\\|")
                for c in row.find_all(["th", "td"])
            ]
            if not cols:
                continue
            md_table.append("| " + " | ".join(cols) + " |")
            if r_idx == 0:
                md_table.append("| " + " | ".join(["---"] * len(cols)) + " |")
        table_str = "\n".join(md_table)
        table.replace_with(soup.new_string("\n\n" + table_str + "\n\n"))

    # Chuyển đổi tiêu đề h1 -> h6
    for h in content_el.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        level = int(h.name[1])
        h_text = h.get_text().strip()
        h.replace_with(soup.new_string(f"\n\n{'#' * level} {h_text}\n\n"))

    # Chuyển đổi danh sách li
    for li in content_el.find_all("li"):
        li_text = li.get_text().strip()
        li.replace_with(soup.new_string(f"\n- {li_text}"))

    lines = [line.strip() for line in content_el.get_text().splitlines() if line.strip()]
    return "\n\n".join(lines)


async def crawl_article(url: str) -> dict:
    """Crawl bài viết từ URL và trả về dict đúng schema."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    loop = asyncio.get_running_loop()
    response = await loop.run_in_executor(
        None, lambda: requests.get(url, headers=headers, timeout=30, verify=False)
    )
    response.raise_for_status()
    response.encoding = "utf-8"

    soup = BeautifulSoup(response.text, "html.parser")
    title_el = soup.find("h1") or soup.find("title")
    raw_title = title_el.get_text().strip() if title_el else "Thông báo tuyển sinh PTIT"

    for sep in ("– PTIT", "- PTIT", "–", "|"):
        if sep in raw_title:
            raw_title = raw_title.split(sep)[0].strip()

    content_markdown = html_to_markdown(soup)
    if not content_markdown:
        content_markdown = raw_title

    return {
        "url": url,
        "title": raw_title,
        "date_crawled": datetime.now().isoformat(),
        "content_markdown": content_markdown,
    }


async def crawl_all() -> None:
    """Crawl và lưu từng bài thành một file JSON."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for index, url in enumerate(ARTICLE_URLS, 1):
        try:
            print(f"[{index}/{len(ARTICLE_URLS)}] Crawling: {url} ...")
            article = await crawl_article(url)
            output = DATA_DIR / f"article_{index:02d}.json"
            output.write_text(
                json.dumps(article, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"Saved: {output.name} ({len(article['content_markdown'])} chars)")
        except Exception as error:
            print(f"Failed: {url} — {error}")


if __name__ == "__main__":
    asyncio.run(crawl_all())
