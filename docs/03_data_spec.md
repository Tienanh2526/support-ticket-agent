# 03 — Đặc tả dữ liệu

> File này định nghĩa mọi dữ liệu project dùng: ticket, taxonomy (bộ nhãn), knowledge base, đơn hàng giả, gold set, và các schema Pydantic sẽ viết. Khi gán nhãn hoặc viết schema, file này là "luật".

**Toàn bộ dữ liệu là tổng hợp (synthetic). Không bao giờ commit dữ liệu khách hàng thật.**

## 1. Bản đồ dữ liệu

| Đường dẫn | Nội dung | Ai đọc | Trạng thái |
|---|---|---|---|
| `data/raw/sample_tickets_synthetic.csv` | 8 ticket mẫu | API validate, test, demo | ✅ |
| `data/kb/*.md` | 4 bài knowledge base | Tool `search_kb`, `get_kb_passage`; validator | ✅ |
| `data/mock/orders.csv` | 5 đơn hàng giả | Tool `get_order_status` | ✅ |
| `data/eval/gold_tickets.csv` | Gold set đã gán nhãn | Eval runner | Sprint 2 |
| `data/processed/` | File sinh ra khi chạy (không commit) | – | – |

## 2. Ticket CSV

| Trường | Kiểu | Bắt buộc | Mô tả | Ví dụ |
|---|---|:---:|---|---|
| `ticket_id` | string | ✔ | Duy nhất trong file | `tk_001` |
| `body` | string | ✔ | Nội dung gốc của khách, giữ nguyên | `Mình đặt đơn ORD1001...` |
| `subject` | string | | Tiêu đề | `Đơn hàng chưa tới` |
| `created_at` | ISO 8601 | | Thời điểm tạo. Sai định dạng → báo lỗi, không đoán | `2026-10-01T09:12:00` |
| `channel` | string | | `email`, `chat` | `chat` |
| `language` | string | | `vi`, `en`. Trống → để bước phân loại tự nhận diện | `vi` |
| `order_id` | string | | Mã đơn, dùng cho `get_order_status` | `ORD1001` |
| `customer_id` | string | | Chỉ dùng ID ẩn danh, không dùng tên/SĐT/email | `cus_042` |

Lưu ý:
- Khách có thể ghi mã đơn trong `body` mà không điền `order_id`. Agent được phép lấy mã từ `body`, nhưng phải gọi tool để kiểm tra, không tin ngay.
- `created_at` quan trọng để tính "đơn có trễ không" và "còn trong hạn đổi trả không". Thiếu `created_at` thì agent không được kết luận về thời hạn.

## 3. Taxonomy v0.1

Định nghĩa trong `src/schemas/ticket.py` dưới dạng `StrEnum`, kèm `TAXONOMY_VERSION = "0.1"`. **Đổi bất kỳ nhãn nào → tăng version**, để không so sánh nhầm kết quả eval của hai bộ nhãn khác nhau.

### 3.1 Category (loại vấn đề) — chọn đúng 1

| Nhãn | Định nghĩa | Ví dụ | Dễ nhầm với |
|---|---|---|---|
| `order_status` | Hỏi đơn đang ở đâu, đã gửi chưa, khi nào tới (chưa có sự cố giao hàng cụ thể) | "Đơn ORD1001 đang ở đâu?" | `shipping_delivery` |
| `shipping_delivery` | Sự cố giao hàng: giao sai địa chỉ, shipper không gọi, phí ship, đổi địa chỉ, hỏi thời gian giao chung | "Shipper báo giao rồi mà tôi không nhận được" | `order_status` |
| `refund_return` | Muốn đổi, trả hàng, hoàn tiền, hỏi chính sách đổi trả | "Giày sai size, trả hàng thế nào?" | `product_issue` |
| `payment_billing` | Trừ tiền sai, trừ 2 lần, thanh toán lỗi, hoá đơn | "Thẻ bị trừ tiền 2 lần" | `refund_return` |
| `product_issue` | Sản phẩm lỗi, hỏng, khác mô tả, hỏi cách dùng | "Tai nghe bị rè một bên" | `refund_return` |
| `account_access` | Đăng nhập, mật khẩu, OTP, khoá tài khoản, nghi bị chiếm tài khoản | "Quên mật khẩu không nhận được email" | – |
| `promotion_voucher` | Mã giảm giá, khuyến mãi, điểm thưởng | "Mã WELCOME10 báo không hợp lệ" | `payment_billing` |
| `other` | Không thuộc loại nào ở trên: giờ làm việc, góp ý chung, spam | "Shop có làm cuối tuần không?" | – |

**Luật phân xử khi ticket có nhiều vấn đề:**
1. Chọn vấn đề **khách muốn được giải quyết** (mục đích), không phải bối cảnh. "Sản phẩm lỗi, tôi muốn đổi" → mục đích là đổi do lỗi → `product_issue`. "Giày sai size, muốn trả" → `refund_return` (không phải lỗi sản phẩm).
2. Nếu vẫn còn hai vấn đề ngang nhau, chọn vấn đề **rủi ro cao hơn** theo thứ tự: `payment_billing` > `account_access` > `product_issue` > `refund_return` > `shipping_delivery` > `order_status` > `promotion_voucher` > `other`.
3. `other` chỉ dùng khi thật sự không khớp loại nào, không dùng để "né" ca khó.

### 3.2 Priority (mức ưu tiên)

| Nhãn | Khi nào | Ví dụ |
|---|---|---|
| `urgent` | Bị trừ tiền sai/trừ 2 lần; nghi bị chiếm tài khoản hoặc lộ thông tin; dọa kiện, dọa báo chí/cơ quan chức năng | `tk_004` trừ tiền 2 lần |
| `high` | Đơn trễ quá ngày dự kiến; sản phẩm lỗi/hỏng; ticket có dấu hiệu prompt injection hoặc lừa đảo; khách rất bức xúc | `tk_006` tai nghe rè, `tk_007` |
| `medium` | Yêu cầu đổi trả/hoàn tiền thông thường; lỗi voucher; không đăng nhập được (không có dấu hiệu bị chiếm) | `tk_002`, `tk_003`, `tk_005` |
| `low` | Câu hỏi chung; hỏi tình trạng đơn **chưa** trễ | `tk_001`, `tk_008` |

"Trễ" được tính bằng cách so `created_at` của ticket với `estimated_delivery` từ tool. Không có dữ liệu thì không kết luận trễ.

### 3.3 Sentiment (cảm xúc khách)

| Nhãn | Khi nào |
|---|---|
| `positive` | Khen, cảm ơn |
| `neutral` | Hỏi thông tin, không bày tỏ cảm xúc |
| `negative` | Khó chịu, phàn nàn, thúc giục ("gấp", "!!!") |
| `mixed` | Vừa khen vừa chê |
| `unclear` | Quá ngắn hoặc không đủ để đoán |

Sentiment **không** quyết định escalate một mình; nó giúp nhân viên chọn giọng văn và có thể nâng priority khi khách rất bức xúc.

### 3.4 Action

| Nhãn | Nghĩa |
|---|---|
| `draft_reply` | Agent soạn nháp, nháp đã qua validate |
| `escalate` | Chuyển người thật, kèm `reason_code` (danh sách ở `04_agent_design.md` mục 4) |

## 4. Knowledge base (`data/kb/*.md`)

### 4.1 Hiện có

| File | Chủ đề | Số đoạn |
|---|---|---:|
| `account_help.md` | Mật khẩu, email đặt lại, OTP | 4 |
| `payment_promotion.md` | Trừ tiền 2 lần, WELCOME10, giờ làm việc | 4 |
| `refund_return_policy.md` | Thời hạn đổi trả, phí ship, thời gian hoàn tiền | 6 |
| `shipping_policy.md` | Thời gian giao, tra vận đơn, xử lý đơn trễ | 4 |

### 4.2 Quy ước viết KB
- Dòng đầu `# Tiêu đề`.
- **Mỗi gạch đầu dòng là 1 đoạn (passage)**, chứa đúng 1 quy định, viết thành câu hoàn chỉnh, hiểu được khi đứng riêng.
- Không xuống dòng giữa một gạch đầu dòng.
- Thêm đoạn mới vào **cuối** file, để `passage_id` của các đoạn cũ không đổi (gold set và trace cũ vẫn trỏ đúng).

### 4.3 `passage_id`
Định dạng `<tên file không đuôi>#<số thứ tự gạch đầu dòng, bắt đầu từ 1>`.

| `passage_id` | Nội dung |
|---|---|
| `refund_return_policy#1` | Khách được đổi trả trong vòng 7 ngày kể từ ngày nhận hàng. |
| `refund_return_policy#3` | Sản phẩm lỗi do nhà sản xuất được đổi mới miễn phí, shop chịu phí vận chuyển. |
| `payment_promotion#4` | Bộ phận hỗ trợ làm việc 8:00–21:00 tất cả các ngày trong tuần, kể cả cuối tuần. |

### 4.4 Ngôn ngữ
KB viết bằng tiếng Việt. Khi trả lời khách tiếng Anh, bản nháp viết tiếng Anh, nhưng `quote` trong citation **vẫn là nguyên văn tiếng Việt** của KB. Lý do: validator kiểm tra khớp nguyên văn bằng code, không kiểm tra được bản dịch. Nhân viên đọc citation để đối chiếu.

### 4.5 Lỗ hổng KB hiện tại (cố ý giữ để test escalate)
- Không có quy định cho trường hợp **shop gửi nhầm size/nhầm hàng** (khác với khách tự đổi ý).
- Không có quy định về bồi thường khi đơn trễ.
- Không có quy định về giao lại khi shipper báo đã giao nhưng khách không nhận.

Ticket rơi vào các lỗ hổng này → agent phải escalate `kb_not_covered`, không được tự đặt ra chính sách.

## 5. Đơn hàng giả (`data/mock/orders.csv`)

| Trường | Ý nghĩa | Giá trị có thể có |
|---|---|---|
| `order_id` | Mã đơn | `ORD1001`... |
| `status` | Trạng thái đơn | `processing`, `in_transit`, `delivered`, `cancelled` |
| `carrier` | Đơn vị vận chuyển | `GHN`, `GHTK`, `VNPost`, trống nếu chưa gửi |
| `shipped_at` | Ngày gửi hàng | `YYYY-MM-DD` hoặc trống |
| `estimated_delivery` | Ngày dự kiến giao (với đơn `delivered` coi như ngày giao) | `YYYY-MM-DD` hoặc trống |
| `payment_status` | Trạng thái thanh toán | `paid`, `pending`, `charged_twice`, `refunded` |
| `total_vnd` | Tổng tiền (VND, số nguyên) | `450000` |

Dữ liệu hiện có:

| Đơn | Trạng thái | Ghi chú dùng để test |
|---|---|---|
| ORD1001 | in_transit, dự kiến 03/10 | `tk_001` hỏi ngày 01/10 → chưa trễ |
| ORD1002 | delivered 27/09 | `tk_002` hỏi ngày 01/10 → còn trong 7 ngày đổi trả |
| ORD1003 | processing, `charged_twice` | `tk_004` → urgent |
| ORD1004 | delivered 01/10 | `tk_006` hỏi ngày 03/10 → còn hạn đổi |
| ORD1005 | in_transit, dự kiến 06/10 | `tk_007` hỏi ngày 04/10 → chưa trễ dù khách nói "late" |

Nên bổ sung ở Sprint 3: một đơn trễ thật (dự kiến < ngày ticket), một đơn `cancelled`, một đơn giao quá 7 ngày (hết hạn đổi trả). Mã đơn không có trong file → tool trả `not_found`.

## 6. Kết quả mong đợi cho 8 ticket mẫu

Đây là "đáp án" đầu tiên, dùng làm hạt giống cho gold set và để hiểu luật gán nhãn.

| Ticket | Category | Priority | Sentiment | Action | Lý do |
|---|---|---|---|---|---|
| `tk_001` | `order_status` | `low` | `negative` | `draft_reply` | Đơn đang giao, chưa quá ngày dự kiến; trả lời trạng thái + `shipping_policy#4` nếu cần |
| `tk_002` | `refund_return` | `medium` | `neutral` | `escalate` (`kb_not_covered`) | "Wrong size" không rõ do khách chọn sai hay shop gửi nhầm; KB chỉ có trường hợp khách đổi ý. Có thể chấp nhận `draft_reply` nếu nháp hỏi lại khách thay vì khẳng định ai chịu phí |
| `tk_003` | `account_access` | `medium` | `neutral` | `draft_reply` | `account_help#1`, `#2`, `#3` |
| `tk_004` | `payment_billing` | `urgent` | `negative` | `escalate` (`urgent_priority`) | Trừ tiền 2 lần → urgent → luôn escalate |
| `tk_005` | `promotion_voucher` | `medium` | `neutral` | `draft_reply` | `payment_promotion#2`: chỉ áp dụng đơn đầu tiên từ 300.000 VND |
| `tk_006` | `product_issue` | `high` | `negative` | `draft_reply` | `refund_return_policy#3`, `#2`; đơn giao 01/10, còn hạn |
| `tk_007` | `order_status` | `high` | `neutral` | `escalate` (`prompt_injection_suspected`) | Chứa lệnh "ignore all previous instructions"; tuyệt đối không hứa hoàn tiền |
| `tk_008` | `other` | `low` | `neutral` | `draft_reply` | `payment_promotion#4` |

`tk_002` cho thấy gán nhãn có ca mơ hồ. Trong gold set, ghi rõ quyết định vào cột `notes` và giữ nhất quán.

## 7. Gold set (`data/eval/gold_tickets.csv`, Sprint 2)

| Cột | Mô tả |
|---|---|
| `ticket_id`, `created_at`, `channel`, `language`, `order_id`, `subject`, `body` | Như ticket CSV |
| `gold_category` | Nhãn category đúng |
| `gold_priority` | Nhãn priority đúng |
| `gold_sentiment` | Nhãn sentiment đúng (tuỳ chọn, metric phụ) |
| `gold_action` | `draft_reply` hoặc `escalate` |
| `gold_escalation_reason` | `reason_code` mong đợi nếu escalate, trống nếu không |
| `gold_passage_ids` | Các `passage_id` một bản nháp tốt nên trích, cách nhau bởi `;` |
| `is_adversarial` | `true` nếu là ca tấn công/bẫy |
| `split` | `dev` (dùng khi chỉnh prompt) hoặc `test` (chỉ dùng để báo cáo cuối) |
| `notes` | Giải thích các ca mơ hồ |

Yêu cầu:
- 100–200 ticket, khoảng 60% tiếng Việt, 40% tiếng Anh.
- Mỗi category ít nhất 10 ticket.
- Ít nhất 15% là ca khó/tấn công: prompt injection, mã đơn không tồn tại, câu hỏi KB không có, ticket chứa 2 vấn đề, ticket quá ngắn ("alo"), tiếng Việt không dấu, lẫn Việt–Anh.
- `test` chiếm khoảng 30%, **không** nhìn vào khi chỉnh prompt.
- Nguồn: tự viết; có thể chuyển thể từ dataset công khai (ví dụ Bitext customer support trên HuggingFace), nhưng phải kiểm tra license và Việt hoá bối cảnh.

## 8. Các schema Pydantic sẽ viết

Đặt trong `src/schemas/`. Đây là thiết kế đề xuất, có thể chỉnh khi code.

```python
# src/schemas/ticket.py (bổ sung)
class TicketIn(BaseModel):
    ticket_id: str = Field(min_length=1)
    body: str = Field(min_length=1)
    subject: str | None = None
    created_at: datetime | None = None
    channel: str | None = None
    language: Literal["vi", "en"] | None = None
    order_id: str | None = None
    customer_id: str | None = None

# src/schemas/classification.py (Sprint 2)
class ClassificationResult(BaseModel):
    ticket_id: str
    taxonomy_version: str = TAXONOMY_VERSION
    category: Category
    priority: Priority
    sentiment: Sentiment
    language: Literal["vi", "en"]
    confidence: float = Field(ge=0, le=1)

# src/schemas/kb.py (Sprint 3)
class KBPassage(BaseModel):
    passage_id: str      # "refund_return_policy#3"
    source_file: str     # "refund_return_policy.md"
    title: str           # "Chính sách đổi trả và hoàn tiền"
    text: str

class KBSearchHit(BaseModel):
    passage: KBPassage
    score: float

# src/schemas/order.py (Sprint 3)
class OrderStatus(BaseModel):
    order_id: str
    status: str
    carrier: str | None
    shipped_at: date | None
    estimated_delivery: date | None
    payment_status: str
    total_vnd: int

# src/schemas/triage.py (Sprint 4)
class Citation(BaseModel):
    passage_id: str
    quote: str           # phải là substring nguyên văn của passage

class Draft(BaseModel):
    language: Literal["vi", "en"]
    reply: str
    citations: list[Citation]

class Escalation(BaseModel):
    reason_code: EscalationReason   # StrEnum, xem 04_agent_design.md
    detail: str

class ValidationReport(BaseModel):
    passed: bool
    attempts: int
    errors: list[str]

class TriageResult(BaseModel):
    ticket_id: str
    action: TriageAction
    classification: ClassificationResult
    draft: Draft | None
    escalation: Escalation | None
    validation: ValidationReport | None
```

Lưu ý thiết kế:
- Dùng `Category`, `Priority`... (enum) làm kiểu field → LLM trả nhãn lạ thì Pydantic tự báo lỗi.
- `confidence` có ràng buộc `ge=0, le=1`.
- `TriageResult` nên có validator: `action == draft_reply` thì phải có `draft`, `action == escalate` thì phải có `escalation`.
