# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Đoàn Công Phú

**Nhóm:** VanFist
**Ngày:** 05/06/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> *High cosine similarity là một chỉ số toán học dùng để đo lường mức độ giống nhau về ý nghĩa giữa hai đoạn văn bản, hình ảnh hoặc dữ liệu bất kỳ đã được chuyển đổi thành vector High similarity nghĩa là hai văn bản có ý nghĩa gần nhau.*

**Ví dụ HIGH similarity:**
- Sentence A: Tôi muốn đặt vé máy bay đi Hà Nội
- Sentence B: Làm sao để mua vé bay tới Hà Nội?
- Tại sao tương đồng: Hai câu dùng từ khác nhau, nhưng ý nghĩa gần giống nhau → cosine similarity cao.

**Ví dụ LOW similarity:**
- Sentence A: Tôi muốn đặt xe bus đi Hải Phòng
- Sentence B: Cách làm bánh đậu xanh tại nhà?
- Tại sao khác: Hai câu nói về hai chủ đề khác nhau → cosine similarity thấp.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> *Cosine similarity tốt hơn Euclidean distance cho text embedding vì nó so sánh hướng giữa hai vector, do đó bỏ qua độ dài/scale của văn bản và phản ánh tốt hơn tương đồng ngữ nghĩa trong không gian nhiều chiều; Euclidean phù hợp khi bạn cần đo khoảng cách tuyệt đối*

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
```
step = chunk_size - overlap = 500 - 50 = 450
N = ceil((10000 - 500) / 450) + 1
N = ceil(9500 / 450) + 1
N = ceil(21.11) + 1
N = 22 + 1
N = 23 chunks
```
> *Đáp án: 23 chunks*

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
```
Số chunk = [(10,000−100)/400]=24.75
```
> *Overlap lớn hơn → bước nhảy nhỏ hơn → số chunk nhiều hơn.Overlap giúp chunk không bị mất nghĩa ở đoạn giao nhau,overlap quá lớn sẽ tạo nhiều chunk hơn, tốn chi phí embedding và truy xuất hơn.*

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Policy Vinfast

**Tại sao nhóm chọn domain này?**
> *Domain chính sách pháp lý/thương mại điện tử có cấu trúc rõ ràng (điều khoản, khoản mục đánh số) và ngôn ngữ đặc thù, phù hợp để thử nghiệm các chunking strategy khác nhau. Bộ tài liệu đa dạng về độ dài (từ 260 đến 34,500 ký tự) giúp so sánh strategy rõ nét hơn. Đây cũng là use case thực tế: khách hàng thường tra cứu chính sách bảo hành, đặt cọc, hoàn tiền trước khi mua xe.*

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | baomatcanhan.md | https://vinfastauto.com/vn_vi/dieu-khoan-phap-ly | 34,505 | category=privacy, chunk_strategy=by_section |
| 2 | chinhsachthuepin.md | https://vinfastauto.com/vn_vi/dieu-khoan-phap-ly | 19,422 | category=battery_rental, chunk_strategy=by_article |
| 3 | dieukiensudung.md | https://vinfastauto.com/vn_vi/dieu-khoan-phap-ly | 7,284 | category=cookies, chunk_strategy=by_section |
| 4 | dieukhoandatcoc.md | https://vinfastauto.com/vn_vi/dieu-khoan-phap-ly | 6,626 | category=deposit, chunk_strategy=by_numbered_clause |
| 5 | dieukhoan.md | https://vinfastauto.com/vn_vi/dieu-khoan-phap-ly | 6,419 | category=terms, chunk_strategy=fixed_size |
| 6 | chinhsachbaomat.md | https://vinfastauto.com/vn_vi/dieu-khoan-phap-ly | 3,551 | category=security, chunk_strategy=fixed_size |
| 7 | chinh_sach_san_pham.md | https://vinfastauto.com/vn_vi/dieu-khoan-phap-ly | ~850 | category=product_policy, chunk_strategy=fixed_size |

*Ghi chú: chinh_sach_san_pham.md được merge từ chinhsachdoitra.md (587 ký tự) và chinhsachvanchuyen.md (260 ký tự) vì cả hai quá ngắn để chunk riêng. File duplicate mientrutrachnhiem.md đã bị xóa (nội dung giống hệt dieukhoan.md).*

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| category | string | deposit, privacy, security, battery_rental, cookies, terms, product_policy | Filter trước khi search để tránh retrieve nhầm sang file không liên quan |
| chunk_strategy | string | by_article, by_section, fixed_size | Ghi lại strategy đã dùng để debug và so sánh |
| source | string | https://vinfastauto.com/vn_vi/dieu-khoan-phap-ly | Traceability — biết chunk đến từ nguồn nào |
| language | string | vi | Hữu ích nếu sau này thêm tài liệu tiếng Anh |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| | FixedSizeChunker (`fixed_size`) | | | |
| | SentenceChunker (`by_sentences`) | | | |
| | RecursiveChunker (`recursive`) | | | |

### Strategy Của Tôi

**Loại:** [FixedSizeChunker / SentenceChunker / RecursiveChunker / custom strategy]

**Mô tả cách hoạt động:**
> *Viết 3-4 câu: strategy chunk thế nào? Dựa trên dấu hiệu gì?*

**Tại sao tôi chọn strategy này cho domain nhóm?**
> *Viết 2-3 câu: domain có pattern gì mà strategy khai thác?*

**Code snippet (nếu custom):**
```python
# Paste implementation here
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| | best baseline | | | |
| | **của tôi** | | | |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi | | | | |
| [Tên] | | | | |
| [Tên] | | | | |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> *Viết 2-3 câu:*

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> *Dùng regex `(?<=[.!?])\s+` để tách văn bản thành các câu dựa trên dấu kết thúc câu như `.`, `!`, `?` và khoảng trắng phía sau. Sau khi tách, dùng `strip()` để loại bỏ khoảng trắng thừa và bỏ qua các câu rỗng. Tiếp theo, gom các câu theo `max_sentences_per_chunk` để mỗi chunk chứa tối đa số câu đã cấu hình.*

**`RecursiveChunker.chunk` / `_split`** — approach:
> *Triển khai thuật toán chia đệ quy theo danh sách separator ưu tiên: `\n\n`, `\n`, `. `, khoảng trắng, rồi cuối cùng là chuỗi rỗng. Base case là nếu đoạn text hiện tại có độ dài nhỏ hơn hoặc bằng `chunk_size` thì trả về ngay đoạn đó. Nếu đoạn vẫn quá dài, hàm `_split` thử separator tiếp theo; nếu không còn separator phù hợp thì fallback sang cắt theo kích thước cố định để đảm bảo chunk không quá lớn.*

### EmbeddingStore

**`add_documents` + `search`** — approach:
> *Trong `add_documents`, mỗi `Document` được chuyển thành một record gồm `id`, `content`, `metadata`, và `embedding`. Metadata luôn được bổ sung thêm `doc_id` để dễ filter hoặc delete theo tài liệu gốc. Khi search, embed query rồi tính điểm similarity bằng dot product giữa query embedding và document embedding, sau đó sắp xếp giảm dần theo score và trả về `top_k` kết quả tốt nhất*

**`search_with_filter` + `delete_document`** — approach:
> *Với `search_with_filter`, filter metadata trước rồi mới chạy similarity search trên tập record đã lọc, vì cách này đảm bảo kết quả trả về đúng phạm vi người dùng yêu cầu. Nếu không có filter thì hàm gọi lại `search` bình thường. Với `delete_document`, tìm tất cả record có `metadata["doc_id"] == doc_id`, xóa chúng khỏi store, và trả về `True` nếu có tài liệu bị xóa, ngược lại trả về `False`.*

### KnowledgeBaseAgent

**`answer`** — approach:
> *Trong `answer`, agent nhận câu hỏi rồi gọi `store.search(question, top_k)` để lấy các chunk liên quan nhất. Các chunk này được ghép vào phần `Context` của prompt theo dạng đánh số `[1]`, `[2]`, `[3]` để LLM có ngữ cảnh rõ ràng trước khi trả lời. Prompt gồm ba phần chính: hướng dẫn trả lời dựa trên context, context đã retrieve, và câu hỏi của người dùng.*

### Test Results

```
======================================= test session starts ========================================
platform win32 -- Python 3.12.10, pytest-9.0.3, pluggy-1.6.0 -- D:\AI_TC\day07_DoanCongPhu_2A202600929\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\AI_TC\day07_DoanCongPhu_2A202600929
collected 42 items                                                                                  

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED         [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                  [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED           [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED            [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                 [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED       [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED        [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED      [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                        [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED        [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                   [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED               [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                         [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED    [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED    [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                        [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED          [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED            [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                  [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED       [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED         [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED          [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                   [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                  [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED             [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED         [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED    [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED        [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED              [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED        [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED   [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED  [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

======================================== 42 passed in 0.10s ========================================
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | | | high / low | | |
| 2 | | | high / low | | |
| 3 | | | high / low | | |
| 4 | | | high / low | | |
| 5 | | | high / low | | |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> *Viết 2-3 câu:*

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Bao nhiêu queries trả về chunk relevant trong top-3?** __ / 5

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> *Viết 2-3 câu:*

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> *Viết 2-3 câu:*

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | / 5 |
| Document selection | Nhóm | / 10 |
| Chunking strategy | Nhóm | / 15 |
| My approach | Cá nhân | / 10 |
| Similarity predictions | Cá nhân | / 5 |
| Results | Cá nhân | / 10 |
| Core implementation (tests) | Cá nhân | / 30 |
| Demo | Nhóm | / 5 |
| **Tổng** | | **/ 100** |
