"""
Task 1 — Thu thập tài liệu chính sách/quy định.

Hướng dẫn:
    1. Chọn chủ đề của nhóm.
    2. Tìm tối thiểu 3 tài liệu PDF/DOCX từ nguồn công khai.
    3. Lưu file gốc vào data/landing/legal/.
    4. Đặt tên không dấu và thể hiện đúng nội dung.

Ví dụ tài liệu: học phí, học bổng, ký túc xá, quy trình đăng ký.
Nếu website chặn crawler, hãy chọn nguồn công khai khác; không vượt WAF.
"""

import sys
from pathlib import Path

import urllib3
import requests

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"

SOURCES = {
    "de-an-tuyen-sinh-dhcq-ptit-2026.pdf": (
        "https://tuyensinh.ptit.edu.vn/wp-content/uploads/sites/4/2026/05/QD1192.-Thong-tin-TSDHCQ-1.pdf"
    ),
    "bang-quy-doi-tuong-duong-ptit-2026.pdf": (
        "https://tuyensinh.ptit.edu.vn/wp-content/uploads/sites/4/2026/07/11.-Thong-bao-bang-duy-doi-tuong-duong-final-TB1147.pdf"
    ),
    "sua-doi-bo-sung-de-an-tuyen-sinh-ptit-2026.pdf": (
        "https://tuyensinh.ptit.edu.vn/wp-content/uploads/sites/4/2026/04/QD1547.-Sua-doi-bo-sung-de-an-tuyen-sinh.pdf"
    ),
}


def setup_directory() -> None:
    """Tạo thư mục lưu tài liệu gốc."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ready: {DATA_DIR}")


def download_documents() -> None:
    """Tải ít nhất 3 PDF/DOCX từ nguồn công khai."""
    setup_directory()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    for filename, url in SOURCES.items():
        destination = DATA_DIR / filename
        print(f"Downloading: {filename} from {url} ...")
        response = requests.get(url, headers=headers, timeout=60, verify=False)
        response.raise_for_status()
        destination.write_bytes(response.content)
        size_kb = len(response.content) / 1024
        print(f"Saved: {destination.name} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    download_documents()
