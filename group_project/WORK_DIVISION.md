# BẢNG PHÂN CHIA CÔNG VIỆC DỰ ÁN RAG PIPELINE (NHÓM KDDK)

**Dự án:** Chatbot RAG tư vấn tuyển sinh Học viện Công nghệ Bưu chính Viễn thông (PTIT 2026)  
**Khóa học:** AI Thực chiến K4 — Day 8 RAG Pipeline  

---

## 1. Danh sách thành viên

| STT | Họ và tên | Mã sinh viên | Vai trò chính | Tỷ lệ đóng góp |
| :---: | :--- | :---: | :--- | :---: |
| **1** | **Thân Tiến Đạt** | **2A202603023** | Pipeline Architect & Retrieval Lead | **50%** |
| **2** | **Vũ Gia Khải** | **2A202602786** | Data Engineer & Evaluation Lead | **50%** |

---

## 2. Chi tiết phân công công việc

### Thành viên 1: Thân Tiến Đạt (2A202603023) — Pipeline Architect & Retrieval Lead
**Phạm vi trách nhiệm:** Thiết kế và hiện thực hóa kiến trúc lõi của Pipeline RAG, quản lý Indexing, thuật toán dung hợp thứ hạng RRF, luồng sinh câu trả lời có trích dẫn và tối ưu hóa chất lượng dữ liệu / truy vấn.

- **Task 4 (Chunking & Indexing):**
  - Xây dựng chiến lược phân đoạn văn bản Recursive Character Text Splitter (`chunk_size=500`, `chunk_overlap=50`).
  - Tích hợp vector store ChromaDB với Persistent Client và cosine distance space.
  - Quản lý metadata sanitization và batch upsert embedding.
- **Task 7 (RRF Reranking):**
  - Hiện thực hóa thuật toán Reciprocal Rank Fusion: $RRF(d) = \sum \frac{1}{k + rank(d)}$ với hằng số làm mượt $k=60$.
  - Khử trùng lặp tài liệu giữa Dense và Lexical Search, chuẩn hóa schema SearchResult.
- **Task 9 (Retrieval Pipeline hoàn chỉnh):**
  - Điều phối luồng tìm kiếm kết hợp (Hybrid Search: Dense + BM25).
  - Tích hợp cơ chế ngưỡng tự tin `SCORE_THRESHOLD = 0.3` và kích hoạt Fallback khi mật độ tương đồng thấp.
- **Task 10 (Generation có Citation):**
  - Thiết kế thuật toán chống hiện tượng "Lost-in-the-middle" bằng cách reorder tài liệu (đưa chunk quan trọng ra đầu và cuối).
  - Viết System Prompt chống ảo giác (hallucination), quy định trích dẫn nguồn `[Document X | Title]` nghiêm ngặt.
  - Tinh chỉnh Prompt để xử lý bài toán phân biệt 2 cơ sở đào tạo (Bắc/Nam) và loại bỏ lỗi từ chối nhầm (over-refusal).
- **Data Optimization & Multi-turn Context:**
  - Tái cấu trúc và bổ sung ngữ cảnh tự nhiên (Self-contained Semantic Bullets) cho các bảng biểu điểm chuẩn và chỉ tiêu bị cắt nhỏ.
  - Khắc phục lỗi "nhiễm ngữ cảnh câu hỏi trước" trong hàm `contextualize_query` trên ứng dụng Streamlit.

---

### Thành viên 2: Vũ Gia Khải (2A202602786) — Data Engineer & Evaluation Lead
**Phạm vi trách nhiệm:** Thu thập dữ liệu đa nguồn, chuẩn hóa văn bản thô, xây dựng các công cụ tìm kiếm thành phần, thiết lập bộ kiểm thử vàng (Golden Dataset), thực nghiệm A/B Testing và báo cáo đánh giá.

- **Task 1 (Thu thập văn bản pháp lý):**
  - Tìm kiếm, tải về và kiểm duyệt tối thiểu 3 văn bản chính sách/đề án tuyển sinh PTIT 2026 định dạng PDF/DOCX.
  - Xác thực dung lượng và tính toàn vẹn dữ liệu trong `data/landing/legal/`.
- **Task 2 (Crawl tin tức tự động):**
  - Xây dựng Web Scraper tự động với Playwright / BeautifulSoup cào tin tức điểm chuẩn, quy đổi điểm, học bổng từ cổng thông tin PTIT.
  - Trích xuất metadata chuẩn (`url`, `title`, `date_crawled`, `content_markdown`) vào `data/landing/news/`.
- **Task 3 (Chuyển đổi Markdown):**
  - Xây dựng pipeline chuyển đổi tài liệu thô (PDF, JSON) sang định dạng Markdown chuẩn hóa (`data/standardized/`).
  - Chuẩn hóa header, bảng biểu Markdown và format siêu dữ liệu thống nhất.
- **Task 5 & Task 6 (Semantic & Lexical Search):**
  - Hiện thực module Semantic Search truy vấn trực tiếp từ ChromaDB.
  - Hiện thực module Lexical Search với thuật toán BM25Okapi và tokenizer tiếng Việt.
- **Task 8 (Vectorless Search Fallback):**
  - Tích hợp cơ chế tìm kiếm dự phòng PageIndex / rule-based khi embedding gặp lỗi hoặc độ tin cậy thấp.
- **Evaluation & Benchmarking:**
  - Xây dựng bộ dữ liệu kiểm thử vàng `golden_dataset.json` (16 grounded Q&A cases phân bố đều trên nhiều chủ đề).
  - Đo lường và tính toán 4 metrics: Faithfulness, Answer Relevance, Context Recall, Latency.
  - Thực nghiệm so sánh A/B Testing (Dense vs BM25 vs Hybrid RRF) và hoàn thiện báo cáo RESULT.md.
- **Giao diện Chatbot:**
  - Xây dựng giao diện ban đầu của ứng dụng Streamlit `app.py`.
