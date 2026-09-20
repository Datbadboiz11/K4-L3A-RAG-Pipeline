"""
Task 5 — Semantic search.

Embed query bằng chính hàm của Task 4, query ChromaDB và đổi cosine distance
thành similarity. Output phải theo SearchResult, sort giảm dần và không quá top_k.
"""

from .task4_chunking_indexing import embed_texts, get_collection


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về dense SearchResult theo score giảm dần."""
    if top_k <= 0:
        return []

    query_embeddings = embed_texts([query])
    if not query_embeddings:
        return []

    collection = get_collection()
    response = collection.query(
        query_embeddings=[query_embeddings[0]],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    if not response or not response.get("ids") or not response["ids"][0]:
        return []

    results: list[dict] = []
    ids = response["ids"][0]
    documents = response.get("documents", [[]])[0]
    metadatas = response.get("metadatas", [[]])[0]
    distances = response.get("distances", [[]])[0]

    for item_id, content, meta, distance in zip(ids, documents, metadatas, distances):
        clean_meta = dict(meta) if meta else {}
        if "chunk_index" in clean_meta and not isinstance(clean_meta["chunk_index"], int):
            try:
                clean_meta["chunk_index"] = int(clean_meta["chunk_index"])
            except (ValueError, TypeError):
                pass
        if clean_meta.get("url") == "":
            clean_meta["url"] = None

        score = max(0.0, 1.0 - float(distance))
        results.append({
            "id": item_id,
            "content": content,
            "score": score,
            "metadata": clean_meta,
            "retrieval_method": "dense",
        })

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    for result in semantic_search("test query", top_k=3):
        print(result)
