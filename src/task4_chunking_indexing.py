import os
from pathlib import Path
import sys

from dotenv import load_dotenv

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai").lower()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIM = 1536 if "openai" in EMBEDDING_PROVIDER else 1024

COLLECTION_NAME = "rag_documents"


class SimpleRecursiveSplitter:
    """Bộ tách văn bản recursive dự phòng tuân thủ nghiêm ngặt contract."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50, separators: list[str] | None = None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", "; ", ", ", " ", ""]

    def split_text(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, text: str, separators: list[str]) -> list[str]:
        if len(text) <= self.chunk_size:
            return [text] if text.strip() else []

        separator = separators[-1]
        new_separators = []
        for i, s in enumerate(separators):
            if s == "":
                separator = ""
                break
            if s in text:
                separator = s
                new_separators = separators[i + 1:]
                break

        splits = text.split(separator) if separator else list(text)
        good_splits = []
        for s in splits:
            if not s.strip() and separator:
                continue
            if len(s) <= self.chunk_size:
                good_splits.append(s)
            else:
                if new_separators:
                    good_splits.extend(self._split(s, new_separators))
                else:
                    step = max(1, self.chunk_size - self.chunk_overlap)
                    for idx in range(0, len(s), step):
                        part = s[idx : idx + self.chunk_size]
                        if part.strip():
                            good_splits.append(part)

        max_allowed = int(self.chunk_size * 1.05)
        merged = []
        current = ""
        for s in good_splits:
            if not current:
                current = s
            elif len(current) + len(separator) + len(s) <= self.chunk_size:
                current = current + separator + s
            else:
                if current.strip():
                    merged.append(current.strip())
                if self.chunk_overlap > 0:
                    overlap_chars = current[-self.chunk_overlap:]
                    candidate = overlap_chars + separator + s
                    current = candidate if len(candidate) <= max_allowed else s
                else:
                    current = s
        if current.strip():
            merged.append(current.strip())
        return merged


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Tạo vector embeddings theo cấu hình EMBEDDING_PROVIDER trong .env."""
    load_dotenv()
    provider = os.getenv("EMBEDDING_PROVIDER", "openai").lower()

    if provider == "openai":
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY chưa được thiết lập trong .env")
        client = OpenAI(api_key=api_key)
        model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

        all_vectors: list[list[float]] = []
        batch_size = 64
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            response = client.embeddings.create(input=batch, model=model)
            for item in response.data:
                all_vectors.append(item.embedding)
        return all_vectors

    elif provider == "sentence_transformers":
        from sentence_transformers import SentenceTransformer

        model_name = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")
        model = SentenceTransformer(model_name)
        return model.encode(texts).tolist()

    else:
        raise ValueError(f"EMBEDDING_PROVIDER không hỗ trợ: {provider}")


def get_collection():
    """Mở Chroma collection dùng cosine distance."""
    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def load_documents() -> list[dict]:
    """Đọc Markdown và trả về danh sách Document."""
    documents = []
    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        doc_type = "legal" if "legal" in path.parts else "news"
        raw_text = path.read_text(encoding="utf-8")
        title = path.stem
        url = None

        lines = raw_text.splitlines()
        for line in lines[:10]:
            if line.startswith("# ") and title == path.stem:
                title = line[2:].strip()
            elif line.startswith("**Source:**") or line.startswith("**Source Document:**"):
                parts = line.split(":", 1)
                if len(parts) > 1:
                    url = parts[1].strip().strip("*").strip()

        documents.append(
            {
                "id": path.relative_to(STANDARDIZED_DIR).as_posix(),
                "content": raw_text,
                "metadata": {
                    "source": path.name,
                    "title": title,
                    "doc_type": doc_type,
                    "url": url,
                },
            }
        )
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chia Document thành chunks có id và chunk_index."""
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", "; ", ", ", " ", ""],
        )
    except ImportError:
        splitter = SimpleRecursiveSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", "; ", ", ", " ", ""],
        )

    chunks = []
    for document in documents:
        doc_id = document["id"]
        doc_meta = document["metadata"]
        raw_splits = splitter.split_text(document["content"])
        for index, text in enumerate(raw_splits):
            chunks.append(
                {
                    "id": f"{doc_id}::chunk-{index}",
                    "content": text,
                    "metadata": {
                        **doc_meta,
                        "chunk_index": index,
                    },
                }
            )
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Thêm embedding vào từng chunk."""
    texts = [chunk["content"] for chunk in chunks]
    vectors = embed_texts(texts)
    for chunk, vector in zip(chunks, vectors):
        chunk["embedding"] = vector
    return chunks


def index_to_vectorstore(chunks: list[dict]) -> None:
    """Upsert chunks vào ChromaDB."""
    collection = get_collection()
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        sanitized_metadatas = []
        for c in batch:
            m = dict(c["metadata"])
            if m.get("url") is None:
                m["url"] = ""
            sanitized_metadatas.append(m)

        collection.upsert(
            ids=[c["id"] for c in batch],
            documents=[c["content"] for c in batch],
            embeddings=[c["embedding"] for c in batch],
            metadatas=sanitized_metadatas,
        )


def run_pipeline() -> None:
    """Chạy load, chunk, embed và index."""
    documents = load_documents()
    print(f"Loaded {len(documents)} documents.")
    chunks = chunk_documents(documents)
    print(f"Created {len(chunks)} chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}).")
    print("Generating embeddings ...")
    embedded_chunks = embed_chunks(chunks)
    print("Indexing to ChromaDB ...")
    index_to_vectorstore(embedded_chunks)
    print(f"Indexed {len(embedded_chunks)} chunks into ChromaDB collection '{COLLECTION_NAME}' successfully!")


if __name__ == "__main__":
    run_pipeline()
