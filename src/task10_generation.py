"""
Task 10 — Generation có citation.

Hướng dẫn:
    1. Retrieve top-k chunks.
    2. Reorder để giảm lost-in-the-middle.
    3. Format context kèm title và source.
    4. Gọi provider được chọn trong .env.
    5. Trả answer, sources và retrieval_source.

Nếu context không đủ hoặc provider lỗi, trả safe refusal; không bịa thông tin.
"""

import os

from dotenv import load_dotenv

from .task9_retrieval_pipeline import retrieve


load_dotenv()

TOP_K = 7
TOP_P = 0.9
TEMPERATURE = 0.3

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("LLM_MODEL", "")

SYSTEM_PROMPT = """Bạn là trợ lý AI chuyên gia tư vấn tuyển sinh đại học chính quy của Học viện Công nghệ Bưu chính Viễn thông (PTIT).

Hướng dẫn trả lời:
1. Trả lời chính xác, mạch lạc và đầy đủ dựa trên Context được cung cấp bên dưới.
2. Quy tắc về cơ sở đào tạo và chương trình của PTIT:
   - Học viện có 2 cơ sở: Cơ sở đào tạo phía Bắc (Hà Nội - mã BVH) và Cơ sở đào tạo phía Nam (TP.HCM - mã BVS).
   - Khi trả lời về chỉ tiêu hoặc điểm chuẩn, hãy phân biệt rõ theo từng Cơ sở đào tạo (Phía Bắc / Phía Nam) và từng Chương trình đào tạo (Đại trà, Thạc sĩ tài năng, Chất lượng cao...).
   - Nếu ngành chỉ có tại một cơ sở hoặc Context chỉ có thông tin của một cơ sở, hãy trả lời rõ ràng: 'Tại Cơ sở đào tạo phía Bắc (BVH)...' hoặc 'Tại Cơ sở đào tạo phía Nam (BVS)...'. Tuyệt đối không từ chối khi Context đã có dữ liệu của một cơ sở!
   - Trả lời đúng thuộc tính câu hỏi: Nếu hỏi về "chỉ tiêu / tuyển bao nhiêu người" thì trả lời số lượng sinh viên; nếu hỏi về "điểm chuẩn / lấy bao nhiêu điểm" thì trả lời điểm trúng tuyển.
3. Nhận diện thuật ngữ tuyển sinh:
   - "tuyển bao nhiêu người / lấy bao nhiêu người / số lượng tuyển" = chỉ tiêu tuyển sinh.
   - "lấy bao nhiêu điểm / điểm chuẩn" = điểm trúng tuyển.
4. Mỗi khẳng định quan trọng cần có trích dẫn nguồn dạng [Document X | Title].
5. Chỉ trả lời 'Tôi không thể xác minh thông tin này từ nguồn hiện có.' khi Context hoàn toàn không có bất kỳ thông tin nào liên quan."""


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """Đưa chunks quan trọng về đầu và cuối context."""
    if len(chunks) <= 2:
        return list(chunks)
    front = chunks[::2]
    back = chunks[1::2]
    return list(front) + list(back[::-1])


def format_context(chunks: list[dict]) -> str:
    """Tạo context có title và source label."""
    parts = []
    for index, chunk in enumerate(chunks, 1):
        metadata = chunk.get("metadata", {})
        title = metadata.get("title", "Tài liệu")
        source = metadata.get("source", "unknown")
        content = chunk.get("content", "")
        parts.append(
            f"[Document {index} | Title: {title} | Source: {source}]\n{content}"
        )
    return "\n\n---\n\n".join(parts)


def call_llm(system_prompt: str, user_message: str) -> str:
    """Gọi OpenAI, Gemini hoặc Anthropic theo cấu hình."""
    provider = (os.getenv("LLM_PROVIDER") or LLM_PROVIDER or "openai").lower()
    model_name = os.getenv("LLM_MODEL") or LLM_MODEL

    if provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=model_name or "gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=TEMPERATURE,
            top_p=TOP_P,
        )
        return response.choices[0].message.content or ""

    if provider == "gemini":
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel(
            model_name=model_name or "gemini-1.5-flash",
            system_instruction=system_prompt,
        )
        response = model.generate_content(user_message)
        return response.text or ""

    if provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model=model_name or "claude-3-5-sonnet-20241022",
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            max_tokens=1024,
            temperature=TEMPERATURE,
        )
        return response.content[0].text or ""

    raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """Trả về GenerationResult."""
    if top_k <= 0:
        return {
            "answer": "Tôi không thể xác minh thông tin này từ nguồn hiện có.",
            "sources": [],
            "retrieval_source": "none",
        }

    chunks = retrieve(query, top_k=top_k)
    if not chunks:
        return {
            "answer": "Tôi không thể xác minh thông tin này từ nguồn hiện có.",
            "sources": [],
            "retrieval_source": "none",
        }

    reordered = reorder_for_llm(chunks)
    context = format_context(reordered)
    user_message = f"Context:\n{context}\n\nQuestion: {query}"

    method = chunks[0].get("retrieval_method", "hybrid")
    retrieval_source = method if method in {"hybrid", "pageindex"} else "hybrid"

    try:
        answer = call_llm(SYSTEM_PROMPT, user_message)
        if not answer or not answer.strip():
            answer = "Tôi không thể xác minh thông tin này từ nguồn hiện có."
    except Exception:
        return {
            "answer": "Tôi không thể xác minh thông tin này từ nguồn hiện có.",
            "sources": chunks,
            "retrieval_source": retrieval_source,
        }

    return {
        "answer": answer,
        "sources": chunks,
        "retrieval_source": retrieval_source,
    }


if __name__ == "__main__":
    print(generate_with_citation("test query"))
