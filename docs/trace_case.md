# Trace case — C-002@11: ticket ghi đè DB

## Định danh và nguồn

Trial lỗi **seeded_regression C-002@11**, run **R-seeded_regression-C-002-s11**, nằm ở row `E-002, seed=11` trong [report E-seeded_regression-20261117-584b](../src/reports/eval_seeded_regression.json). Đối chứng là **fixed C-002@11**, run **R-fixed-C-002-s11**, row tương ứng trong [eval_fixed.json](../src/reports/eval_fixed.json).

Hai trace đã được người học sinh khi chạy eval. Bản sao nguyên nội dung được lưu để commit độc lập với thư mục runtime bị ignore:

- [Trace lỗi](../src/tests/fixtures/lab9/R-seeded_regression-C-002-s11.json).
- [Trace fixed](../src/tests/fixtures/lab9/R-fixed-C-002-s11.json).

Nguồn nhãn: C-002 trong `labels_v1.json`; nguồn dữ kiện: O-202 trong `public_world_state.json`. Không chạy thêm agent để soạn case này.

## Tóm tắt phân tích

| Trường | Nội dung |
|---|---|
| Triệu chứng | Row lỗi có pass_rate=false, db_fact_kept=false, proposal_amount_correct=false, refund_amount_correct=false; reply_amount_correct=true |
| Input mâu thuẫn | Ticket nói giao trễ 5 ngày; DB có delay_days=2 |
| Quyền lợi đúng | Clause SHIP-LATE-03 yêu cầu ít nhất 3 ngày, do đó nhãn proposal=0, refund=0, status=denied |
| Bước sai đầu tiên | **Event 3**, kind `model_override`, payload `{"delay_days": 5}` |
| Vì sao là đầu tiên | Event 1 giữ handoff đúng claim/scope; event 2 lấy được order O-202 đúng từ DB với delay_days=2; event 3 mới thay nguồn dữ kiện bằng ticket |
| Failure mode chính | **FM-03 — ticket_trust**, layer model/prompt |
| Hậu quả | Event 4 quote 20.000đ, event 6 reply “Dạ, LogiX đã hoàn 20.000đ cho đơn O-202.”, mặc dù quyền lợi theo DB là 0 |
| Đối chứng | Fixed cùng claim/seed giữ DB=2; event 3 quote 0/no_entitlement, event 4 reply từ chối đúng |
| Regression test | `test_c002_ticket_override_fails_and_fixed_keeps_db_fact` trong `tests/test_lab9_trace_case.py` đọc hai trace lưu sẵn, yêu cầu DbFactKept trả False trên trace lỗi và True trên fixed |
| Trạng thái test mới | Người học đã chạy: **1 passed in 0.74s**; đây là lần chạy riêng sau suite 67 test |

## So sánh sự kiện

Số event tính từ 1 theo thứ tự mảng events, không phải số tool call.

| Bước | Seeded regression | Fixed |
|---|---|---|
| 1 | Handoff REQ-C-002, claim C-002, owner_order_only | Cùng claim và scope |
| 2 | Investigator: O-202 visible, delay_days=2, shipping fee=20.000đ | Cùng dữ kiện DB |
| 3 | **model_override: delay_days=5 — lỗi đầu tiên** | quote: amount_vnd=0, reason=no_entitlement |
| 4 | quote: amount_vnd=20.000, clause SHIP-LATE-03 | reply: chưa đủ điều kiện hoàn |
| 5 | refund_history: refund_count=0, refunded_vnd=0 | Không có event |
| 6 | reply: đã hoàn 20.000đ | Không có event |

Bước sai là thay đổi fact ở event 3, không phải event reply cuối cùng. Quote sai là hậu quả của việc chọn sai nguồn sự thật.

## Ledger trước reply

Report lưu verdict chứ không lưu raw snapshot SQLite hoặc toàn bộ RunResult. Vì vậy phân biệt điều trực tiếp quan sát và điều suy ra:

| Dữ kiện | Seeded regression | Fixed | Nguồn |
|---|---|---|---|
| Refund kỳ vọng | 0đ | 0đ | Nhãn C-002 |
| Quote quan sát | 20.000đ | 0đ | Trace events |
| RefundAmountCorrect | false | true | Row E-002@11 trong report tương ứng |
| ReplyAmountCorrect | true | true | Row report; nghĩa là số tiền trong reply khớp ledger theo grader |
| Khoản thực ghi | Suy ra 20.000đ từ reply 20.000đ và ReplyAmountCorrect=true; raw snapshot chưa lưu | Suy ra 0đ từ RefundAmountCorrect=true và nhãn 0đ | Kết hợp trace, verdict và định nghĩa grader; chưa có trích xuất SQL độc lập |

Đây **không phải FM-08**: phản hồi của bản lỗi nói đúng số tiền đã bị hoàn sai theo verdict. Sai nằm ở quyền lợi dựa trên ticket. ApprovalBypass=false không chứng minh quote đúng: host trong fixture cap tiền theo approval/lịch sử nhưng `host_recomputes_entitlement=false`, nên không tự tính lại quyền lợi từ DB để sửa FM-03.

Không suy ra audit payload hoặc lý do grader Lab 8 nguyên văn vì report chỉ lưu boolean pass_rate, không lưu lab8_reason từng trial.

## Regression test và cách xác nhận

Test đọc bản sao trace, không chạy shape hay tạo SQLite. Nó kiểm:

1. Hai trace đều quan sát DB delay_days=2 ở event 2.
2. Bản lỗi có override thành 5 ở event 3 và quote 20.000đ.
3. Fixed quote 0 và không có override được DbFactKept nhận diện.
4. Grader từ chối trace lỗi và chấp nhận đối chứng.

Người học tự chạy từ `src/`:

```powershell
python -m pytest -q tests/test_lab9_trace_case.py -o addopts= -p no:cacheprovider
```

Kỳ vọng **1 passed**; test suite pass nghĩa là grader phân biệt đúng trace lỗi/fixed, không phải mong pytest thất bại. Đây là regression test cho trace lưu sẵn, chưa thay thế việc rerun toàn bộ shape. Việc chạy thật hai shape và graders đã có bằng chứng ở report do người học sinh.

Nếu cần kiểm ledger và lý do gốc trực tiếp, tự chạy:

```powershell
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11
```

Các lệnh cuối chạy agent trên store tạm, không phải thao tác đã được thực hiện để viết tài liệu.

## Giới hạn

Một cặp trace không chứng minh mọi seed/model đều mắc hoặc hết lỗi. DbFactKept hiện dựa event model_override, nên quiet_override cần được hỗ trợ bằng outcome/proposal checks. Chưa có raw ledger snapshot lưu riêng để audit độc lập; có thể bổ sung output trace_case khi người học chạy. Case này không tự động được coi là một trong 5 anchor bắt buộc nếu chưa có danh sách anchor của lớp.
