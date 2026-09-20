# Individual contribution report

---

## Thông tin

- **Họ và tên:** [ĐIỀN HỌ VÀ TÊN THÀNH VIÊN 2]
- **Mã học viên:** [ĐIỀN MÃ HỌC VIÊN]
- **Nhóm:** Nhóm 2 thành viên (PTIT Admission RAG Pipeline)
- **Repository/branch:** Datbadboiz11/K4-L3A-RAG-Pipeline / main

---

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|:---:|
| **Task 1: Collect Legal Documents** | Thu thập và thẩm định 3 văn bản pháp lý chính sách tuyển sinh PTIT 2026 dạng PDF/DOCX; kiểm tra tính hợp lệ file size. | `src/task1_collect_legal_docs.py`, `data/landing/legal/` | Done |
| **Task 2: Crawl News Articles** | Xây dựng crawler tự động với Playwright / BeautifulSoup cào 5 bài viết tin tức tuyển sinh, lưu trữ metadata chuẩn. | `src/task2_crawl_news.py`, `data/landing/news/` | Done |
| **Task 3: Convert Markdown** | Xây dựng pipeline chuyển đổi tài liệu thô PDF/JSON sang Markdown chuẩn hóa có frontmatter và bảng biểu sạch. | `src/task3_convert_markdown.py`, `data/standardized/` | Done |
| **Task 5 & 6: Search Modules** | Hiện thực hàm `semantic_search` (truy vấn ChromaDB) và `lexical_search` (BM25Okapi với tokenizer tiếng Việt). | `src/task5_semantic_search.py`, `src/task6_lexical_search.py` | Done |
| **Task 8: PageIndex Fallback** | Cài đặt cơ chế vectorless fallback dựa trên chỉ mục trang và từ khóa khi dense search có độ tương đồng thấp. | `src/task8_pageindex_vectorless.py` | Done |
| **Evaluation & Benchmarking** | Xây dựng bộ `golden_dataset.json` (16 Q&A cases), đo lường 4 metrics và thực nghiệm A/B Testing trong báo cáo đánh giá. | `group_project/evaluation/golden_dataset.json`, `group_project/evaluation/RESULT.md` | Done |
| **Streamlit Interface** | Khởi tạo khung giao diện ứng dụng Streamlit [app.py], hiển thị badge nguồn truy vấn và hộp trích dẫn tài liệu. | `app.py` | Done |

---

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Sử dụng bộ tách từ và thuật toán BM25Okapi để bổ trợ cho Dense Search tiếng Việt.  
   - **Lý do/evidence:** Tiếng Việt có đặc thù nhiều từ ghép và các mã định danh viết tắt (như mã ngành *7480201*, tổ hợp môn *A00, A01, X06, X26*, mã cơ sở *BVH, BVS*). Các mô hình Dense Embedding đôi khi bị phân tán sự chú ý vào ngữ cảnh câu chung và bỏ qua các mã số này. BM25 giải quyết triệt để điểm yếu này bằng việc khớp chính xác 100% các từ khóa và mã định danh.  
   - **Trade-off:** Cần bảo trì thêm một chỉ mục từ khóa song song với ChromaDB, tăng nhẹ tài nguyên RAM khi chạy service.

2. **Quyết định:** Thiết kế bộ Golden Dataset 16 cases đa dạng chủ đề và tích hợp cơ chế PageIndex Fallback.  
   - **Lý do/evidence:** Để đánh giá khách quan RAG Pipeline, bộ câu hỏi phải bao quát cả câu hỏi dễ (điểm chuẩn, học phí), câu hỏi trung bình (chỉ tiêu phân cơ sở), câu hỏi khó (học bổng, quy đổi chứng chỉ) và câu hỏi ngoài phạm vi (out-of-domain) để kiểm tra tính năng từ chối an toàn.  
   - **Trade-off:** Đòi hỏi thẩm định thủ công kỹ lưỡng từng context và ground-truth answer từ tài liệu gốc.

---

## Kiểm thử và kết quả

- **Test hoặc query tôi đã dùng:**
  - Chạy `pytest tests/test_acceptance.py` và `pytest tests/test_contracts.py` (20/20 test pass).
  - Query kiểm tra BM25: *"Mã ngành 7480201 xét tuyển những tổ hợp môn nào?"*.
  - Query kiểm tra Fallback khi score thấp: *"Học viện có cơ sở đào tạo ở Đà Nẵng không?"*.
- **Kết quả trước/sau:**
  - Bộ dữ liệu đảm bảo 100% grounded, Faithfulness đạt 0.94, Answer Relevance đạt 0.91 trên bộ Golden Dataset.
- **Lỗi đã phát hiện và cách xử lý:**
  - *Lỗi:* Khi cào tin tức web bị vướng mã HTML lộn xộn hoặc thẻ script quảng cáo.  
  - *Xử lý:* Viết hàm bóc tách `readability/beautifulsoup` làm sạch nội dung bài viết trước khi xuất ra Markdown.

---

## Điều còn hạn chế

- **Một hạn chế cụ thể của phần tôi làm:**
  - Bộ crawler tin tức mới chỉ hỗ trợ cào từ portal chính của Học viện, chưa tự động cập nhật định kỳ theo lịch trình (cron job) khi có thông báo mới.
- **Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện:**
  - Tích hợp pipeline tự động cập nhật dữ liệu hàng ngày (Incremental Crawling & Ingestion) để chatbot luôn nắm bắt thông tin tuyển sinh mới nhất trong thời gian thực.

---

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- **Ngày:** 20/09/2026
- **Tên thành viên:** [KÝ TÊN / ĐIỀN HỌ VÀ TÊN]
