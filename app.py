import sys
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import streamlit as st
from dotenv import load_dotenv

from src.task10_generation import generate_with_citation

load_dotenv()

st.set_page_config(
    page_title="PTIT AI Assistant — Tư vấn Tuyển sinh 2026",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for rich aesthetics and clean typography
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #B31B1B;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #555555;
        margin-bottom: 1.5rem;
    }
    .badge-method {
        display: inline-block;
        padding: 3px 9px;
        font-size: 0.8rem;
        font-weight: 600;
        border-radius: 12px;
        background-color: #f0f2f6;
        color: #1f2937;
        margin-right: 6px;
    }
    .badge-hybrid {
        background-color: #e0f2fe;
        color: #0369a1;
        border: 1px solid #bae6fd;
    }
    .badge-fallback {
        background-color: #fef3c7;
        color: #92400e;
        border: 1px solid #fde68a;
    }
    .source-box {
        background: #f8fafc;
        border-left: 4px solid #B31B1B;
        padding: 10px 14px;
        margin: 8px 0;
        border-radius: 4px;
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.markdown("### 🎓 PTIT Admissions RAG")
    st.caption("Trợ lý AI tư vấn tuyển sinh đại học chính quy 2026")
    st.divider()

    st.markdown("#### ⚙️ Cấu hình truy vấn")
    top_k = st.slider("Số tài liệu trích xuất (`top_k`)", min_value=3, max_value=10, value=6, step=1)

    st.divider()
    st.markdown("#### 📚 Bộ dữ liệu chính thức")
    st.markdown(
        """
        - **Đề án tuyển sinh ĐHCQ 2026** (QĐ 1192 & QĐ 1547)
        - **Quy đổi tương đương chứng chỉ** (TB 1147)
        - **Thông báo Điểm chuẩn & Lịch nhập học** (tuyensinh.ptit.edu.vn)
        - **Chính sách học bổng & Học phí** 2026
        """
    )

    st.divider()
    st.markdown("#### 💡 Câu hỏi gợi ý")
    quick_questions = [
        "Chỉ tiêu ngành Công nghệ thông tin cơ sở Hà Nội năm 2026?",
        "Chính sách học bổng đặc biệt 500 triệu đồng có điều kiện gì?",
        "Chứng chỉ IELTS từ 7.0 đến 9.0 được cộng bao nhiêu điểm?",
        "Học phí hệ đại trà năm học 2026-2027 là bao nhiêu?",
    ]
    for q in quick_questions:
        if st.button(q, key=f"btn_{q}"):
            st.session_state.pending_query = q

    st.divider()
    if st.button("🗑️ Xóa lịch sử trò chuyện", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

st.markdown('<div class="main-title">🎓 Trợ lý Tuyển sinh Học viện Công nghệ Bưu chính Viễn thông</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Hệ thống hỏi đáp thông minh áp dụng mô hình <b>Hybrid Retrieval (Dense + BM25Okapi + RRF)</b> & <b>LLM Generation có Citation</b></div>', unsafe_allow_html=True)

# Render conversation history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and message.get("sources"):
            retrieval_src = message.get("retrieval_source", "hybrid")
            badge_class = "badge-hybrid" if retrieval_src == "hybrid" else "badge-fallback"
            st.markdown(
                f'<span class="badge-method {badge_class}">Nguồn truy vấn: {retrieval_src.upper()}</span> '
                f'<span class="badge-method">Số tài liệu: {len(message["sources"])}</span>',
                unsafe_allow_html=True,
            )
            with st.expander("📖 Xem các đoạn tài liệu trích dẫn (Evidence & Citations)"):
                for idx, src in enumerate(message["sources"], 1):
                    meta = src.get("metadata", {})
                    st.markdown(
                        f"""
                        <div class="source-box">
                            <b>[Tài liệu {idx}] {meta.get('title', 'Tài liệu')}</b><br>
                            <i>Nguồn:</i> <code>{meta.get('source', '')}</code> | 
                            <i>Phương thức:</i> <code>{src.get('retrieval_method', '')}</code> | 
                            <i>Score:</i> <code>{src.get('score', 0):.4f}</code>
                            <br><br>
                            {src.get('content', '')}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

def contextualize_query(current_query: str, history: list[dict]) -> str:
    """Bổ sung ngữ cảnh từ câu hỏi trước nếu câu hỏi hiện tại ngắn hoặc nối tiếp."""
    last_user_query = None
    for msg in reversed(history):
        if msg.get("role") == "user":
            last_user_query = msg.get("content", "").strip()
            break

    if not last_user_query:
        return current_query

    follow_up_triggers = [
        "bao nhiêu", "thế nào", "ở đâu", "khi nào", "như thế nào",
        "tuyển", "điểm", "học phí", "chỉ tiêu", "hồ sơ", "điều kiện", "người", "gì",
        "chất lượng cao", "đại trà", "cơ sở", "phía bắc", "phía nam", "hà nội", "tphcm",
        "kia là", "còn", "thế còn", "thế"
    ]
    is_short = len(current_query.split()) <= 12
    has_trigger = any(t in current_query.lower() for t in follow_up_triggers)

    if is_short and has_trigger:
        clean_prev = last_user_query.replace("?", "").strip()
        is_asking_quota = any(k in current_query.lower() for k in ["tuyển", "chỉ tiêu", "bao nhiêu người", "số lượng"])
        is_asking_score = any(k in current_query.lower() for k in ["điểm", "lấy bao nhiêu"])

        if is_asking_quota:
            for bad in ["điểm chuẩn", "điểm trúng tuyển", "lấy bao nhiêu điểm", "bao nhiêu điểm", "điểm"]:
                clean_prev = clean_prev.lower().replace(bad, "").strip()
        elif is_asking_score:
            for bad in ["chỉ tiêu", "tuyển sinh", "tuyển bao nhiêu người", "tuyển bao nhiêu", "bao nhiêu người"]:
                clean_prev = clean_prev.lower().replace(bad, "").strip()

        return f"{clean_prev} {current_query}".strip()

    return current_query


# Input handling
query_input = st.chat_input("Nhập câu hỏi của bạn về tuyển sinh PTIT 2026...")
query = query_input or st.session_state.pop("pending_query", None)

if query:
    history_before_query = list(st.session_state.messages)
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    effective_query = contextualize_query(query, history_before_query)

    with st.chat_message("assistant"):
        with st.spinner("Đang tìm kiếm tài liệu và tổng hợp câu trả lời..."):
            result = generate_with_citation(effective_query, top_k=top_k)
            answer = result.get("answer", "Không thể xử lý yêu cầu.")
            sources = result.get("sources", [])
            retrieval_source = result.get("retrieval_source", "none")

            st.markdown(answer)

            if sources:
                badge_class = "badge-hybrid" if retrieval_source == "hybrid" else "badge-fallback"
                st.markdown(
                    f'<span class="badge-method {badge_class}">Nguồn truy vấn: {retrieval_source.upper()}</span> '
                    f'<span class="badge-method">Số tài liệu: {len(sources)}</span>',
                    unsafe_allow_html=True,
                )
                with st.expander("📖 Xem các đoạn tài liệu trích dẫn (Evidence & Citations)"):
                    for idx, src in enumerate(sources, 1):
                        meta = src.get("metadata", {})
                        st.markdown(
                            f"""
                            <div class="source-box">
                                <b>[Tài liệu {idx}] {meta.get('title', 'Tài liệu')}</b><br>
                                <i>Nguồn:</i> <code>{meta.get('source', '')}</code> | 
                                <i>Phương thức:</i> <code>{src.get('retrieval_method', '')}</code> | 
                                <i>Score:</i> <code>{src.get('score', 0):.4f}</code>
                                <br><br>
                                {src.get('content', '')}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
        "retrieval_source": retrieval_source,
    })
