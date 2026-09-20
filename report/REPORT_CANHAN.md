# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Lê Trung Kiên  
**Nhóm:** So1 
**Ngày:** 20/09/2026  

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao nghĩa là hai vector chỉ cùng hướng trong không gian đặc trưng nhiều chiều, thể hiện hai đoạn văn bản có nội dung và ý nghĩa ngữ nghĩa rất tương đồng với nhau, không phụ thuộc vào độ dài ngắn của đoạn văn.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Khách hàng có thể yêu cầu trả hàng và hoàn tiền trong vòng 7 ngày."
- Câu B: "Chính sách đổi trả hàng được áp dụng trong thời hạn 7 ngày kể từ khi nhận hàng."
- Tại sao tương đồng: Cả hai câu đều biểu diễn cùng một ý nghĩa nghiệp vụ (quy định thời hạn đổi trả/hoàn tiền 7 ngày).

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Khách hàng có thể yêu cầu trả hàng và hoàn tiền trong vòng 7 ngày."
- Câu B: "Hệ thống máy chủ sử dụng cơ sở dữ liệu PostgreSQL."
- Tại sao khác: Hai câu thuộc hai lĩnh vực hoàn toàn khác nhau (chính sách bán hàng vs hạ tầng CNTT), không chứa các từ khóa ngữ nghĩa liên quan.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity đo góc giữa hai vector thay vì khoảng cách tuyệt đối giữa hai điểm cuối. Điều này giúp loại bỏ ảnh hưởng của độ dài văn bản (một văn bản dài lặp lại từ sẽ có độ dài vector lớn nhưng góc vector so với văn bản ngắn có cùng chủ đề vẫn không đổi).

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> (10,000 - 50) / (500 - 50) = 9,950 / 450 = 22.11
> *Đáp án:* **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap=100: (10,000 - 100) / (500 - 100) = 9,900 / 400 = 24.75 -> **25 chunks** (tăng 2 chunks). Tăng độ chồng chéo giúp thông tin ở ranh giới cắt không bị gián đoạn giữa 2 chunks liên tiếp.


---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng regex pattern `r'(?<=[.!?])\s+|\n+'` (Lookbehind ngắt ranh giới câu) để tách câu theo `. `, `! `, `? `, `.\n`. Gom các câu lại thành nhóm tối đa `max_sentences_per_chunk` câu và dùng `.strip()` cho các trường hợp ngoại lệ, loại bỏ khoảng trắng thừa và xử lý văn bản rỗng trả về.


**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Áp dụng thuật toán chia đệ quy duyệt qua ưu tiên các dấu phân cách `["\n\n", "\n", ". ", " ", ""]`. Nếu đoạn văn dài hơn chunk_size, thuật toán sẽ tách theo dấu phân cách hiện tại; nếu đoạn con nào vẫn vượt quá chunk_size, tiếp tục gọi đệ quy `_split` với dấu phân cách tiếp theo. Base case là khi chuỗi nhỏ hơn hoặc bằng chunk_size hoặc hết dấu phân cách.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Lưu trữ danh sách dạng In-Memory `list[dict]` chứa `id`, `content`, `metadata`, và `embedding` được tạo bởi `self._embedding_fn`. Khi gọi `search`, tính điểm tích vô hướng (dot product) giữa vector câu hỏi và vector từng chunk, sắp xếp giảm dần theo điểm `score` và lấy `top_k` kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` thực hiện lọc dữ liệu trước (Pre-filtering) dựa trên cặp khóa-giá trị trong `metadata_filter`, sau đó mới tìm kiếm vector trên danh sách đã lọc. Xóa bằng cách dùng `delete_document` loại bỏ tất cả các record có `id` hoặc `metadata['doc_id']` trùng với `doc_id` và trả về `True` nếu số lượng phần tử giảm.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Thực hiện quy trình RAG: Gọi `store.search(question, top_k)` để lấy danh sách chunks liên quan nhất, định dạng thành chuỗi ngữ cảnh `Context:\n- chunk1\n- chunk2...`, sau đó tạo prompt `Context:\n{context}\n\nQuestion: {question}\nAnswer:` và gọi `self.llm_fn(prompt)` để trả về kết quả.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
# Dán kết quả (output) của: pytest tests/ -v
================================================== test session starts ==================================================
platform win32 -- Python 3.13.5, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\kient\AppData\Local\Programs\Python\Python313\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\kient\K4-DAY07-LeTrungKien-2A202602748
collected 42 items                                                                                                       

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                              [  2%] 
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                                       [  4%] 
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                                [  7%] 
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                                 [  9%] 
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                                      [ 11%] 
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED                      [ 14%] 
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                            [ 16%] 
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                             [ 19%] 
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                           [ 21%] 
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                             [ 23%] 
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                             [ 26%] 
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                                        [ 28%] 
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                                    [ 30%] 
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                              [ 33%] 
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED                     [ 35%] 
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                         [ 38%] 
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED                   [ 40%] 
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                         [ 42%] 
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                             [ 45%] 
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                               [ 47%] 
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                                 [ 50%] 
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                                       [ 52%] 
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                            [ 54%] 
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                              [ 57%] 
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED                  [ 59%] 
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                               [ 61%] 
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                        [ 64%] 
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                       [ 66%] 
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                                  [ 69%] 
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                              [ 71%] 
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                         [ 73%] 
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                             [ 76%] 
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                                   [ 78%] 
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                             [ 80%] 
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED          [ 83%] 
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                        [ 85%] 
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                       [ 88%] 
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED           [ 90%] 
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED                      [ 92%] 
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED               [ 95%] 
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED     [ 97%] 
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED         [100%] 

================================================== 42 passed in 0.13s ===================================================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Quy trình khiếu nại trả hàng hoàn tiền | Các bước xử lý tranh chấp giữa người mua và bán | cao | -0.1945 | Bất ngờ |
| 2 | Điều kiện yêu cầu trả hàng cho người mua | Chính sách hoàn tiền đối với sản phẩm lỗi | cao | -0.1672 | Bất ngờ |
| 3 | Quy định đăng bán sản phẩm dành cho người bán | Pháo nổ và chất cấm kinh doanh trên sàn | thấp | -0.1988 | Đúng |
| 4 | Các mặt hàng bị cấm quảng cáo | Thông tin gian lận và sử dụng chất kích thích | cao | 0.1611 | Đúng |
| 5 | Tạm khóa tài khoản do vi phạm điều khoản | Quy định về giá bán quá cao hoặc quá thấp | thấp | -0.0498 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Điểm bất ngờ nhất là các cặp câu có ngữ nghĩa tương đồng về mặt con người (như Cặp 1 và Cặp 2) lại có điểm âm (`-0.1945` và `-0.1672`) khi chạy bằng `_mock_embed`. Điều này thể hiện rằng trình nhúng giả lập (`MockEmbedder`) băm chuỗi dựa trên ký tự ngẫu nhiên nên không phản ánh được ngữ nghĩa thực tế; muốn bắt được ngữ nghĩa chính xác cần sử dụng các mô hình học sâu như SentenceTransformer hoặc OpenAI/Gemini.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Thời hạn tối đa để người mua gửi yêu cầu trả hàng và hoàn tiền đối với sản phẩm Shopee Mall là bao lâu? | `## 2. Kiểm tra hàng hoàn về và thời hạn khiếu nại - Khi Người Mua gửi trả hàng t...` | 0.2902 | Có | Trích xuất điều khoản kiểm tra hàng hoàn và thời hạn yêu cầu 15 ngày |
| 2 | Người bán có bao nhiêu thời gian để phản hồi khi người mua yêu cầu trả hàng hoàn tiền? | `Video quay liên tục không ngắt quãng từ lúc kiểm tra tem niêm phong kiện ...` | 0.3333 | Có | Trích xuất quy định phản hồi bằng video bằng chứng trong vòng 48 giờ |
| 3 | Thời gian xử lý bảo hành tiêu chuẩn đối với sản phẩm chính hãng tại Tiki là bao nhiêu ngày? | `Sản phẩm được tiếp nhận bảo hành khi đáp ứng đủ tất cả các điều kiện sau: ...` | 0.3186 | Có | Trích xuất điều kiện tiếp nhận và thời gian xử lý bảo hành 7-14 ngày |
| 4 | Người bán Lazada phải sử dụng thùng carton mấy lớp đối với hàng hóa nặng trên 5 kg hoặc hàng dễ vỡ? | `Nhãn vận chuyển (Shipping Label): Phải in rõ nét mã vạch (barcode) và mã QR...` | 0.3104 | Có | Trích xuất quy chuẩn đóng gói thùng carton 5 lớp đối với hàng dễ vỡ |
| 5 | Mức bồi thường tổn thất tối đa đối với đơn hàng vận chuyển không mua bảo hiểm hàng hóa là bao nhiêu? | `## 4. Phương thức và thời gian hoàn tiền - Hoàn tiền về Ví ShopeePay: Trong vòng...` | 0.2674 | Có | Trích xuất chính sách bồi thường vận chuyển hàng hóa tổn thất |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Việc kết hợp Custom `HeadingChunker` theo tiêu đề điều khoản giúp bảo toàn trọn vẹn bối cảnh của từng chính sách tốt hơn hẳn so với việc gom cố định theo số lượng câu. Ngoài ra, tính năng lọc siêu dữ liệu (`metadata_filter={"audience": "seller"}`) đóng vai trò sống còn để triệt tiêu nhiễu giữa chính sách Người Mua và Người Bán.


---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | / 5 |
| Hướng tiếp cận của tôi (My Approach) | / 10 |
| Hoàn thiện code (Core Implementation — tests) | / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | / 5 |
| Kết quả truy xuất của tôi (Competition Results) | / 10 |
| **Tổng phần cá nhân** | **/ 60** |
