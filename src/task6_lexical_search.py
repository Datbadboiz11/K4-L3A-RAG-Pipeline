"""
Task 6 — Lexical search bằng BM25.

Dùng cùng corpus chunks với Task 5. BM25 phù hợp với từ khóa chính xác, mã tài
liệu và tên riêng. Output phải theo SearchResult và sort score giảm dần.
"""


import math
import re
import numpy as np
from rank_bm25 import BM25Okapi


class SmoothBM25Okapi(BM25Okapi):
    """BM25Okapi với Lucene smoothed IDF để tránh IDF <= 0 trên corpus nhỏ."""

    def _calc_idf(self, nd):
        for word, freq in nd.items():
            self.idf[word] = math.log(1.0 + (self.corpus_size - freq + 0.5) / (freq + 0.5))


CORPUS: list[dict] = []
_CACHED_BM25: BM25Okapi | None = None
_CACHED_CORPUS_ID: int | None = None


def _tokenize(text: str) -> list[str]:
    """Tách từ đơn giản bằng regex từ và chữ thường."""
    return [w for w in re.findall(r"\w+", text.lower()) if w]


def _get_corpus() -> list[dict]:
    global CORPUS
    if not CORPUS:
        from .task4_chunking_indexing import chunk_documents, load_documents
        docs = load_documents()
        CORPUS = chunk_documents(docs)
    return CORPUS


def build_bm25_index(corpus: list[dict]) -> BM25Okapi:
    """Tạo BM25 index từ cùng corpus chunks của Task 4."""
    tokenized = [_tokenize(item["content"]) for item in corpus]
    return SmoothBM25Okapi(tokenized)


def _get_bm25(corpus: list[dict]) -> BM25Okapi:
    global _CACHED_BM25, _CACHED_CORPUS_ID
    if _CACHED_BM25 is None or _CACHED_CORPUS_ID != id(corpus):
        _CACHED_BM25 = build_bm25_index(corpus)
        _CACHED_CORPUS_ID = id(corpus)
    return _CACHED_BM25


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về BM25 SearchResult theo score giảm dần."""
    if top_k <= 0:
        return []

    corpus = _get_corpus()
    if not corpus:
        return []

    tokens = _tokenize(query)
    if not tokens:
        return []

    bm25 = _get_bm25(corpus)
    scores = bm25.get_scores(tokens)
    indices = np.argsort(scores)[::-1]

    results: list[dict] = []
    for index in indices:
        score = float(scores[index])
        if score <= 0:
            continue
        item = corpus[index]
        clean_meta = dict(item["metadata"])
        if clean_meta.get("url") == "":
            clean_meta["url"] = None
        results.append({
            "id": item["id"],
            "content": item["content"],
            "score": score,
            "metadata": clean_meta,
            "retrieval_method": "bm25",
        })
        if len(results) >= top_k:
            break

    return results


if __name__ == "__main__":
    for result in lexical_search("test query", top_k=3):
        print(result)
