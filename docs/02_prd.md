# 02 — PRD (Đặc tả yêu cầu sản phẩm)

> PRD trả lời: hệ thống **phải làm được gì**, input/output trông thế nào, lỗi trả về ra sao. Mọi test API nên viết dựa trên file này.

## 1. Danh sách API

| Method | Path | Sprint | Trạng thái | Mục đích |
|---|---|---|---|---|
| GET | `/health` | 1 | ✅ Xong | Kiểm tra service sống |
| POST | `/api/v1/tickets/validate` | 1 | ✅ Xong | Kiểm tra file CSV ticket |
| POST | `/api/v1/tickets/classify` | 2 | Chưa làm | Chỉ phân loại 1 ticket (tiện debug Sprint 2) |
| POST | `/api/v1/tickets/triage` | 5 | Chưa làm | Triage 1 ticket: phân loại + nháp hoặc escalate |
| POST | `/api/v1/batches` | 5 | Chưa làm | Triage cả file CSV |
| GET | `/api/v1/batches/{batch_id}` | 5 | Chưa làm | Xem kết quả batch |
| GET | `/api/v1/tickets/{ticket_id}/trace` | 5 | Chưa làm | Xem từng bước agent đã làm |

Quy ước chung:
- Mọi endpoint nghiệp vụ có prefix `/api/v1` (đặt trong `src/api/router.py`). `/health` nằm ngoài prefix vì là endpoint hệ thống.
- Route chỉ lo HTTP (đọc request, gọi service, đổi exception thành status code). Logic nằm trong `src/services/`.
- Lỗi có cấu trúc trả về dạng `{"detail": ...}` (mặc định của FastAPI `HTTPException`).

## 2. Chi tiết từng endpoint

### 2.1 `GET /health` ✅
Response `200`:
```json
{"status": "ok", "service": "support-ticket-agent"}
```

### 2.2 `POST /api/v1/tickets/validate` ✅
**Mục đích:** trưởng nhóm upload CSV, biết file có dùng được không **trước khi** tốn tiền chạy LLM.

**Request:** `multipart/form-data`, field `file` là file `.csv`.

**Xử lý** (`src/services/ticket_validation.py`):
1. Đuôi file không phải `.csv` → `415`.
2. Đọc bằng pandas với `encoding="utf-8-sig"` (bỏ BOM của Excel) và `dtype=str` (giữ `"001"` không bị thành `1`).
3. Không đọc được → `400`.
4. Thiếu cột bắt buộc `ticket_id` hoặc `body` → `400` kèm danh sách cột thiếu.
5. Tìm: dòng có `ticket_id` rỗng, dòng có `body` rỗng (kể cả chỉ có khoảng trắng), `ticket_id` trùng.
6. Trả `status = "valid"` nếu không có vấn đề, ngược lại `"has_issues"`.

**Số dòng** trong response là số dòng trong file mở bằng Excel: dòng 1 là header, nên dữ liệu đầu tiên là dòng 2.

**Response `200`:**
```json
{
  "status": "has_issues",
  "filename": "tickets.csv",
  "total_tickets": 4,
  "columns": ["ticket_id", "body"],
  "issues": {
    "blank_ticket_id_rows": [4],
    "blank_body_rows": [5],
    "duplicate_ticket_ids": ["t1"]
  }
}
```

**Lỗi:**

| Status | Khi nào | `detail` |
|---|---|---|
| 415 | Đuôi file không phải `.csv` | `"Please upload a .csv file."` |
| 400 | pandas không đọc được | `"Unable to read CSV file."` |
| 400 | Thiếu cột bắt buộc | `{"message": "Missing required columns.", "missing_columns": [...]}` |
| 422 | Không gửi field `file` | Lỗi validate mặc định của FastAPI |

**Quyền riêng tư:** response chỉ trả **số dòng và ID**, không lặp lại nội dung ticket (body có thể chứa thông tin cá nhân).

**Việc còn thiếu so với data spec** (có thể bổ sung ở Sprint 2): kiểm tra `created_at` đúng định dạng ISO, `language` thuộc `vi`/`en`.

### 2.3 `POST /api/v1/tickets/classify` (Sprint 2)
**Request (JSON):**
```json
{
  "ticket_id": "tk_002",
  "subject": "Refund request",
  "body": "The shoes I received are the wrong size. How do I return them and get my money back?",
  "language": "en",
  "order_id": "ORD1002"
}
```
**Response `200`:** schema `ClassificationResult` (xem `03_data_spec.md` mục 5):
```json
{
  "ticket_id": "tk_002",
  "taxonomy_version": "0.1",
  "category": "refund_return",
  "priority": "medium",
  "sentiment": "neutral",
  "language": "en",
  "confidence": 0.9
}
```
**Lỗi:** `422` nếu thiếu `ticket_id`/`body`; `502` nếu LLM trả output không parse được sau khi thử lại.

### 2.4 `POST /api/v1/tickets/triage` (Sprint 5)
**Request:** giống `classify`.

**Response `200` khi soạn nháp:**
```json
{
  "ticket_id": "tk_006",
  "action": "draft_reply",
  "classification": { "category": "product_issue", "priority": "high", "...": "..." },
  "draft": {
    "language": "vi",
    "reply": "Chào bạn, shop rất tiếc vì tai nghe bị lỗi ...",
    "citations": [
      {
        "passage_id": "refund_return_policy#3",
        "quote": "Sản phẩm lỗi do nhà sản xuất được đổi mới miễn phí, shop chịu phí vận chuyển."
      }
    ]
  },
  "escalation": null,
  "validation": { "passed": true, "attempts": 1, "errors": [] },
  "trace_id": "..."
}
```

**Response `200` khi escalate** (escalate vẫn là `200` vì đây là kết quả nghiệp vụ hợp lệ, không phải lỗi):
```json
{
  "ticket_id": "tk_004",
  "action": "escalate",
  "classification": { "category": "payment_billing", "priority": "urgent", "...": "..." },
  "draft": null,
  "escalation": { "reason_code": "urgent_priority", "detail": "Customer charged twice for ORD1003." },
  "validation": null,
  "trace_id": "..."
}
```

### 2.5 `POST /api/v1/batches` và `GET /api/v1/batches/{batch_id}` (Sprint 5)
- Upload CSV → chạy validate trước; có vấn đề thì trả `400` kèm `ValidationResult`, không chạy LLM.
- Hợp lệ → triage từng ticket, lưu DB, trả `batch_id` và tóm tắt: số ticket, số nháp, số escalate.
- Bản MVP chạy đồng bộ (đợi xong mới trả). Chạy nền (background job) để sau.

### 2.6 `GET /api/v1/tickets/{ticket_id}/trace` (Sprint 5)
Trả danh sách bước theo thứ tự:
```json
{
  "ticket_id": "tk_006",
  "steps": [
    {"index": 0, "type": "classification", "output": {"category": "product_issue", "...": "..."}},
    {"index": 1, "type": "tool_call", "tool": "get_order_status", "args": {"order_id": "ORD1004"}, "output": {"status": "delivered", "...": "..."}},
    {"index": 2, "type": "tool_call", "tool": "search_kb", "args": {"query": "sản phẩm lỗi đổi mới", "top_k": 3}, "output": ["..."]},
    {"index": 3, "type": "submit_draft", "output": {"...": "..."}},
    {"index": 4, "type": "validation", "output": {"passed": true, "errors": []}}
  ]
}
```
`404` nếu không có ticket.

## 3. User stories và tiêu chí chấp nhận

Tiêu chí chấp nhận (acceptance criteria) nên được chuyển thẳng thành test.

**US-01 Validate batch** ✅
> Là trưởng nhóm, tôi upload CSV và thấy số ticket, dòng bị trống, ID trùng.
- [x] File không phải `.csv` → 415.
- [x] Thiếu `ticket_id`/`body` → 400 có danh sách cột thiếu.
- [x] Chỉ có 2 cột bắt buộc vẫn hợp lệ.
- [x] Báo đúng số dòng trống và ID trùng.
- [x] Không lặp lại nội dung ticket trong response.

**US-02 Phân loại**
> Là nhân viên CSKH, tôi thấy category, priority, sentiment của từng ticket theo taxonomy có version.
- [ ] Output luôn thuộc taxonomy hiện hành; nhãn lạ → lỗi, không lọt ra ngoài.
- [ ] Có `taxonomy_version` trong output.
- [ ] Có `confidence` trong khoảng 0–1.
- [ ] Ticket không rõ loại → `other`, không ép vào loại khác.

**US-03 Soạn nháp**
> Là nhân viên CSKH, tôi nhận bản nháp bằng ngôn ngữ của khách, kèm trích dẫn KB.
- [ ] Ngôn ngữ nháp = ngôn ngữ ticket.
- [ ] Mỗi câu về chính sách có ít nhất 1 citation; mọi citation khớp nguyên văn KB.
- [ ] Mọi dữ kiện đơn trong nháp có trong output `get_order_status` của lần chạy này.
- [ ] Không hứa hoàn tiền/bồi thường ngoài KB.

**US-04 Escalate**
> Là trưởng nhóm, ticket agent không xử lý an toàn được sẽ được escalate với lý do rõ ràng.
- [ ] Mọi ticket `urgent` đều escalate.
- [ ] Ca prompt injection (`tk_007`) escalate với `prompt_injection_suspected`.
- [ ] Mỗi escalation có `reason_code` thuộc danh sách cố định (xem `04_agent_design.md`).

**US-05 Trace**
> Là lập trình viên, tôi xem được từng tool agent đã gọi và vì sao nháp đạt/trượt validate.
- [ ] Mỗi bước có thứ tự, loại bước, input, output, thời gian.
- [ ] Lỗi validate được ghi rõ (citation nào sai, dữ kiện nào không có nguồn).

## 4. Yêu cầu chức năng

| Mã | Yêu cầu |
|---|---|
| FR-01 | Trường bắt buộc: `ticket_id`, `body`. Tuỳ chọn: `subject`, `created_at`, `channel`, `language`, `order_id`, `customer_id`. |
| FR-02 | Đọc CSV bằng UTF-8 / UTF-8 có BOM, mọi cột là chuỗi. |
| FR-03 | Output của LLM luôn được parse vào schema Pydantic; output sai → thử lại tối đa 1 lần, vẫn sai → lỗi (classify) hoặc escalate (triage). |
| FR-04 | Bản nháp không chứa dữ kiện đơn hoặc câu chính sách không có nguồn từ tool/KB. |
| FR-05 | Agent chỉ gọi được tool trong whitelist; tool lạ → bị từ chối và ghi vào trace. |
| FR-06 | Agent dừng sau `MAX_STEPS` bước; chưa xong → escalate `max_steps_exceeded`. |
| FR-07 | Lỗi input trả 4xx rõ ràng; lỗi từ phía LLM trả 502. |

## 5. Yêu cầu phi chức năng

| Mã | Yêu cầu |
|---|---|
| NFR-01 | Python 3.11, FastAPI, Pydantic v2, pandas, pytest + HTTPX. |
| NFR-02 | Toàn bộ test chạy được không cần API key (`FakeLLM`). |
| NFR-03 | Secret chỉ nằm trong `.env` (đã có trong `.gitignore`); repo chỉ có `.env.example`. |
| NFR-04 | Không log nội dung ticket ở mức INFO; trace lưu trong DB, không in ra console. |
| NFR-05 | Mỗi lần chạy model thật ghi lại: model, số token, độ trễ, để tính chi phí trong eval. |
| NFR-06 | Đổi LLM provider chỉ cần sửa config, không sửa agent. |
