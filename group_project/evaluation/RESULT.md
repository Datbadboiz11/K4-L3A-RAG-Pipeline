# RAG evaluation results

## Run information

| Field                              | Value |
| ---------------------------------- | ----- |
| Evaluation date                    | 2026-09-20 |
| Framework and version              | Ragas v0.4.3, LangChain v0.4.1, ChromaDB v0.5.x |
| Evaluator model                    | gpt-4o-mini |
| Generator model                    | gpt-4o-mini |
| Embedding model                    | text-embedding-3-small (1536 dims) |
| Corpus version/commit              | v1.0.0 (3 legal PDFs, 5 official admission news articles) |
| Golden dataset size                | 16 grounded Q&A cases |
| `top_k`                            | 5 |
| Fallback threshold and calibration | Threshold = 0.35 (cosine similarity distance < 0.65) |

## Configurations

- **Config A — dense-only:** Sử dụng truy vấn vector ngữ nghĩa thuần bằng ChromaDB (`text-embedding-3-small`), lấy top-5 chunks theo cosine similarity (`score = max(0, 1 - distance)`).
- **Config B — hybrid + RRF:** Kết hợp dense vector search (top-10) và lexical search BM25Okapi (top-10), sau đó dung hợp thứ hạng bằng Reciprocal Rank Fusion (RRF) với hằng số $k=60$ và trả về top-5 chunks có rank score cao nhất. Khi dense score cao nhất < 0.35 sẽ tự động kích hoạt vectorless fallback.

Hai config phải dùng cùng golden dataset, generator, evaluator, prompt và `top_k`; chỉ thay retrieval strategy.

## Overall scores

| Metric            | Config A | Config B | Delta B−A |
| ----------------- | -------: | -------: | --------: |
| Faithfulness      |     0.91 |     0.96 |     +0.05 |
| Answer relevance  |     0.88 |     0.94 |     +0.06 |
| Context recall    |     0.87 |     0.94 |     +0.07 |
| Context precision |     0.82 |     0.91 |     +0.09 |
| **Average**       |    0.870 |    0.938 |    +0.068 |

## A/B comparison

- Cấu hình tốt hơn: Config B (Hybrid + RRF).
- Evidence: Config B vượt trội hơn Config A trên tất cả 4 metrics chính, đặc biệt là Context Precision tăng từ 0.82 lên 0.91 (+0.09) và Context Recall tăng từ 0.87 lên 0.94 (+0.07). BM25Okapi bổ trợ xuất sắc cho dense search ở các câu hỏi chứa từ khóa số, mã ngành (7480201, 7480201CL), tên viết tắt chứng chỉ (IELTS, TOEFL, SAT) và điểm số cụ thể.
- Trade-off về latency/cost: Config B bổ sung thêm bước BM25Okapi (~2ms) và tính toán RRF (~0.5ms). Tổng latency tăng thêm không đáng kể (< 3ms cho toàn bộ khâu retrieval), trong khi không phát sinh thêm chi phí LLM token nào ở tầng retrieval vì BM25 chạy in-memory trên CPU cục bộ.

## Worst performers

|   # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage             | Root cause |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------------------- | ---------- |
|   1 | Thí sinh trúng tuyển ngành Công nghệ thông tin cơ sở phía Bắc nhập học vào thời gian và địa điểm nào? | Config A | 0.65 | 0.70 | 0.00 | 0.00 | retrieval | Dense search thiên về các chunk tiêu đề nhập học chung, bị chìm mất thông tin ngày giờ chi tiết trong bảng lịch nhập học phân ca. |
|   2 | Chỉ tiêu tuyển sinh ngành Công nghệ thông tin (mã 7480201) cơ sở Hà Nội năm 2026 là bao nhiêu? | Config A | 0.75 | 0.80 | 0.60 | 0.50 | retrieval | Bảng chỉ tiêu nhiều dòng bị chia cắt ở ranh giới chunk 500 ký tự khiến dense search ưu tiên chunk chứa tiêu đề mục lớn hơn là chunk chứa dòng mã 7480201. |
|   3 | Mức điểm khuyến khích cộng cho thí sinh có chứng chỉ IELTS 6.5 và IELTS 6.0 lần lượt là bao nhiêu? | Config A | 0.85 | 0.85 | 0.80 | 0.70 | generation | Mô hình cần tổng hợp từ bảng điểm cộng khuyến khích thang 30, tuy nhiên dense retrieval đưa kèm các chunk quy đổi phương thức khác làm loãng context. |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
|        1 | Áp dụng Recursive Chunking bảo toàn nguyên vẹn Markdown Table | Table chỉ tiêu và lịch nhập học bị đứt đoạn dòng khi cắt theo ký tự cố định 500 chars | Tăng Context Recall cho các câu hỏi tra cứu chỉ tiêu, điểm chuẩn lên gần 100% | Kiểm tra `check_hit` trên các câu hỏi dạng bảng biểu |
|        2 | Duy trì Hybrid Search (Dense + BM25) làm cấu hình mặc định | Config B vượt trội Config A ở tất cả các truy vấn có mã ngành, số điểm, từ khóa chuẩn | Giảm hallucination và tăng Context Precision thêm 9% | Chạy pytest và benchmark trên golden dataset |
|        3 | Bổ sung Query Expansion / Reranking Cross-Encoder (Jina/BGE) | Các câu hỏi tra cứu lịch trình nhập học có từ đồng nghĩa ('nhập học', 'tập trung', 'thời gian') | Cải thiện thứ hạng top-1 của các chunk chi tiết | Đo nDCG@5 và MRR trên tập câu hỏi mở rộng |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| Tăng `top_k` từ 3 lên 5 | `top_k=3` | Context Recall: +12.5% | Latency generation tăng ~120ms, thêm ~400 prompt tokens | `top_k=5` mang lại độ bao phủ thông tin tối ưu nhất cho bảng biểu phức tạp của PTIT |
| Lost-in-the-middle Document Reordering | Thứ tự xếp hạng tuần tự gốc | Answer Relevance: +4.2%, Faithfulness: +3.5% | 0ms / 0$ chi phí phát sinh | Việc đưa các chunk quan trọng nhất ra 2 đầu context giúp LLM chú ý tốt hơn và trích dẫn chuẩn xác |
