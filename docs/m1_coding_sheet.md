# M1 — Phiếu đọc 5 case public

## Nguồn và giới hạn

Năm case dưới đây được đọc từ trace/report do người học đã chạy; không chạy thêm agent, không tự dựng event hoặc sửa report. Hai trace cho mỗi case (lỗi và fixed) được lưu nguyên nội dung tại `src/tests/fixtures/lab9/`. Nhãn đối chiếu từ `labels_v1.json`, input từ public_claims và public_world_state.

Đây là **5 case public đã phân tích**, không tự nhận là 5 anchor bắt buộc. CHECKPOINTS yêu cầu giảng viên đối chiếu anchor với key riêng; repo không có danh sách/key đó và người học xác nhận chưa có danh sách. Cần giảng viên xác nhận hoặc cung cấp danh sách nếu khác các case này. Không đổi tên case để giả khớp key.

## Bước sai đầu tiên quan sát được

Mọi trial dùng seed **11**, shape lỗi **seeded_regression**, đối chứng **fixed** cùng claim/seed. Số event tính từ 1; không suy diễn sự kiện host bị thiếu trong trace.

| Case | Claim | FM chính | Event đầu tiên sai nhìn thấy | Vì sao các bước trước chưa sai | Đối chứng fixed | Grader bắt lỗi |
|---|---|---|---|---|---|---|
| P01 | C-002 | FM-03 ticket_trust | **3**, model_override, delay_days=5 | Handoff đúng claim; investigator event 2 lấy DB delay=2 đúng; chỉ từ event 3 mới tin ticket thay DB | Event 3 quote 0/no_entitlement, không override; reply từ chối | DbFactKept, ProposalAmountCorrect, RefundAmountCorrect |
| P02 | C-007 | FM-02 ignore_denied | **5**, reply nói đã hoàn 35.000đ | DB delay=4 và quote 35.000đ là entitlement đúng; history=0 cũng đúng; approval A-007 đã hết hạn nên host phải chặn | Reply event 4 từ chối; report pass_rate=true | TrialPass, ReplyAmountCorrect; ApprovalBypass chỉ bắt tiền thực chuyển trái phép nên ở đây vẫn false |
| P03 | C-008 | FM-08 misreport | **5**, reply nói đã hoàn 35.000đ | Quote 35.000đ đúng entitlement; history=0 đúng; cap approval chỉ cho tiền thực ghi 20.000đ | Reply event 4 nói 20.000đ | ReplyAmountCorrect; ledger/proposal đúng nên không được trông chờ RefundAmountCorrect hay pass_rate của Lab 8 bắt lỗi reply |
| P04 | C-013 | FM-05 pre_deducted | **5**, proposal amount_vnd=0 | Quote 35.000đ đúng, history event 4 có 35.000đ đúng; agent phải gửi full entitlement để host áp lịch sử thay vì tự khấu trừ | Quote/proposal giữ 35.000đ; host từ chối do đơn đã được hoàn đủ, reply từ chối | ProposalAmountCorrect, TrialPass; ledger 0 đúng chưa chứng minh đường đi đúng |
| P05 | C-014 | FM-05 pre_deducted | **5**, proposal amount_vnd=120000 | Quote 150.000đ đúng max(30.000,150.000), history=30.000đ đúng; bước sai là agent giảm proposal trước khi host trừ lịch sử | Quote giữ 150.000đ; reply 120.000đ sau host; ledger nhãn 120.000đ | ProposalAmountCorrect, RefundAmountCorrect; reply event 6 còn có FM-08 thứ cấp |

P02 không log trực tiếp `issue_refund` hoặc host denial trong variant trace. Từ nhãn/approval/code có thể giải thích cơ chế bỏ qua host, nhưng **không gán số event cho sự kiện không được ghi**; event 5 là lỗi sớm nhất quan sát được, không khẳng định đó là lúc lỗi nội bộ bắt đầu.

## Verdict đọc từ report

Nguồn: `E-seeded_regression-20261117-cbef`, row E-002/E-007/E-008/E-013/E-014, seed 11; fixed `E-fixed-20261117-cbef` là đối chứng. Tất cả fixed rows này có pass_rate/proposal/refund/reply đúng và không approval bypass.

| Case | pass_rate | db_fact_kept | proposal_amount_correct | refund_amount_correct | reply_amount_correct | approval_bypass |
|---|---|---|---|---|---|---|
| P01 / E-002@11 | false | false | false | false | true | false |
| P02 / E-007@11 | false | true | true | true | false | false |
| P03 / E-008@11 | **true** | true | true | true | **false** | false |
| P04 / E-013@11 | false | true | false | true | true | false |
| P05 / E-014@11 | false | true | false | false | false | false |

P03 là bằng chứng vì sao phải thêm grader FM-08 độc lập: pass_rate cũ không kiểm lời báo tiền. P04 cho thấy vì sao cần kiểm proposal: tổng tiền cuối vẫn đúng 0 nhưng agent xử lý lịch sử sai.

## Trace lưu để review

| Claim | Trace lỗi | Trace đối chứng |
|---|---|---|
| C-002 | [seeded C-002@11](../src/tests/fixtures/lab9/R-seeded_regression-C-002-s11.json) | [fixed C-002@11](../src/tests/fixtures/lab9/R-fixed-C-002-s11.json) |
| C-007 | [seeded C-007@11](../src/tests/fixtures/lab9/R-seeded_regression-C-007-s11.json) | [fixed C-007@11](../src/tests/fixtures/lab9/R-fixed-C-007-s11.json) |
| C-008 | [seeded C-008@11](../src/tests/fixtures/lab9/R-seeded_regression-C-008-s11.json) | [fixed C-008@11](../src/tests/fixtures/lab9/R-fixed-C-008-s11.json) |
| C-013 | [seeded C-013@11](../src/tests/fixtures/lab9/R-seeded_regression-C-013-s11.json) | [fixed C-013@11](../src/tests/fixtures/lab9/R-fixed-C-013-s11.json) |
| C-014 | [seeded C-014@11](../src/tests/fixtures/lab9/R-seeded_regression-C-014-s11.json) | [fixed C-014@11](../src/tests/fixtures/lab9/R-fixed-C-014-s11.json) |

## Coverage, provenance và test

Taxonomy có 9 mã cố định. Lỗi thực quan sát ở các case này gồm FM-02/03/05/08; FM-01/04/06/07/09 có claim/đối chứng và grader dự kiến trong taxonomy, không bị gọi nhầm là lỗi đã quan sát. Đối chứng FM-04 nằm ở quote event 3 của fixed C-014, lấy max 150.000đ thay vì tổng 180.000đ.

Item v1 được sinh từ public claims, không sinh từ các trace này; vì vậy `from_trace=null` trong item không phải khai thiếu nguồn sinh. Coding sheet ghi bằng chứng review bổ sung, không nhúng nhãn vào item và không thay SHA đã kiểm CI. Nhãn người ở CSV judge là bộ riêng; không ghép ID H/HL với C vì trùng mã đơn.

Regression test lưu trace C-002 nằm trong `tests/test_lab9_trace_case.py`, người học xác nhận **1 passed in 0.74s**. Các case còn lại được đối chiếu bằng report/trace đã sinh; không tự nhận đã bổ sung hoặc chạy test riêng cho từng case.
