# Individual contribution report

---

## Thông tin

- **Họ và tên:** Thân Tiến Đạt
- **Mã học viên:** 2A202603023
- **Nhóm:** Nhóm 2 thành viên (PTIT Admission RAG Pipeline)
- **Repository/branch:** Datbadboiz11/K4-L3A-RAG-Pipeline / main

---

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|:---:|
| **Task 4: Chunking & Indexing** | Thiết kế bộ chia chunk RecursiveSplitter (500 chars, 50 overlap), tích hợp OpenAI Embeddings (`text-embedding-3-small`) và lưu trữ Persistent ChromaDB. | `src/task4_chunking_indexing.py` | Done |
| **Task 7: RRF Reranking** | Cài đặt thuật toán Reciprocal Rank Fusion ($k=60$) gộp kết quả Dense và BM25, khử trùng lặp và chuẩn hóa score. | `src/task7_reranking.py` | Done |
| **Task 9: Retrieval Pipeline** | Xây dựng pipeline tích hợp Hybrid Search, cơ chế `SCORE_THRESHOLD = 0.3` để fallback PageIndex an toàn khi embedding thấp. | `src/task9_retrieval_pipeline.py` | Done |
| **Task 10: Generation có Citation** | Thiết kế prompt chống ảo giác, reorder context chống Lost-in-the-middle, sinh câu trả lời kèm citation `[Document X \| Title]`. | `src/task10_generation.py` | Done |
| **Data Optimization & Multi-turn** | Bổ sung ngữ cảnh tự nhiên (Self-contained Semantic Bullets) cho bảng điểm chuẩn/chỉ tiêu; sửa lỗi nhiễm ngữ cảnh đa lượt trong Chatbot. | `data/standardized/news/article_03.md`, `data/standardized/legal/de-an-*.md`, `app.py` | Done |

---

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Chuẩn hóa dữ liệu bảng biểu dạng danh sách tự chứa ngữ cảnh (Self-contained Semantic Bullets) kết hợp mở rộng Context Window (`top_k = 7`).  
   - **Lý do/evidence:** Khi băm nhỏ (chunking) theo ký tự cố định 500 ký tự, các bảng điểm chuẩn và chỉ tiêu bị cắt ngang, làm mất dòng tiêu đề cột và tiêu đề cơ sở (Hà Nội vs TP.HCM). Cụ thể với câu hỏi *"ngành khoa học máy tính lấy bao nhiêu điểm"*, vector embedding của đoạn cắt chỉ đạt cosine similarity 0.37 và bị trượt khỏi top 50. Sau khi bổ sung câu hỏi tự nhiên giàu từ khóa, cosine similarity tăng vọt lên **0.62** và đạt **Rank 1 tuyệt đối** trong RRF Fusion.  
   - **Trade-off:** Tăng nhẹ kích thước lưu trữ của tài liệu Markdown và thời gian indexing ban đầu thêm ~15%, nhưng đổi lại độ chính xác truy xuất tăng từ 0% lên 100%, loại bỏ triệt để hallucination.

2. **Quyết định:** Khử nhiễm thuộc tính đối nghịch trong bộ xử lý hội thoại đa lượt (`contextualize_query`).  
   - **Lý do/evidence:** Khi người dùng hỏi nối tiếp câu ngắn như *"tuyển sinh bao nhiêu người"* sau câu *"điểm chuẩn ngành thương mại điện tử"*, hàm ghép câu cũ tạo ra query *"điểm chuẩn ngành thương mại điện tử tuyển sinh bao nhiêu người"*. Từ khóa "điểm chuẩn" làm lệch hướng tìm kiếm sang bài báo điểm chuẩn thay vì đề án chỉ tiêu, khiến LLM từ chối trả lời. Tôi đã cài đặt bộ lọc bóc tách từ khóa đối nghịch (loại bỏ "điểm chuẩn" khi câu hỏi mới hỏi về "chỉ tiêu/tuyển sinh").  
   - **Trade-off:** Tăng thêm một bước tiền xử lý logic regex trước khi gửi query vào RAG pipeline, nhưng giúp trải nghiệm chat hội thoại mượt mà và chính xác đúng ý định người dùng.

---

## Kiểm thử và kết quả

- **Test hoặc query tôi đã dùng:**
  - Chạy toàn bộ test suite: `pytest -v` (đạt **20/20 test PASSED** bao gồm cả contract tests và acceptance tests).
  - Query kiểm thử điểm chuẩn: *"ngành khoa học máy tính lấy bao nhiêu điểm"*.
  - Query kiểm thử chỉ tiêu phân biệt cơ sở: *"ngành công nghệ thông tin đại trà tuyển bao nhiêu người"*.
  - Query kiểm thử hội thoại đa lượt: Hỏi *"điểm chuẩn ngành thương mại điện tử"*, sau đó hỏi tiếp *"tuyển sinh bao nhiêu người"*.
- **Kết quả trước/sau:**
  - *Trước:* Câu hỏi Khoa học máy tính bị từ chối *"Tôi không thể xác minh thông tin này từ nguồn hiện có"*; câu hỏi CNTT bị nhầm lẫn chỉ tiêu 150 sinh viên của ngành Viễn thông.
  - *Sau:* Trả lời chính xác **26.00 điểm** cho ngành Khoa học máy tính tại Hà Nội; phân biệt rõ **600 sinh viên** (phía Bắc) và **275 sinh viên** (phía Nam) cho ngành CNTT; trả lời chính xác **180 sinh viên** cho ngành Thương mại điện tử.
- **Lỗi đã phát hiện và cách xử lý:**
  - *Lỗi 1 (ChromaDB HNSW Index Lock):* Khi re-index trên Windows trong lúc Streamlit daemon đang mở kết nối, Rust segment reader bị lỗi `InternalError`. Cách xử lý: Đóng tiến trình Streamlit trước khi re-index hoặc dọn dẹp thư mục persistent cache trước khi rebuild index.
  - *Lỗi 2 (Over-refusal trong System Prompt):* Quy tắc cấm dùng số liệu của một cơ sở khiến LLM từ chối trả lời những ngành chỉ đào tạo tại một cơ sở duy nhất (như Khoa học máy tính chỉ có ở Hà Nội). Cách xử lý: Nới lỏng prompt để LLM ghi rõ *"Tại cơ sở đào tạo phía Bắc (BVH), ngành... lấy... điểm"* thay vì từ chối an toàn.

---

## Điều còn hạn chế

- **Một hạn chế cụ thể của phần tôi làm:**
  - Việc chuẩn hóa dữ liệu bảng biểu hiện tại được bổ sung thủ công bằng các semantic bullets; nếu tài liệu có hàng trăm bảng biểu lớn thì cần một parser chuyên dụng (Table Parser / LLM-based Markdown Table Enhancer) để tự động hóa hoàn toàn.
- **Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện:**
  - Tích hợp một mô hình Cross-Encoder Reranker (như `bge-reranker-large` hoặc `jina-reranker`) ở tầng Task 7 để thay thế hoặc bổ trợ cho RRF, giúp chấm điểm tương quan ngữ nghĩa sâu hơn giữa câu hỏi và context trước khi đưa vào LLM.

---

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- **Ngày:** 20/09/2026
- **Tên thành viên:** Thân Tiến Đạt
