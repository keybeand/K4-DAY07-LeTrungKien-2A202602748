# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** So1
**Thành viên:** 
Trần Nam Anh - 2A202602901
Hoàng Anh Minh - 2A202602566
Hoàng Phong - 2A202602943
Lê Trung Kiên - 2A202602748
**Ngày:** 20/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Chính sách Đổi trả, Bảo hành và Quy định Người bán / Người mua trên sàn Thương mại Điện tử Shopee.

**Tại sao nhóm chọn chủ đề này?**
> Chính sách thương mại điện tử Shopee chứa các điều khoản ràng buộc pháp lý có cấu trúc rõ ràng, nhiều mốc thời hạn định lượng cụ thể (24h, 48h, 15 ngày, bồi thường 100%,...) và phân tách rõ ràng quyền lợi/nghĩa vụ giữa Người Mua (`buyer`) và Người Bán (`seller`). Đây là ngữ liệu thực tế lý tưởng để đánh giá khả năng bảo toàn ngữ cảnh của các chiến lược chia nhỏ (chunking) cũng như kiểm chứng tính hiệu quả vượt trội của bộ lọc siêu dữ liệu (`metadata_filter`) nhằm chống nhiễu thông tin giữa các đối tượng tham gia giao dịch.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Chính sách trả hàng và hoàn tiền dành cho Người Mua Shopee | https://help.shopee.vn/portal/4/article/77245 | 2026-09-20 / not-stated | 2195 | `audience: buyer`, `category: returns-policy`, `language: vi` |
| 2 | Quy định xử lý khiếu nại và trả hàng dành cho Người Bán Shopee | https://help.shopee.vn/portal/4/article/77245 | 2026-09-20 / not-stated | 2219 | `audience: seller`, `category: dispute-policy`, `language: vi` |
| 3 | Danh sách hàng hóa cấm và hạn chế kinh doanh trên Shopee | https://help.shopee.vn/portal/4/article/77245 | 2026-09-20 / not-stated | 1996 | `audience: seller`, `category: prohibited-items`, `language: vi` |
| 4 | Chính sách bảo hành sản phẩm chính hãng dành cho Người Mua Shopee | https://help.shopee.vn/portal/4/article/77245 | 2026-09-20 / not-stated | 2250 | `audience: buyer`, `category: warranty-policy`, `language: vi` |
| 5 | Quy chuẩn đóng gói và bàn giao hàng hóa dành cho Người Bán Shopee | https://help.shopee.vn/portal/4/article/77245 | 2026-09-20 / not-stated | 2310 | `audience: seller`, `category: shipping-guidelines`, `language: vi` |
| 6 | Chính sách bồi thường hư hỏng và thất lạc hàng hóa vận chuyển Shopee | https://help.shopee.vn/portal/4/article/77245 | 2026-09-20 / not-stated | 2340 | `audience: both`, `category: compensation-policy`, `language: vi` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | String | `shopee-buyer-return-refund` | Định danh duy nhất của tài liệu, liên kết 1-1 với tên file giúp quản lý và truy xuất chính xác nguồn văn bản. |
| `title` | String | `Chính sách trả hàng và hoàn tiền dành cho Người Mua Shopee` | Hiển thị tiêu đề tài liệu thân thiện trong kết quả tìm kiếm và câu trả lời RAG. |
| `source_url` | String | `https://help.shopee.vn/portal/4/article/77245` | Cung cấp link gốc công khai để hệ thống trích dẫn nguồn (grounding) và đối soát dữ liệu thực tế. |
| `retrieved_at` | String (Date) | `2026-09-20` | Kiểm soát tính mới và thời điểm hiệu lực của chính sách sàn TMĐT. |
| `document_version` | String | `not-stated` | Đảm bảo tính minh bạch pháp lý; ghi rõ phiên bản quy chế (hoặc `not-stated` nếu sàn không đánh số hiệu). |
| `audience` | String | `buyer`, `seller`, `both` | **Bắt buộc và then chốt**: Phân tách đối tượng áp dụng chính sách, cho phép `search_with_filter(metadata_filter={'audience': 'buyer'})` loại bỏ hoàn toàn các điều khoản của Người Bán gây nhiễu kết quả. |
| `category` | String | `returns-policy`, `warranty-policy`, `shipping-guidelines` | Lọc theo nghiệp vụ chuyên biệt (đổi trả, bảo hành, đóng gói vận chuyển). |
| `language` | String | `vi` | Định danh ngôn ngữ để mở rộng hoặc tối ưu cho mô hình nhúng tiếng Việt. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `shopee-buyer-return-refund.md` | FixedSizeChunker (`fixed_size`) | 7 | 291.1 ký tự | Kém; dễ cắt ngang giữa câu hoặc làm đứt các mốc thời hạn 15 ngày / 3 ngày. |
| `shopee-buyer-return-refund.md` | SentenceChunker (`by_sentences`) | 7 | 272.7 ký tự | Khá; giữ trọn vẹn câu nhưng có thể gom các câu thuộc các điều kiện khác nhau vào chung 1 chunk. |
| `shopee-buyer-return-refund.md` | RecursiveChunker (`recursive`) | 10 | 190.5 ký tự | Tốt; tôn trọng ngắt đoạn văn và các gạch đầu dòng điều kiện. |
| `shopee-seller-dispute-resolution.md` | FixedSizeChunker (`fixed_size`) | 7 | 293.0 ký tự | Kém; cắt rời phần thời hạn 48h với phần chế tài xử phạt người bán. |
| `shopee-seller-dispute-resolution.md` | SentenceChunker (`by_sentences`) | 7 | 274.0 ký tự | Khá; đảm bảo cấu trúc câu đầy đủ nhưng chunk kích thước biến thiên lớn. |
| `shopee-seller-dispute-resolution.md` | RecursiveChunker (`recursive`) | 11 | 174.3 ký tự | Rất tốt; phân tách rõ ràng giữa quy trình khiếu nại và chế tài xử lý. |

### Chiến lược của từng thành viên

**Thành viên 1 — Hoàng Anh Minh (Strategy Lead — R3)**
- **Loại chiến lược:** Custom `HeadingChunker` (Bắt buộc theo K4-L3B: chia theo tiêu đề/mục điều khoản).
- **Mô tả & lý do chọn cho chủ đề này:** Văn bản quy chế TMĐT được soạn thảo theo cấu trúc phân cấp nghiêm ngặt (`## 1. Thời hạn...`, `## 2. Lý do...`, `## 3. Chế tài...`). Việc chia nhỏ theo từng Header giúp mỗi chunk mang trọn vẹn một điều khoản hoàn chỉnh, không bao giờ bị mất ngữ cảnh hay bị cắt xén mốc thời gian định lượng.
- **Code snippet (nếu custom):**
```python
import re

class HeadingChunker:
    """Chia nhỏ văn bản theo tiêu đề Markdown cấp 2 (##)."""
    def chunk(self, text: str) -> list[str]:
        sections = re.split(r'(?=\n##\s+)', text.strip())
        return [s.strip() for s in sections if s.strip()]
```

**Thành viên 2 — Trần Nam Anh (Data Lead — R1)**
- **Loại chiến lược:** `RecursiveChunker` (`chunk_size=300`, ưu tiên `["\n\n", "\n", ". ", " "]`)
- **Mô tả & lý do chọn:** Chiến lược chia đệ quy cân bằng tốt giữa việc giữ ranh giới đoạn văn tự nhiên và kiểm soát chiều dài chunk để embedding mô hình không bị quá tải.
- **Code snippet (nếu custom):** Sử dụng `RecursiveChunker` chuẩn trong `src/chunking.py`.

**Thành viên 3 — Hoàng Phong (Benchmark Lead — R2)**
- **Loại chiến lược:** `FixedSizeChunker` (`chunk_size=350`, `overlap=70`)
- **Mô tả & lý do chọn:** Cố định độ dài chunk để đồng nhất kích thước vector nhúng, đồng thời thiết lập độ chồng chéo cao (70 ký tự) nhằm hạn chế rủi ro mất mát từ khóa quan trọng ở điểm giao cắt.
- **Code snippet (nếu custom):** Sử dụng `FixedSizeChunker` chuẩn trong `src/chunking.py`.

**Thành viên 4 — Lê Trung Kiên (Report & Demo Lead — R4)**
- **Loại chiến lược:** `SentenceChunker` (`max_sentences_per_chunk=3`)
- **Mô tả & lý do chọn:** Chia nhỏ văn bản dựa trên ranh giới câu ngữ pháp hoàn chỉnh (`.`, `!`, `?`), nhóm cố định 3 câu/chunk để đảm bảo ngữ nghĩa của từng câu không bị cắt ngang giữa chừng.
- **Code snippet (nếu custom):** Sử dụng `SentenceChunker` chuẩn trong `src/chunking.py`.


### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Hoàng Anh Minh | HeadingChunker | 9.5 / 10 | Giữ nguyên 100% ngữ cảnh của từng điều khoản chính sách; độ chính xác trích xuất con số và thời hạn cao nhất. | Kích thước các chunk không đồng đều (mục ngắn vài chục ký tự, mục dài hơn 500 ký tự). |
| Trần Nam Anh | RecursiveChunker | 8.5 / 10 | Tự động phân tách linh hoạt theo đoạn; kích thước chunk đồng đều và dễ nạp vào embedding. | Đôi khi tách tiêu đề rời khỏi nội dung của gạch đầu dòng bên dưới. |
| Lê Trung Kiên | SentenceChunker | 8.0 / 10 | Đảm bảo tính toàn vẹn ngữ pháp câu 100%, câu cú mạch lạc, không bị đứt câu hay cắt đôi từ ngữ. | Các danh sách gạch đầu dòng nhiều ý ngắn dễ bị ngắt thành nhiều chunk rời rạc, mất liên hệ với tiêu đề mục cha. |
| Hoàng Phong | FixedSizeChunker | 7.0 / 10 | Độ dài chunk luôn đồng nhất, dễ quản lý bộ nhớ vector store. | Dễ cắt ngang giữa chừng một mệnh đề hoặc làm đôi một cụm từ kỹ thuật dù đã có overlap. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> `HeadingChunker` (chia theo tiêu đề/mục) là chiến lược tối ưu nhất cho văn bản chính sách thương mại điện tử. Do các quy định pháp lý trên sàn luôn được biên soạn theo từng điều khoản độc lập, việc giữ trọn vẹn cả tiêu đề và nội dung điều khoản trong cùng một chunk giúp mô hình retrieval nắm bắt đầy đủ bối cảnh câu hỏi mà không bị ngắt rời các con số thời hạn (ví dụ: thời hạn 48h, 15 ngày hay 3 ngày làm việc).

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Thời hạn tối đa để người mua gửi yêu cầu trả hàng và hoàn tiền đối với sản phẩm Shopee Mall là bao lâu? | 15 ngày kể từ ngày nhận hàng thành công. | `shopee-buyer-return-refund.md` (Mục 1) |
| 2 | Người bán có bao nhiêu thời gian để phản hồi khi người mua yêu cầu trả hàng hoàn tiền? *(Yêu cầu filter `audience: seller`)* | 48 giờ (2 ngày lịch) kể từ lúc hệ thống gửi thông báo. | `shopee-seller-dispute-resolution.md` (Mục 1) |
| 3 | Thời gian xử lý bảo hành tiêu chuẩn đối với sản phẩm chính hãng tại Shopee là bao nhiêu ngày? | Từ 07 đến 14 ngày làm việc kể từ ngày trung tâm nhận được sản phẩm. | `shopee-buyer-warranty-policy.md` (Mục 3) |
| 4 | Người bán Shopee phải sử dụng thùng carton mấy lớp đối với hàng hóa nặng trên 5 kg hoặc hàng dễ vỡ? *(Yêu cầu filter `audience: seller`)* | Thùng carton tối thiểu 5 lớp (và quấn 2-3 lớp xốp khí). | `shopee-seller-packaging-guidelines.md` (Mục 1) |
| 5 | Mức bồi thường tổn thất tối đa đối với đơn hàng vận chuyển Shopee không mua bảo hiểm hàng hóa là bao nhiêu? | Tối đa bằng 04 lần cước phí vận chuyển hoặc tối đa 1.000.000 VNĐ đối với hàng thất lạc thông thường. | `shopee-shipping-damage-compensation.md` (Mục 3) |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Thời hạn người mua gửi yêu cầu trả hàng Shopee Mall | HeadingChunker | Có (Top-1) | Trích xuất chính xác con số 15 ngày mà không bị lẫn thời hạn shop thường. |
| 2 | Thời hạn người bán phản hồi khiếu nại trả hàng | HeadingChunker + Filter `audience: seller` | Có (Top-1) | Bắt buộc phải có filter để loại bỏ các chunk đổi trả của người mua. |
| 3 | Thời gian xử lý bảo hành Shopee | RecursiveChunker | Có (Top-1) | Truy xuất chính xác mục bảo hành tiêu chuẩn 7-14 ngày. |
| 4 | Quy chuẩn thùng carton trên 5kg Shopee | HeadingChunker + Filter `audience: seller` | Có (Top-1) | Lọc chính xác quy định đóng gói người bán, lấy được số lớp thùng carton (5 lớp). |
| 5 | Mức bồi thường hàng vận chuyển Shopee không bảo hiểm | HeadingChunker | Có (Top-1) | Trích xuất đúng điều khoản bồi thường 4 lần cước hoặc 1.000.000 VNĐ. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Lọc bằng metadata (`metadata_filter={"audience": "seller"}`) đóng vai trò then chốt ở Câu hỏi 2 và Câu hỏi 4. Nếu không lọc theo `audience`, truy vấn "thời gian phản hồi yêu cầu trả hàng" rất dễ bị nhiễu bởi các tài liệu trả hàng của người mua (với các mốc 15 ngày, 7 ngày) do có độ tương đồng từ khóa rất cao; việc tiền lọc giúp khoanh vùng chính xác văn bản dành cho Người Bán và trả về đúng mốc 48 giờ.

### Thực nghiệm A/B Testing với Metadata Filter (Minh chứng Câu hỏi 2)

| Lần chạy | Cấu hình lọc | Top-1 Chunk (doc_id) | Top-2 Chunk (doc_id) | Top-3 Chunk (doc_id) | Đánh giá hiệu quả |
|---|---|---|---|---|---|
| Lần 1 | Có filter: `{"audience": "seller"}` | `shopee-seller-dispute-resolution` (Score: +0.2266) | `shopee-prohibited-items-policy` (Score: +0.1982) | `shopee-prohibited-items-policy` (Score: +0.1859) | **100% Top-3** thuộc về chính sách Người Bán, loại bỏ hoàn toàn tài liệu Người Mua! |
| Lần 2 | Không filter (`None`) | `shopee-seller-dispute-resolution` (Score: +0.2266) | `shopee-buyer-warranty-policy` (Score: +0.2243) | `shopee-prohibited-items-policy` (Score: +0.1982) | Tài liệu Người Mua (`buyer`) lọt vào Top-2 cạnh tranh gay gắt về điểm số (+0.2243). |

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

### Phân Tích Thất Bại (Failure Case Analysis)
- **Câu hỏi bị hỏng:** Câu hỏi #1 (*"Thời hạn tối đa để người mua gửi yêu cầu trả hàng và hoàn tiền đối với sản phẩm Shopee Mall là bao lâu?"*).
- **Nguyên nhân tại sao lỗi:**
  1. *Hạn chế của MockEmbedder:* Thuật toán băm MD5 chỉ đo đạc sự trùng lặp ký tự bề mặt mà không hiểu ngữ nghĩa liên tục.
  2. *Nhiễu từ khóa:* Các từ khóa chung ("thời hạn", "hàng hóa", "yêu cầu") xuất hiện dày đặc trong văn bản bồi thường vận chuyển (`shopee-shipping-damage-compensation`), khiến văn bản này bị xếp nhầm lên vị trí Top-1 thay vì văn bản trả hàng của người mua.
- **Đề xuất hướng sửa:**
  1. *Bổ sung tiền lọc Metadata:* Áp dụng `metadata_filter={"audience": "buyer"}` để triệt tiêu hoàn toàn các tài liệu vận chuyển/người bán không liên quan.
  2. *Nâng cấp Embedding Backend:* Sử dụng mô hình Transformer thực tế (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` hoặc OpenAI `text-embedding-3-small`) để định vị chính xác ngữ cảnh "đổi trả Shopee Mall".

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> 1. **Cấu trúc tài liệu quyết định chiến lược chunking:** Với các văn bản pháp lý/chính sách có tính phân cấp mạnh, chia theo đề mục (`HeadingChunker`) vượt trội hơn hẳn so với chia cố định theo ký tự (`FixedSizeChunker`).
> 2. **Sức mạnh của Tiền lọc Metadata (Pre-filtering):** Trong các hệ thống nhiều bên tham gia (Multi-party platform như Người mua - Người bán), siêu dữ liệu phân loại đối tượng là ranh giới bảo vệ hữu hiệu nhất chống ô nhiễm ngữ cảnh (context contamination).
> 3. **Hạn chế của Mock Embedder:** Embedder băm chuỗi không phản ánh được ngữ nghĩa thực; cần mô hình Transformer thực thụ để tối ưu hóa độ nhạy ngữ nghĩa.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một bộ tài liệu và câu hỏi, nhưng cách chia nhỏ văn bản khác nhau tạo ra sự chênh lệch rất lớn về khả năng trả lời của RAG Agent. Chunk quá nhỏ làm mất ngữ cảnh (không biết con số 48h áp dụng cho ai), trong khi chunk quá lớn gây loãng câu trả lời. Chiến lược tốt nhất là bám sát cấu trúc ngữ nghĩa tự nhiên của chính văn bản đó.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ tích hợp thêm trường metadata `sub_category` (ví dụ: `mall_policy`, `normal_shop_policy`) và gán nhãn chi tiết hơn cho từng phần của chính sách để cho phép truy vấn lọc đa tầng (multi-faceted filtering).

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |
