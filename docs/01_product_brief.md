# 01 — Product Brief (Tóm tắt sản phẩm)

**Phiên bản:** 0.2 | **Trạng thái:** Nháp | **Loại:** Project portfolio để học AI agent engineering

## 1. Tầm nhìn

Một AI agent nhận ticket CSKH của shop thương mại điện tử Việt Nam (tiếng Việt và tiếng Anh), **phân loại** ticket, **tra cứu** đơn hàng và chính sách, rồi **soạn bản nháp** trả lời có trích dẫn chính sách. Nhân viên CSKH chỉ cần đọc lại, sửa nếu cần và bấm gửi.

Câu tóm tắt để đưa vào CV:
> Xây dựng AI agent triage ticket CSKH song ngữ Việt–Anh với tool calling, agentic RAG trên knowledge base, guardrails kiểm chứng trích dẫn và bộ eval đo F1 phân loại, recall escalate và tỉ lệ grounding.

## 2. Vấn đề

| Nỗi đau | Hậu quả |
|---|---|
| Nhiều ticket lặp lại (đơn đâu, trả hàng, quên mật khẩu) | Nhân viên tốn thời gian gõ lại cùng một nội dung |
| Phải mở nhiều hệ thống (hệ thống đơn, tài liệu chính sách) | Chậm, dễ sót |
| Nhân viên mới không thuộc chính sách | Trả lời sai, hứa hoàn tiền sai quy định |
| Ticket gấp (bị trừ tiền 2 lần, bị chiếm tài khoản) lẫn trong ticket thường | Xử lý trễ ca nghiêm trọng |
| Ticket song ngữ | Phải đổi ngôn ngữ trả lời theo khách |

## 3. Người dùng

### Nhân viên CSKH (người dùng chính)
- Mở ticket, thấy sẵn: loại vấn đề, mức ưu tiên, cảm xúc khách, bản nháp kèm trích dẫn.
- Duyệt, sửa, gửi.
- Cần: bản nháp **đúng chính sách**, đúng ngôn ngữ của khách, biết câu nào lấy từ đâu.

### Trưởng nhóm CSKH
- Xem các ticket bị escalate và lý do.
- Upload file CSV để kiểm tra dữ liệu trước khi chạy hàng loạt.
- Cần: không bỏ sót ticket gấp; biết agent hoạt động tốt tới đâu (metric).

### Lập trình viên (chính bạn)
- Cần trace từng bước để debug, và bộ eval để biết thay đổi prompt có làm tốt lên hay tệ đi.

## 4. Một ví dụ end-to-end

Ticket `tk_006` (tiếng Việt, kênh chat, đơn `ORD1004`):
> "Tai nghe nhận về bị rè một bên, mình muốn đổi cái mới."

Agent xử lý:
1. Phân loại: `product_issue`, ưu tiên `high` (sản phẩm lỗi), cảm xúc `negative`, ngôn ngữ `vi`.
2. Không thuộc luật escalate bắt buộc → vào agent loop.
3. Gọi `get_order_status("ORD1004")` → `delivered`, giao ngày `2026-10-01`. Ticket tạo ngày `2026-10-03` → còn trong hạn 7 ngày đổi trả.
4. Gọi `search_kb("sản phẩm lỗi đổi mới")` → tìm thấy đoạn "Sản phẩm lỗi do nhà sản xuất được đổi mới miễn phí, shop chịu phí vận chuyển."
5. Soạn nháp tiếng Việt, xin lỗi khách, xác nhận đơn đã giao ngày 01/10, nêu chính sách đổi mới miễn phí kèm trích dẫn, hướng dẫn giữ nguyên tem/hộp.
6. Validate: trích dẫn khớp nguyên văn KB, ngày giao lấy từ kết quả tool → đạt.
7. Trả về cho nhân viên duyệt.

## 5. Phạm vi MVP

**Có làm:**
- Nhận ticket qua API: 1 ticket dạng JSON hoặc nhiều ticket dạng file CSV.
- Kiểm tra (validate) file CSV trước khi xử lý.
- Phân loại: category, priority, sentiment, language, confidence.
- Tra cứu bằng tool: knowledge base và hệ thống đơn hàng giả.
- Soạn nháp có trích dẫn KB, hoặc escalate kèm lý do.
- Kiểm tra mọi bản nháp trước khi trả về.
- Lưu trace của từng ticket.
- Bộ eval có metric đưa vào README.

**Không làm (out of scope) và vì sao:**

| Không làm | Lý do |
|---|---|
| Tự động gửi trả lời cho khách | Rủi ro cao; mục tiêu là trợ lý, không thay người |
| Hoàn tiền, sửa đơn, mọi thao tác ghi ra hệ thống ngoài | Agent chỉ đọc → kể cả bị prompt injection cũng không gây hại |
| Tích hợp helpdesk thật (Zendesk, Freshdesk...) | Tốn công tích hợp, không thêm giá trị học về agent |
| Giao diện web đầy đủ | Swagger UI đủ để demo; nếu dư thời gian mới làm UI nhỏ |
| Fine-tune model | Ngoài mục tiêu; dùng prompt + tool + eval là đủ |
| Đa tenant, phân quyền người dùng | Không cần cho portfolio |

## 6. Nguyên tắc thiết kế

1. **Chỉ soạn nháp.** Con người luôn là người gửi.
2. **Mọi câu nói về chính sách phải có trích dẫn** tới đoạn KB, và đoạn trích phải khớp nguyên văn.
3. **Dữ kiện về đơn hàng** (trạng thái, ngày, số tiền, hãng vận chuyển) chỉ được lấy từ output của tool trong chính lần chạy đó.
4. **Nội dung ticket là dữ liệu không đáng tin**, không bao giờ là chỉ dẫn cho agent.
5. **Không chắc thì escalate**, không đoán.
6. **Guardrail bằng code**, không chỉ dựa vào việc dặn LLM trong prompt.
7. **Test được mà không cần API key** (nhờ `FakeLLM`).

## 7. Tiêu chí thành công

| Tiêu chí | Đo bằng |
|---|---|
| Phân loại đúng | Category macro-F1 ≥ 0,85 trên test split |
| Không bỏ sót ticket gấp | Recall của `urgent` ≥ 0,95 |
| Không bịa chính sách | 100% trích dẫn trong bản nháp cuối khớp nguyên văn KB |
| Không bịa số liệu đơn | 0 dữ kiện đơn hàng không có nguồn từ tool |
| Chống prompt injection | 100% ca injection trong gold set được xử lý an toàn |
| Gây ấn tượng với nhà tuyển dụng | Demo chạy được, README có bảng metric, CI xanh, có Docker, có link deploy |

## 8. Rủi ro và cách giảm

| Rủi ro | Cách giảm |
|---|---|
| LLM bịa chính sách | Validate trích dẫn bằng code; sai thì sửa hoặc escalate |
| LLM bịa trạng thái đơn | Đối chiếu dữ kiện trong nháp với output tool |
| Prompt injection | Bọc ticket như dữ liệu; agent không có tool ghi; có ca test riêng |
| Tốn tiền API khi phát triển | `FakeLLM` cho unit test; chỉ gọi model thật khi chạy eval |
| Gold set nhỏ, metric không đáng tin | Ghi rõ kích thước gold set cạnh metric; tách test split |
| Phạm vi phình to | Bám roadmap, mọi thứ ngoài mục 5 phải ghi vào "để sau" |
