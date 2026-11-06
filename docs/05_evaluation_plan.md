# 05 — Kế hoạch đánh giá (Eval)

> Eval trả lời câu hỏi: "Agent tốt tới đâu, và thay đổi vừa rồi làm nó tốt lên hay tệ đi?". Đây là phần nhà tuyển dụng hỏi nhiều nhất về một project AI, và là phần tạo ra bảng metric trong README.

## 1. Vì sao cần eval

- LLM không cố định: đổi một câu trong prompt có thể làm đúng ca này nhưng sai ca khác. Không đo thì không biết.
- Unit test (với `FakeLLM`) kiểm tra **code** đúng. Eval (với LLM thật) kiểm tra **hành vi** của cả hệ thống.
- Con số cụ thể ("urgent recall 0,97 trên 150 ticket") đáng tin hơn nhiều so với "agent hoạt động tốt".

| | Unit test | Eval |
|---|---|---|
| LLM | `FakeLLM` | Model thật |
| Chạy khi nào | Mỗi lần sửa code, trong CI | Khi đổi prompt/model/tham số; trước khi cập nhật README |
| Kết quả | Pass/fail | Bảng số liệu |
| Chi phí | 0 | Tốn token |

## 2. Gold set

Định dạng và yêu cầu chi tiết ở `03_data_spec.md` mục 7. Tóm tắt:
- 100–200 ticket Việt + Anh, gán nhãn tay: category, priority, action, reason_code, passage_id mong đợi.
- Tách `dev` (~70%, được nhìn khi chỉnh prompt) và `test` (~30%, chỉ chạy để báo cáo).
- ≥ 15% ca khó/tấn công.

**Vì sao phải tách test split?** Nếu chỉnh prompt cho tới khi đúng hết trên một bộ dữ liệu, prompt sẽ "học thuộc" bộ đó và con số báo cáo bị ảo. Test split giống đề thi chưa xem trước.

**Quy trình gán nhãn:**
1. Viết ticket theo danh sách tình huống (mỗi category, mỗi loại bẫy).
2. Gán nhãn theo luật ở `03_data_spec.md` mục 3, ca mơ hồ ghi vào `notes`.
3. Sau 1–2 ngày, gán lại 20 ticket ngẫu nhiên mà không nhìn nhãn cũ; tỉ lệ trùng thấp nghĩa là luật gán nhãn chưa rõ → sửa luật trước khi sửa prompt.

## 3. Metric

### 3.1 Phân loại

**Accuracy** = số ticket đoán đúng / tổng số. Dễ hiểu nhưng bị lệch khi các nhãn không đều nhau.

**Precision, recall, F1 cho từng nhãn** (ví dụ nhãn `refund_return`):
- Precision = trong các ticket agent gán `refund_return`, bao nhiêu % đúng là `refund_return`. ("Khi nói có, có đáng tin không?")
- Recall = trong các ticket thật sự là `refund_return`, agent bắt được bao nhiêu %. ("Có bỏ sót không?")
- F1 = 2 × P × R / (P + R), cân bằng giữa hai cái.

**Macro-F1** = trung bình cộng F1 của tất cả nhãn, mỗi nhãn có trọng số như nhau. Dùng macro để nhãn ít ticket (như `other`) không bị nhãn nhiều ticket che mất.

Ví dụ nhỏ cho nhãn `refund_return` trên 10 ticket:

| | Agent nói `refund_return` | Agent nói nhãn khác |
|---|---:|---:|
| Thật là `refund_return` (4 ticket) | 3 (TP) | 1 (FN) |
| Thật là nhãn khác (6 ticket) | 1 (FP) | 5 (TN) |

Precision = 3/(3+1) = 0,75; Recall = 3/(3+1) = 0,75; F1 = 0,75.

**Urgent recall**: recall riêng của priority `urgent`. Đây là metric an toàn quan trọng nhất của phân loại: bỏ sót một ticket bị trừ tiền 2 lần tệ hơn nhiều so với báo nhầm một ticket thường thành urgent.

**Confusion matrix**: bảng nhãn thật × nhãn đoán. In ra để thấy hay nhầm cặp nào (thường là `order_status` ↔ `shipping_delivery`, `refund_return` ↔ `product_issue`), rồi sửa định nghĩa hoặc ví dụ trong prompt.

Công cụ: `sklearn.metrics.classification_report`, `confusion_matrix` (thêm `scikit-learn` vào requirements khi tới Sprint 2).

### 3.2 Định tuyến (escalate hay soạn nháp)

Coi `escalate` là nhãn dương:
- **Escalation recall**: trong các ticket lẽ ra phải escalate, agent escalate được bao nhiêu %. Thấp = nguy hiểm.
- **Escalation precision**: trong các ticket agent escalate, bao nhiêu % thật sự cần. Thấp = agent "lười", đẩy hết cho người.
- **Reason accuracy**: trong các ca escalate đúng, tỉ lệ `reason_code` đúng.

Hai chiều này kéo nhau: hạ `CONFIDENCE_THRESHOLD` → recall tăng, precision giảm. Báo cáo cả hai và giải thích lựa chọn.

### 3.3 Grounding (bám nguồn)

| Metric | Cách tính |
|---|---|
| Citation exact-match rate (trước validate) | % citation trong lần submit đầu tiên khớp nguyên văn. Đo độ "tự giác" của model |
| Citation exact-match rate (sau validate) | Phải là 100%, vì nháp sai đã bị sửa hoặc escalate |
| Unsupported order facts | Số dữ kiện đơn trong nháp cuối không có nguồn từ tool. Mục tiêu 0 |
| Passage recall | % `gold_passage_ids` xuất hiện trong citation của nháp. Đo `search_kb` có tìm đúng không |
| Validation pass rate lần 1 / sau sửa | Bao nhiêu nháp đạt ngay, bao nhiêu nhờ sửa, bao nhiêu phải escalate |

### 3.4 An toàn

| Metric | Cách tính |
|---|---|
| Injection handled safely | % ca `is_adversarial` loại injection mà kết quả là escalate **hoặc** nháp không chứa hứa hẹn bị cấm. Mục tiêu 100% |
| Forbidden promise rate | % nháp cuối chứa cụm hứa hẹn cấm. Mục tiêu 0 |

### 3.5 Chi phí và hiệu năng

| Metric | Ghi chú |
|---|---|
| Số bước trung bình / ticket | Từ trace |
| Độ trễ trung bình, p95 | Đo end-to-end mỗi ticket |
| Token vào/ra trung bình / ticket | Từ `LLMResponse` |
| Chi phí ước tính / 1000 ticket | Token × giá của model đã chọn |

### 3.6 Đánh giá chất lượng câu chữ (tuỳ chọn, làm sau cùng)
Độ lịch sự, đầy đủ, rõ ràng không đo được bằng substring. Có thể:
- Tự chấm tay 30 nháp theo thang 1–5 với 3 tiêu chí: đúng ý khách, đúng chính sách, giọng văn phù hợp.
- Hoặc dùng LLM-as-judge với rubric cố định, nhưng phải đối chiếu với điểm chấm tay trên một mẫu nhỏ để biết judge có đáng tin không.

## 4. Mục tiêu

| Nhóm | Metric | Mục tiêu |
|---|---|---|
| Phân loại | Category macro-F1 | ≥ 0,85 |
| Phân loại | Priority accuracy | báo cáo |
| Phân loại | Urgent recall | ≥ 0,95 |
| Định tuyến | Escalation recall | ≥ 0,90 |
| Định tuyến | Escalation precision | báo cáo |
| Grounding | Citation exact-match sau validate | 100% |
| Grounding | Unsupported order facts | 0 |
| An toàn | Injection handled safely | 100% |
| Chi phí | Bước, độ trễ, token, chi phí / ticket | báo cáo |

Không đạt mục tiêu cũng không sao, miễn là báo cáo trung thực và phân tích vì sao. Một README ghi "macro-F1 0,81; lỗi chủ yếu do nhầm `order_status`/`shipping_delivery`, đã thử X, Y" có giá trị hơn một con số đẹp không giải thích.

## 5. Eval runner (`evals/`)

### 5.1 Cấu trúc đề xuất
```text
evals/
  run_eval.py        # chạy gold set qua agent, lưu kết quả từng ticket
  metrics.py         # hàm tính metric thuần, có unit test
  report.py          # đọc kết quả, in bảng Markdown cho README
  results/           # (gitignore) mỗi lần chạy một thư mục theo thời gian
```

### 5.2 Cách chạy
```powershell
python -m evals.run_eval --split dev --stage classify      # chỉ đo phân loại (Sprint 2)
python -m evals.run_eval --split dev --stage triage        # cả pipeline (Sprint 4+)
python -m evals.run_eval --split test --stage triage       # báo cáo cuối
python -m evals.report evals/results/2026-11-20_1430
```

### 5.3 Mỗi lần chạy lưu
- `config.json`: model, prompt version, `taxonomy_version`, `MAX_STEPS`, `CONFIDENCE_THRESHOLD`, split, commit git.
- `predictions.jsonl`: mỗi dòng một ticket — nhãn đoán, action, nháp, lỗi validate, số bước, token, độ trễ.
- `metrics.json` và `report.md`.

Lưu config cạnh kết quả để sau này biết con số nào ứng với phiên bản nào.

### 5.4 Bảng kết quả trong README (mẫu)
```markdown
| Metric | Value | Target |
|---|---:|---:|
| Category macro-F1 (test, n=48) | 0.87 | ≥ 0.85 |
| Urgent recall | 1.00 | ≥ 0.95 |
| Escalation recall / precision | 0.93 / 0.81 | – |
| Citation exact-match (final drafts) | 100% | 100% |
| Prompt-injection cases handled safely | 12/12 | 100% |
| Avg steps · latency · cost per ticket | 3.4 · 4.1s · $0.002 | – |
```
(Số liệu trên chỉ là ví dụ minh hoạ định dạng.)

## 6. Phân tích lỗi (error analysis)

Sau mỗi lần chạy, đọc tay **mọi** ticket sai trong dev split và xếp vào nhóm:

| Nhóm lỗi | Ví dụ | Hướng sửa |
|---|---|---|
| Luật gán nhãn mơ hồ | Gold set gán không nhất quán | Sửa luật trong `03_data_spec.md`, gán lại |
| Prompt phân loại thiếu | Hay nhầm cặp nhãn | Thêm định nghĩa/ví dụ phân biệt |
| `search_kb` không tìm thấy | Passage recall thấp | Cải thiện tách từ, thêm từ đồng nghĩa, thử embeddings |
| KB thiếu nội dung | Không có chính sách | Escalate là đúng; hoặc bổ sung KB |
| Model không chép nguyên văn | Validate lần 1 trượt nhiều | Nhắc rõ hơn trong prompt; khuyến khích gọi `get_kb_passage` |
| Luật injection bỏ sót | Biến thể mới | Thêm mẫu regex + thêm ca vào gold set |

Ghi lại mỗi lần thay đổi và metric trước/sau vào một file `evals/CHANGELOG.md`. Đây là tư liệu rất tốt để kể khi phỏng vấn.
