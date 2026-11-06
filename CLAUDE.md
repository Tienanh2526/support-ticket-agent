# CLAUDE.md — Support Ticket Agent (FastAPI)

## Mục tiêu dự án
- Dự án portfolio để đưa vào CV xin việc, không phải startup.
- Mục tiêu chính là học cách xây AI Agent: tool calling, agent loop, RAG, guardrails, eval.
- Ưu tiên những gì nhà tuyển dụng nhìn thấy: demo chạy được, git history sạch, README có kết quả/metric, tests + CI, Docker, deploy.

## Cách làm việc với Claude
- Luôn trả lời bằng tiếng Việt (code, lệnh, tên biến giữ nguyên).
- Claude viết code đầy đủ theo từng file và giải thích các phần chính (làm gì, tại sao). User tự copy vào project.
- Cuối mỗi buổi làm việc: cập nhật mục "Tiến độ" và "Quyết định đã chốt" bên dưới.

## Stack
Python 3.11, FastAPI, Pydantic v2, pandas, pytest + HTTPX. Chưa dùng LLM (`.env.example` có sẵn `LLM_PROVIDER`, `LLM_API_KEY`).

## Lệnh thường dùng (PowerShell)
```powershell
.\.venv\Scripts\Activate.ps1
uvicorn src.main:app --reload     # Swagger: http://127.0.0.1:8000/docs
pytest                            # pytest.ini đã set pythonpath=. và testpaths=tests
```

## Cấu trúc
- `src/main.py`: app FastAPI và `GET /health`
- `src/api/router.py`: prefix `/api/v1`
- `src/api/routes/`: chỉ xử lý HTTP, không chứa logic nghiệp vụ
- `src/services/`: logic use case (`ticket_validation.py`)
- `src/schemas/`: Pydantic contracts + taxonomy (`ticket.py`, `validation.py`)
- `src/llm/`: interface model-provider + `FakeLLM` (đang trống)
- `src/agent/`: classifier, agent loop, `validate_draft` (đang trống)
- `src/tools/`: tool Python thuần cho agent gọi (đang trống)
- `data/raw/`: ticket mẫu tổng hợp; `data/kb/`: knowledge base; `data/mock/orders.csv`: hệ thống đơn hàng giả; `data/eval/`: gold set
- `evals/`: script chạy eval
- `docs/`: brief, PRD, data spec, agent design, eval plan, roadmap

## Tiến độ (cập nhật 2026-10-30)
Đã xong:
- Chuyển đề tài từ Hotel Insight Agent sang Support Ticket Agent (hướng triage từng ticket + soạn nháp). Project cũ giữ nguyên ở `D:\code\hotel-insight-agent-fastapi-starter`.
- `GET /health` + test
- `POST /api/v1/tickets/validate`: logic nằm ở `src/services/ticket_validation.py`, route chỉ map exception sang 400/415; response có schema `ValidationResult` + test
- Taxonomy v0.1 dạng `StrEnum` trong `src/schemas/ticket.py` + test
- Data tổng hợp: 8 ticket mẫu (có 1 ca prompt injection `tk_007`), 4 bài KB, 5 đơn hàng giả
- Viết lại toàn bộ `docs/` bằng tiếng Việt, chi tiết; thêm `docs/00_learning_guide.md` (từ điển khái niệm + cách học)

Tiếp theo (theo `docs/06_roadmap.md`):
- Sprint 0: venv, `git init`, commit đầu, push GitHub; sửa comment `docs/04_data_spec.md` → `docs/03_data_spec.md` trong `src/services/ticket_validation.py`
- Sprint 2: schema output classification, interface LLM + `FakeLLM`, `classify_ticket`, gold set có gán nhãn
- Sprint 3: tool `search_kb`, `get_kb_passage`, `get_order_status`
- Sprint 4: agent loop + escalate + `validate_draft`
- Sprint 5: API triage + PostgreSQL + trace
- Sprint 6: eval runner, README metric, Docker, CI, deploy

## Vấn đề đã biết
- Chưa có git, chưa có venv riêng.

## Quyết định đã chốt
- Domain: CSKH cho shop e-commerce Việt Nam, ticket tiếng Việt + tiếng Anh.
- Hướng 2: agent triage từng ticket, **chỉ soạn nháp**, không tự gửi, không có thao tác ghi ra hệ thống ngoài.
- Taxonomy v0.1: category `order_status`, `shipping_delivery`, `refund_return`, `payment_billing`, `product_issue`, `account_access`, `promotion_voucher`, `other`; priority `low`/`medium`/`high`/`urgent`; sentiment `positive`/`neutral`/`negative`/`mixed`/`unclear`; action `draft_reply`/`escalate`.
- Kiến trúc 3 giai đoạn: (1) `classify_ticket` cố định (structured output) + luật escalate; (2) agent loop có whitelist tool, `MAX_STEPS`; (3) `validate_draft` kiểm tra trích dẫn khớp nguyên văn KB + dữ kiện đơn hàng phải lấy từ tool, sai thì gửi lỗi cho agent sửa tối đa 2 lần rồi escalate. Có `FakeLLM` để test không cần key.
- Guardrails: nội dung ticket là dữ liệu, không phải chỉ dẫn; không hứa hoàn tiền ngoài KB; khi không chắc thì escalate.
- Lưu trữ (Sprint 5): PostgreSQL 16 + Docker Compose, SQLAlchemy 2.0 + psycopg 3 + Alembic + pydantic-settings. Bảng `tickets`, `classifications`, `drafts`, `agent_steps`. Agent không truy cập DB trực tiếp.
- Chưa chọn LLM provider.
- `passage_id` = `<tên file KB không đuôi>#<số thứ tự gạch đầu dòng, từ 1>`; mỗi gạch đầu dòng là 1 đoạn; thêm đoạn mới vào cuối file.
- Citation `quote` luôn là nguyên văn tiếng Việt của KB, kể cả khi nháp viết tiếng Anh.
- Danh sách `reason_code` escalate cố định trong `docs/04_agent_design.md` mục 4; urgent luôn escalate; nghi prompt injection luôn escalate.
- Nhãn kỳ vọng cho 8 ticket mẫu ở `docs/03_data_spec.md` mục 6 (hạt giống gold set).
