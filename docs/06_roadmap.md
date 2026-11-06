# 06 — Lộ trình (Roadmap)

> Mỗi sprint có: **mục tiêu**, **khái niệm cần học**, **các bước cụ thể** (file nào, làm gì), **definition of done** (làm xong thì kiểm tra bằng cách nào) và **câu hỏi tự kiểm tra**. Mỗi sprint ước tính 1–2 tuần nếu làm buổi tối.

## Tổng quan

| Sprint | Chủ đề | Kết quả nhìn thấy được | Trạng thái |
|---|---|---|---|
| 0 | Hạ tầng dev | git, venv, commit đầu tiên | ⏳ Chưa làm |
| 1 | FastAPI + validate CSV | `/health`, `/tickets/validate`, taxonomy | ✅ Xong |
| 2 | Phân loại | `classify_ticket`, `FakeLLM`, gold set, F1 đầu tiên | Tiếp theo |
| 3 | Tool | `search_kb`, `get_kb_passage`, `get_order_status` | |
| 4 | Agent loop | Loop + escalate + `validate_draft` | |
| 5 | API triage + DB | `/triage`, `/batches`, trace, PostgreSQL | |
| 6 | Ship | Eval, README metric, Docker, CI, deploy | |

---

## Sprint 0: Hạ tầng dev (làm ngay)

Đang thiếu git và venv riêng (xem `CLAUDE.md` > "Vấn đề đã biết"). Git history sạch là thứ nhà tuyển dụng xem, nên làm trước khi viết thêm code.

**Các bước:**
1. Tạo venv và cài thư viện:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   pytest
   ```
2. Sửa comment trong `src/services/ticket_validation.py`: đang ghi `docs/04_data_spec.md`, đúng phải là `docs/03_data_spec.md`.
3. Khởi tạo git và commit đầu tiên:
   ```powershell
   git init
   git add .
   git commit -m "chore: initial FastAPI skeleton with CSV validation"
   ```
4. Tạo repo trên GitHub và push.

**Quy ước commit** (Conventional Commits): `feat:` tính năng, `fix:` sửa lỗi, `test:` thêm test, `docs:` tài liệu, `refactor:` đổi cấu trúc không đổi hành vi, `chore:` việc lặt vặt. Mỗi commit một việc.

**Done khi:** `pytest` xanh trong venv; `git log` có commit đầu; repo có trên GitHub.

---

## Sprint 1: FastAPI + validate dữ liệu ✅

**Đã làm:** `GET /health`; `POST /api/v1/tickets/validate` (logic ở `src/services/ticket_validation.py`, route chỉ map exception sang 400/415); schema `ValidationResult`; taxonomy `StrEnum` có `TAXONOMY_VERSION`; 8 ticket mẫu, 4 bài KB, 5 đơn giả; test cho tất cả.

**Đã học:** tách route/service, `UploadFile`, đọc CSV an toàn (`utf-8-sig`, `dtype=str`), `TestClient`, `StrEnum`.

**Tự kiểm tra:**
- Vì sao route không chứa logic validate?
- Nếu bỏ `dtype=str`, ticket ID `001` sẽ thành gì?
- Vì sao số dòng trong response là `index + 2`?

---

## Sprint 2: Phân loại

**Mục tiêu:** có hàm `classify_ticket` chạy được với cả `FakeLLM` và LLM thật, và có con số F1 đầu tiên trên gold set.

**Khái niệm cần học:**
- Structured output / JSON mode / tool-forced output của LLM provider.
- Pydantic v2: `model_validate`, `model_json_schema()`, `Field(ge=, le=)`, `ValidationError`.
- `typing.Protocol` (để viết interface `LLMClient`).
- Precision, recall, F1, macro-F1, confusion matrix (`05_evaluation_plan.md` mục 3.1).

**Các bước:**
1. **Schema** — `src/schemas/ticket.py` thêm `TicketIn`; tạo `src/schemas/classification.py` với `ClassificationResult` (thiết kế ở `03_data_spec.md` mục 8).
   Test: nhãn lạ bị từ chối; `confidence = 1.5` bị từ chối.
2. **Interface LLM** — `src/llm/base.py`: `LLMClient` (Protocol), `LLMResponse`, `ToolCall` (`04_agent_design.md` mục 5.4).
3. **FakeLLM** — `src/llm/fake.py`: nhận danh sách response viết sẵn, trả lần lượt, ghi lại các message đã nhận để test kiểm tra prompt.
4. **Prompt** — `src/agent/prompts.py`: `CLASSIFY_SYSTEM_PROMPT` sinh từ enum (lặp qua `Category` để không bao giờ lệch taxonomy) + định nghĩa + luật phân xử.
5. **Classifier** — `src/agent/classifier.py`: `classify_ticket(ticket, llm)`; parse lỗi thì thử lại 1 lần, vẫn lỗi thì raise `ClassificationError`.
   Test với `FakeLLM`: output đúng → trả kết quả; output sai rồi đúng → thử lại thành công; sai 2 lần → raise.
6. **Gold set** — `data/eval/gold_tickets.csv`: bắt đầu từ 8 ticket mẫu với nhãn ở `03_data_spec.md` mục 6, mở rộng lên ≥ 60 ticket ở sprint này (đủ 200 trước Sprint 6).
7. **Chọn LLM provider** và viết `src/llm/<provider>.py`; đọc key từ `.env`. Ghi quyết định vào `CLAUDE.md`.
8. **Eval phân loại** — `evals/metrics.py` (hàm thuần + unit test với dữ liệu nhỏ tự tính tay) và `evals/run_eval.py --stage classify`.
9. *(Tuỳ chọn)* `POST /api/v1/tickets/classify` để demo trên Swagger.

**Done khi:**
- `pytest` xanh, không cần API key.
- Chạy eval classify trên dev split ra được macro-F1 và confusion matrix.
- Có ít nhất 3 commit nhỏ (schema, fake LLM + classifier, gold set + eval).

**Tự kiểm tra:**
- Vì sao dùng enum làm kiểu field thay vì `str`?
- `FakeLLM` kiểm tra được điều gì, và **không** kiểm tra được điều gì?
- Vì sao không nên chỉnh prompt dựa trên test split?
- Macro-F1 khác accuracy ở chỗ nào, khi nào khác nhau nhiều?

---

## Sprint 3: Tool

**Mục tiêu:** ba tool chỉ đọc, chạy độc lập, test đầy đủ, chưa cần LLM.

**Khái niệm cần học:**
- Tách đoạn (chunking) tài liệu; vì sao đoạn nhỏ, tự đứng được thì trích dẫn tốt hơn.
- BM25 (thư viện `rank-bm25`); tách từ tiếng Việt (bắt đầu với tách theo khoảng trắng + lowercase; tìm hiểu thêm `underthesea`/`pyvi` nếu cần).
- JSON Schema cho định nghĩa tool (`model_json_schema()`).
- Unicode NFC/NFD với tiếng Việt (`unicodedata.normalize`).

**Các bước:**
1. **Schema** — `src/schemas/kb.py` (`KBPassage`, `KBSearchHit`), `src/schemas/order.py` (`OrderStatus`).
2. **KB loader** — `src/tools/kb.py`: đọc `data/kb/*.md`, mỗi gạch đầu dòng thành `KBPassage` với `passage_id = "<file>#<n>"` (`03_data_spec.md` mục 4.3).
   Test: số đoạn mỗi file đúng (4, 4, 6, 4); `refund_return_policy#3` đúng nội dung.
3. **`get_kb_passage(passage_id)`** — trả nguyên văn hoặc `{"error": "not_found"}`.
4. **`search_kb(query, top_k=3)`** — BM25 trên các đoạn; trả top_k kèm score.
   Test: "đổi trả bao nhiêu ngày" → top 1 là `refund_return_policy#1`; "WELCOME10" → `payment_promotion#2`; "weekend support" (tiếng Anh) → ghi nhận kết quả, đây là giới hạn đã biết của BM25 khi KB tiếng Việt.
5. **`get_order_status(order_id)`** — `src/tools/orders.py`: đọc `data/mock/orders.csv` với `dtype=str`, chuyển đổi kiểu qua `OrderStatus`; không có → `not_found`; chuẩn hoá mã (strip, upper).
   Bổ sung vào `orders.csv`: 1 đơn trễ thật, 1 đơn `cancelled`, 1 đơn giao quá 7 ngày.
6. **Registry** — `src/tools/registry.py`: dict `TOOLS = {name: (hàm, schema tham số, mô tả)}`, hàm `run(name, args)` kiểm tra whitelist, validate tham số, bắt exception → trả lỗi dạng dữ liệu. Hàm `tool_specs()` sinh định nghĩa tool cho LLM.
7. **Đo passage recall** của `search_kb` với `gold_passage_ids` trên gold set (chưa cần LLM).

**Done khi:** test tool xanh; `run("delete_order", {...})` trả `unknown_tool`; có số passage recall@3.

**Tự kiểm tra:**
- Vì sao tool trả lỗi dạng dữ liệu thay vì raise exception?
- Vì sao `passage_id` phải ổn định khi thêm đoạn KB mới?
- BM25 sẽ gặp khó với ticket tiếng Anh hỏi KB tiếng Việt thế nào? Có những cách nào xử lý?

---

## Sprint 4: Agent loop

**Mục tiêu:** pipeline đầy đủ phân loại → luật → loop → validate → `TriageResult`, chạy được với `FakeLLM` và LLM thật.

**Khái niệm cần học:**
- Định dạng message tool use của provider đã chọn (assistant tool call, tool result, ID ghép cặp).
- Agent loop, điều kiện dừng, `MAX_STEPS`.
- Prompt injection và phòng thủ nhiều lớp (`04_agent_design.md` mục 7.1).
- Regex Python.

**Các bước:**
1. **Schema** — `src/schemas/triage.py`: `Citation`, `Draft`, `Escalation`, `EscalationReason`, `ValidationReport`, `AgentStep`, `TriageResult` (+ validator ràng buộc action ↔ draft/escalation).
2. **Luật** — `src/agent/rules.py`: `pre_loop_escalation` (urgent, confidence thấp, injection, đe doạ pháp lý).
   Test: `tk_004` → `urgent_priority`; `tk_007` → `prompt_injection_suspected`; thêm 5 biến thể injection tiếng Việt/không dấu.
3. **Validator** — `src/agent/validator.py`: các kiểm tra ở `04_agent_design.md` mục 6. Viết **trước** loop vì là hàm thuần, dễ test nhất.
   Test: quote đúng → đạt; sai một chữ → lỗi; ngày không có trong tool output → lỗi; mã đơn chưa tra → lỗi; "refund approved" → lỗi.
4. **Loop** — `src/agent/loop.py`: `run_agent` theo mã giả mục 5.2; prompt agent trong `prompts.py`.
   Test với `FakeLLM`: luồng bình thường (tool → submit); gọi tool lạ; vượt `MAX_STEPS`; tự gọi `escalate`; nháp sai → sửa → đạt; sai 3 lần → `validation_failed`.
5. **Service** — `src/services/triage.py`: `triage_ticket(ticket, llm) -> TriageResult` ghép các bước, thu trace.
6. **Chạy thật** 8 ticket mẫu với LLM thật, so với bảng kỳ vọng ở `03_data_spec.md` mục 6; đọc trace, sửa prompt.

**Done khi:** test xanh không cần key; 8 ticket mẫu với LLM thật cho action khớp bảng kỳ vọng (cho phép `tk_002` theo một trong hai cách đã ghi); `tk_007` không bao giờ ra nháp hứa hoàn tiền.

**Tự kiểm tra:**
- Nếu bỏ hết phòng thủ trong prompt, vì sao `tk_007` vẫn không gây hại được?
- Vì sao validator kiểm tra "đoạn được trích đã được tool trả về" chứ không chỉ "đoạn tồn tại trong KB"?
- Điều gì xảy ra nếu LLM không bao giờ gọi `submit_draft`?

---

## Sprint 5: API triage + lưu trữ

**Mục tiêu:** triage qua API, kết quả và trace lưu PostgreSQL.

**Khái niệm cần học:**
- Docker Compose; PostgreSQL cơ bản.
- SQLAlchemy 2.0 (kiểu `Mapped[...]`, `Session`), Alembic migration.
- pydantic-settings đọc config từ `.env`.
- FastAPI dependency injection (`Depends`) để inject `LLMClient` và session DB → test thay bằng `FakeLLM` và DB test.

**Các bước:**
1. `docker-compose.yml` với `postgres:16`; `src/config.py` dùng pydantic-settings (`DATABASE_URL`, `LLM_PROVIDER`, `LLM_API_KEY`, tham số agent).
2. `src/db/models.py`: 4 bảng (`04_agent_design.md` mục 10); `alembic init`, migration đầu tiên.
3. `src/db/repository.py`: lưu/đọc ticket, classification, draft, steps.
4. Route: `POST /tickets/triage`, `POST /batches`, `GET /batches/{id}`, `GET /tickets/{id}/trace` (`02_prd.md` mục 2.4–2.6).
5. Test API với `FakeLLM` qua `app.dependency_overrides`; DB test dùng database riêng hoặc transaction rollback.

**Done khi:** `docker compose up` + `alembic upgrade head` + gọi `/triage` trên Swagger thấy kết quả và xem được trace.

**Tự kiểm tra:**
- Vì sao agent không được truy cập DB trực tiếp?
- `dependency_overrides` giúp test thế nào?
- Vì sao dùng migration thay vì `create_all()`?

---

## Sprint 6: Ship

**Mục tiêu:** đóng gói thành thứ nhà tuyển dụng mở ra là thấy giá trị trong 2 phút.

**Các bước:**
1. Gold set đủ 100–200 ticket; chạy eval trên test split; viết `evals/CHANGELOG.md`.
2. `Dockerfile` (multi-stage, user không phải root); `docker compose up` chạy cả app + DB.
3. GitHub Actions: cài dependency, `pytest` (với `FakeLLM`), lint (`ruff`). Badge CI trên README.
4. Deploy (Render/Railway/Fly.io hoặc tương đương) với giới hạn số request để không bị đốt tiền API.
5. README (tiếng Anh, cho nhà tuyển dụng): 1 câu giới thiệu, sơ đồ kiến trúc, GIF demo, bảng metric, "Design decisions", "Known limitations", cách chạy local.

**Done khi:** người lạ clone repo, chạy 3 lệnh là thấy app; README có metric thật; CI xanh; link demo hoạt động.

---

## Để sau (không làm trong MVP)
- Embeddings / hybrid search cho `search_kb`.
- Xử lý batch chạy nền (background worker).
- LLM-as-judge chấm chất lượng câu chữ.
- UI nhỏ (Streamlit hoặc React) cho nhân viên duyệt nháp.
- Prompt caching để giảm chi phí.
- Hỗ trợ thêm ngôn ngữ.
