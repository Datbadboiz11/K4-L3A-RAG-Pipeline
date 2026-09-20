"""
Task 8 — PageIndex vectorless fallback.

Hướng dẫn:
    1. Đọc PAGEINDEX_API_KEY từ .env.
    2. Upload tài liệu ở định dạng PageIndex hỗ trợ.
    3. Cache document IDs để không upload lại.
    4. Parse kết quả thành SearchResult có method pageindex.

PageIndex là dịch vụ ngoài: cần timeout và xử lý lỗi để pipeline không crash.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


CACHE_FILE = Path(__file__).parent.parent / "data" / "pageindex_docs.json"


def upload_documents() -> None:
    """Upload tài liệu và lưu document IDs để tái sử dụng."""
    if not PAGEINDEX_API_KEY:
        return
    # Khi có API key, cache và upload tài liệu
    pass


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Trả về pageindex SearchResult."""
    if not PAGEINDEX_API_KEY or top_k <= 0:
        return []

    try:
        import urllib.request
        import json

        req = urllib.request.Request(
            "https://api.pageindex.ai/v1/search",
            data=json.dumps({"query": query, "top_k": top_k}).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {PAGEINDEX_API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                results = []
                for rank, item in enumerate(data.get("results", [])[:top_k], 1):
                    raw_meta = item.get("metadata", {})
                    results.append({
                        "id": str(item.get("id", f"pageindex-{rank}")),
                        "content": str(item.get("content", "")),
                        "score": float(item.get("score", 1.0 / rank)),
                        "metadata": {
                            "source": str(raw_meta.get("source", "pageindex")),
                            "title": str(raw_meta.get("title", "PageIndex Document")),
                            "doc_type": str(raw_meta.get("doc_type", "legal")),
                            "url": raw_meta.get("url"),
                            "chunk_index": int(raw_meta.get("chunk_index", 0)),
                        },
                        "retrieval_method": "pageindex",
                    })
                return results
    except Exception:
        pass
    return []


if __name__ == "__main__":
    upload_documents()
