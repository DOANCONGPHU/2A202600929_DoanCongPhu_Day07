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
| 1 | baomatcanhan.md | https://vinfastauto.com/vn_vi/dieu-khoan-phap-ly | 25,816 | category=privacy, chunk_strategy=by_section |
| 2 | chinhsachthuepin.md | https://vinfastauto.com/vn_vi/dieu-khoan-phap-ly | 14,893 | category=battery_rental, chunk_strategy=by_article |
| 3 | dieukiensudung.md | https://vinfastauto.com/vn_vi/dieu-khoan-phap-ly | 5,925 | category=cookies, chunk_strategy=by_section |
| 4 | dieukhoandatcoc.md | https://vinfastauto.com/vn_vi/dieu-khoan-phap-ly | 5,099 | category=deposit, chunk_strategy=by_numbered_clause |
| 5 | dieukhoan.md | https://vinfastauto.com/vn_vi/dieu-khoan-phap-ly | 5,023 | category=terms, chunk_strategy=fixed_size |
| 6 | chinhsachbaomat.md | https://vinfastauto.com/vn_vi/dieu-khoan-phap-ly | 2,908 | category=security, chunk_strategy=fixed_size |
| 7 | chinh_sach_san_pham.md | https://vinfastauto.com/vn_vi/dieu-khoan-phap-ly | 800 | category=product_policy, chunk_strategy=fixed_size |

*Ghi chú: chinh_sach_san_pham.md được merge từ chinhsachdoitra.md (587 ký tự) và chinhsachvanchuyen.md (260 ký tự) vì cả hai quá ngắn để chunk riêng. File duplicate mientrutrachnhiem.md đã bị xóa (nội dung giống hệt dieukhoan.md).*

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| category | string | deposit, privacy, security, battery_rental, cookies, terms, product_policy | Filter trước khi search để tránh retrieve nhầm sang file không liên quan |
| chunk_strategy | string | by_article, by_section, fixed_size | Ghi lại strategy đã dùng để debug và so sánh |
| source | string | https://vinfastauto.com/vn_vi/dieu-khoan-phap-ly | Traceability — biết chunk đến từ nguồn nào |
| language | string | vi | Hữu ích nếu sau này thêm tài liệu tiếng Anh |

---

## 3. Chunking Strategy - Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| baomatcanhan.md | FixedSizeChunker (`fixed_size`) | 52 | 496.5 | Trung bình, dễ cắt ngang câu trong văn bản dài |
| baomatcanhan.md | SentenceChunker (`by_sentences`) | 36 | 714.7 | Tốt, giữ các câu chính sách đầy đủ ý |
| baomatcanhan.md | RecursiveChunker (`recursive`) | 77 | 333.6 | Tốt, chia nhỏ hơn theo đoạn/dòng |
| chinhsachbaomat.md | FixedSizeChunker (`fixed_size`) | 6 | 484.7 | Trung bình, phụ thuộc vị trí cắt ký tự |
| chinhsachbaomat.md | SentenceChunker (`by_sentences`) | 8 | 362.1 | Tốt, mỗi chunk chứa các câu hoàn chỉnh |
| chinhsachbaomat.md | RecursiveChunker (`recursive`) | 10 | 289.2 | Tốt, chunk ngắn và bám cấu trúc văn bản |
| dieukhoandatcoc.md | FixedSizeChunker (`fixed_size`) | 11 | 463.5 | Trung bình, có thể tách rời điều kiện và giải thích |
| dieukhoandatcoc.md | SentenceChunker (`by_sentences`) | 12 | 421.4 | Tốt, giữ nội dung điều khoản theo câu |
| dieukhoandatcoc.md | RecursiveChunker (`recursive`) | 16 | 315.9 | Tốt, phù hợp khi tài liệu có nhiều đoạn |

### Strategy Của Tôi

**Loại:** SentenceChunker

**Mô tả cách hoạt động:**
> Chọn `SentenceChunker`, tức là chia văn bản dựa trên ranh giới câu thay vì cắt theo số ký tự cố định. Trong code, strategy này dùng regex `(?<=[.!?])\s+` để phát hiện điểm kết thúc câu sau các dấu `.`, `!`, `?`, sau đó loại bỏ khoảng trắng thừa bằng `strip()`. Các câu được gom lại theo nhóm, mặc định khoảng 3 câu/chunk, để mỗi chunk vẫn đủ ngữ cảnh nhưng không quá dài. Cách này giúp tránh việc một câu hoặc một ý bị cắt đôi giữa chừng.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Vì các tài liệu nhóm dùng là dạng chính sách bảo mật, bảo mật cá nhân và điều khoản đặt cọc, trong đó mỗi câu thường diễn đạt một quy định, quyền lợi hoặc điều kiện cụ thể. Khi truy vấn trong hệ thống RAG, việc giữ nguyên câu giúp embedding biểu diễn đúng nội dung điều khoản hơn so với cắt ngang theo ký tự. Strategy này phù hợp vì người dùng thường hỏi theo ý nghĩa của một quy định, không chỉ theo từ khóa rời rạc.

**Code snippet (nếu custom):**
```python
# Không dùng custom strategy.
# Strategy của tôi là SentenceChunker đã implement trong src/chunking.py.
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| baomatcanhan.md | FixedSizeChunker baseline | 52 | 496.5 | Khá, nhưng có thể cắt ngang quy định trong văn bản dài |
| baomatcanhan.md | **SentenceChunker của tôi** | 36 | 714.7 | Tốt, ít chunk hơn và giữ câu chính sách đầy đủ |
| chinhsachbaomat.md | FixedSizeChunker baseline | 6 | 484.7 | Trung bình, phụ thuộc vị trí cắt ký tự |
| chinhsachbaomat.md | **SentenceChunker của tôi** | 8 | 362.1 | Tốt, chunk gọn và giữ ý theo câu |
| dieukhoandatcoc.md | FixedSizeChunker baseline | 11 | 463.5 | Khá, nhưng có thể tách điều kiện khỏi phần giải thích |
| dieukhoandatcoc.md | **SentenceChunker của tôi** | 12 | 421.4 | Tốt, phù hợp để truy vấn từng điều khoản |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Vũ Quang Vinh | ArticleChunker | 4 | Giữ nguyên điều khoản, context rất rõ ràng khi LLM đọc | Bị nhiễu ngữ nghĩa (semantic noise) nếu không có metadata filtering hỗ trợ |
| Nguyễn Trần Kiên | FixedSizeChunker (`chunk_size=500`, `overlap=50`) | 8 | Đơn giản, chạy ổn, 4/5 query có relevant chunk trong top-3 | Có thể cắt giữa điều khoản, query thay pin SOH dưới 70% chưa retrieve đúng |
| Đoàn Công Phú | SentenceChunker | 9 | Benchmark thật bằng OpenAI embedding + metadata filter cho thấy top-3 retrieve đúng nguồn ở 5/5 câu hỏi; Q2, Q3, Q4 có câu trả lời đúng ngay TOP 1 | Q1 có chunk trả lời chính xác ở TOP 2 chứ chưa phải TOP 1; Q5 cần ghép nhiều chunk để đủ cả thẻ quốc tế và thẻ nội địa |
| Hoàng Đức Dũng | Strategy 3 (RecursiveChunker) | 2 | Tách đoạn và câu chuẩn, giữ nguyên ý | Chunk size dao động nhiều |
| Đinh Văn Anh Khôi | FixedSize Chunker tuned (300, 100) | 8 | Giảm rách context ở ranh giới tốt nhờ overlap 100; chunk nhỏ cô đọng | Số lượng chunk nhiều (gây tốn token), dễ bị nhiễu do lặp từ |



**Strategy nào tốt nhất cho domain này? Tại sao?**
> Với kết quả hiện có của cả nhóm, `SentenceChunker` là strategy tốt nhất cho domain này vì đạt điểm cao nhất (9/10) và retrieve đúng nguồn trong top-3 ở cả 5 câu benchmark khi dùng metadata filter. `FixedSizeChunker` và bản tuned cũng chạy ổn nhưng vẫn có rủi ro cắt ngang điều khoản hoặc tạo nhiều chunk hơn. `ArticleChunker` và `RecursiveChunker` có lợi thế về cấu trúc, nhưng kết quả benchmark cho thấy cần metadata filter/embedding tốt hơn để tránh retrieve lệch sang tài liệu khác.

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
| 1 | Khách hàng được hoàn lại tiền đặt cọc khi VinFast không bàn giao xe. | Tiền đặt cọc sẽ được trả lại nếu bên bán không ký hợp đồng hoặc không giao xe. | high | 0.6855 | Đúng |
| 2 | Vinfastauto.com không trực tiếp lưu trữ thông tin thẻ thanh toán của khách hàng. | Thông tin thẻ quốc tế được đối tác cổng thanh toán lưu trữ và bảo mật. | high | 0.5273 | Đúng |
| 3 | Khách hàng có quyền yêu cầu thay pin khi dung lượng pin tối đa dưới 70%. | Website sử dụng cookies để cải thiện trải nghiệm người dùng. | low | 0.2725 | Đúng |
| 4 | Sản phẩm VinFast không áp dụng chính sách đổi trả sau khi mua. | Tôi có thể đổi hoặc trả xe sau khi mua không? | high | 0.6218 | Đúng |
| 5 | Xe được phân phối qua hệ thống showroom của đại lý chính hãng. | Dữ liệu cá nhân có thể được mã hóa trong quá trình lưu trữ hoặc chuyển giao. | low | 0.3401 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Pair 2 hơi bất ngờ vì hai câu cùng nói về bảo mật thẻ thanh toán nhưng score chỉ ở mức 0.5273, thấp hơn Pair 1 và Pair 4. Điều này cho thấy embeddings không chỉ nhìn chủ đề chung mà còn bị ảnh hưởng bởi chi tiết diễn đạt: một câu nói "không trực tiếp lưu trữ", câu còn lại nói "đối tác lưu trữ và bảo mật". Vì vậy khi retrieval tài liệu chính sách, chỉ dựa vào một chunk đôi khi chưa đủ; cần top-k context hoặc metadata filter để giữ đủ ý.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | Nếu khách hàng không đến ký hợp đồng mua bán đúng hạn, tiền đặt cọc sẽ được xử lý như thế nào? | Tiền đặt cọc thuộc về VinFast, và VinFast có toàn quyền quyết định việc xử lý khoản tiền đó. |
| 2 | Tôi có thể đổi hoặc trả xe sau khi mua không? | Không. Sản phẩm VinFast không áp dụng chính sách đổi trả. Xe được bảo hành tại hệ thống Showroom và Xưởng dịch vụ của Đại lý phân phối chính hãng theo chính sách bảo hành hiện hành. |
| 3 | VinFast có giao xe trực tiếp đến nhà tôi không? | Không. VinFast không áp dụng chính sách vận chuyển trực tiếp đến khách hàng mua qua vinfastauto.com. Xe được nhận tại hệ thống Showroom của Đại lý phân phối chính hãng trên toàn quốc. |
| 4 | Khách hàng thuê pin VinFast được quyền yêu cầu thay pin khi nào? | Khách hàng có quyền yêu cầu sửa chữa hoặc thay thế pin khi dung lượng pin tối đa (SOH) xuống dưới 70%. Việc thay pin phải được thực hiện tại showroom, xưởng dịch vụ của VinFast Trading hoặc nhà phân phối chính hãng. |
| 5 | Vinfastauto.com có lưu trữ thông tin thẻ ngân hàng của tôi không? | Không. Vinfastauto.com không trực tiếp lưu trữ thông tin thẻ. Đối với thẻ quốc tế, thông tin được Đối Tác Cổng Thanh Toán lưu và bảo mật. Đối với thẻ nội địa, chỉ lưu mã đơn hàng, mã giao dịch và tên ngân hàng. |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Nếu khách hàng không đến ký hợp đồng mua bán đúng hạn, tiền đặt cọc sẽ được xử lý như thế nào? | `dieukhoandatcoc.md`: thời hạn đặt cọc và điều kiện kết thúc thời hạn đặt cọc; chunk trả lời chính xác nằm ở TOP 2 | 0.6753 | Có trong top-3 | Nếu khách hàng không ký hợp đồng/biên bản bàn giao đúng thời gian và địa điểm thông báo, Bên Bán có quyền chấm dứt thỏa thuận, tiền đặt cọc thuộc về VinFast và VinFast quyết định cách xử lý. |
| 2 | Tôi có thể đổi hoặc trả xe sau khi mua không? | `chinh_sach_san_pham.md`: sản phẩm không áp dụng đổi, trả; được bảo hành tại showroom/xưởng dịch vụ chính hãng | 0.6014 | Có | Không được đổi/trả xe sau khi mua; xe được bảo hành theo chính sách bảo hành tại hệ thống showroom và xưởng dịch vụ chính hãng. |
| 3 | VinFast có giao xe trực tiếp đến nhà tôi không? | `chinh_sach_san_pham.md`: sản phẩm phân phối qua showroom; không áp dụng vận chuyển trực tiếp tới khách mua qua website | 0.4924 | Có | VinFast không giao xe trực tiếp đến nhà cho khách mua qua vinfastauto.com; khách nhận xe qua hệ thống showroom đại lý chính hãng. |
| 4 | Khách hàng thuê pin VinFast được quyền yêu cầu thay pin khi nào? | `chinhsachthuepin.md`: khách hàng được sửa chữa/thay pin khi SOH dưới 70%; thực hiện tại điểm cung cấp dịch vụ | 0.6812 | Có | Khách hàng được yêu cầu sửa chữa hoặc thay pin khi dung lượng pin tối đa (SOH) dưới 70%, tại showroom/xưởng dịch vụ VinFast Trading hoặc nhà phân phối chính hãng. |
| 5 | Vinfastauto.com có lưu trữ thông tin thẻ ngân hàng của tôi không? | `chinhsachbaomat.md`: thẻ quốc tế không lưu trên hệ thống Vinfastauto.com; đối tác cổng thanh toán lưu trữ và bảo mật | 0.7624 | Có | Vinfastauto.com không trực tiếp lưu thông tin thẻ; thẻ quốc tế do đối tác cổng thanh toán lưu/bảo mật, thẻ nội địa chỉ lưu mã đơn hàng, mã giao dịch và tên ngân hàng. |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 5 / 5

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> Tôi học được từ các thành viên khác rằng chunking không có một strategy luôn tốt cho mọi tài liệu. `ArticleChunker` giữ cấu trúc điều khoản rất rõ khi tài liệu có đánh số điều/mục, còn `FixedSizeChunker` tuned với overlap lớn giúp giảm rủi ro mất context ở ranh giới chunk. Tuy nhiên kết quả benchmark cũng cho thấy strategy tốt vẫn cần metadata filter và embedding phù hợp.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> Tôi học được rằng việc thiết kế benchmark quan trọng không kém việc viết code. Một bộ benchmark tốt cần có query đa dạng, gold answer rõ ràng, expected source và cả các câu hỏi dễ retrieve nhầm để kiểm tra độ ổn định của hệ thống. Ngoài ra, không nên để file benchmark nằm trong corpus retrieval vì sẽ làm kết quả bị lộ đáp án.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> Nếu làm lại, tôi sẽ gắn metadata `category` ngay từ đầu cho mọi chunk và dùng `search_with_filter` trong agent thay vì chỉ dùng search toàn cục. Tôi cũng sẽ tách riêng file benchmark khỏi thư mục tài liệu nguồn để tránh retrieve nhầm vào đáp án. Với các tài liệu dài như `baomatcanhan.md`, tôi sẽ thử hybrid strategy: tách theo section trước, sau đó tách câu bên trong từng section để vừa giữ cấu trúc vừa tránh chunk quá dài.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 10 / 10 |
| Chunking strategy | Nhóm | 15 / 15 |
| My approach | Cá nhân | 10 / 10 |
| Similarity predictions | Cá nhân | 5 / 5 |
| Results | Cá nhân | 9 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | 5 / 5 |
| **Tổng** | | **89 / 90** |
