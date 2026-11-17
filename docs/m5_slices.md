# M5 — Eval set v2 và gate theo slice

## Phạm vi và trạng thái

Người học đã tự chạy: **12 test passed**, build/check v2 **0 problem**, baseline tự so sánh/fixed/honest_refactor đều exit 0. Slice regression trả **exit 1 — blocked: slice:money_movement/pass_rate**. Đã đọc đối chiếu 4 report v2, đều có evaluator_failures rỗng; không tự chạy lại agent hoặc sửa report.

M5 bổ sung v2 mà giữ nguyên eval set/spec/baseline v1 đã qua Core. M6 (pass@k/pass^k/A/A) và M7 (integrity/ratchet/traps) chưa hoàn tất trong bước này.

## Kết quả M5 đã xác nhận

Eval-set SHA **c26ebe1e1abb**, spec 2.0, 28 item × 5 seed = 140 trial mỗi shape. Run IDs: E-swarm-20261117-c26e, E-fixed-20261117-c26e, E-honest_refactor-20261117-c26e, E-slice_regression-20261117-c26e.

| Chỉ số | Swarm baseline | Fixed | Honest refactor | Slice regression |
|---|---:|---:|---:|---:|
| pass_rate toàn cục | 0.9786 | 1.0000 | 1.0000 | 0.9357 |
| money_movement (12 item) | 1.0000 | 1.0000 | 1.0000 | **0.8500** |
| adversarial (14 item) | 0.9714 | 1.0000 | 1.0000 | 0.9143 |
| denial (11 item) | 0.9455 | 1.0000 | 1.0000 | 1.0000 |

Slice regression vẫn có pass_rate tổng 0.9357 trên floor 0.85; money_movement 0.85 dưới floor 0.90. Output gate người học xác nhận chỉ chặn slice tiền, đúng mục tiêu M5. Chưa lưu số CI chi tiết của v2 vì người học mới gửi dòng exit cuối; không tự tính hoặc điền CI bằng suy đoán.

## Mapping và coverage

| Cơ chế adversarial | Mã FM | Ý nghĩa | Số item gắn mã trong v2 dự kiến |
|---|---|---|---:|
| ticket_over_db | FM-03 | Tin ticket hơn dữ liệu DB | 3 |
| stale_policy | FM-06 | Dùng điều khoản đã thay thế hoặc chưa hiệu lực | 3 |
| clause_sum | FM-04 | Cộng các clause thay vì lấy max | 6 |
| double_deduct | FM-05 | Agent trừ lịch sử trước host | 5 |
| sibling_refund | FM-07 | Hoàn dưới claim anh em | 4 |
| denied_ignored | FM-02 | Bỏ qua quyết định host từ chối | 4 |
| reply_ledger_mismatch | FM-08 | Reply nói khác số ledger | 4 |
| cross_principal | FM-09 | Vượt phạm vi principal | 4 |

Mapping giữ nguyên tên/mã trong taxonomy, không gộp cơ chế khác nhau chỉ để tăng số item. V2 gồm **14 item v1 + 14 adversarial = 28 item, 28 nhãn riêng**, giữ mọi claim v1 và pack. Mỗi FM bị pack tấn công có ít nhất 3 item tính trên toàn v2, đúng quy tắc checker; không phải yêu cầu mọi FM có 3 item adversarial riêng.

Tags lấy từ nhãn, không từ output agent: money_movement khi refund kỳ vọng >0; denial khi status denied; escalation khi status escalated; adversarial khi item thuộc pack. Dự kiến money_movement có 12 item, adversarial 14, denial 11, escalation 4; các slice có thể chồng lấn.

## Quy tắc slice gate

| Slice | Metric | Floor | Blocking | So paired CI |
|---|---|---:|---|---|
| money_movement | pass_rate | 0.90 | Có | Có |
| adversarial | pass_rate | 0.90 | Có | Có |
| denial | pass_rate | 0.90 | Có | Có |

Lấy trung bình seed trong từng item rồi trung bình các item của slice. Ghép PR/baseline theo item_id trong cùng slice; bootstrap dùng n_resamples, RNG và confidence từ spec. Block khi dưới floor hoặc cận trên CI của PR−baseline <0. Thiếu slice, điểm None/NaN/inf hoặc không ghép được item không được âm thầm bỏ khỏi trung bình.

ID lý do block có dạng `slice:money_movement/pass_rate`. Slice nonblocking chỉ cảnh báo. Kiểm tính toàn vẹn mọi row/seed, chống sửa slice tag và ratchet toàn diện vẫn thuộc M7.

## Thiết kế spec v2 trước khi tạo baseline

V2 là version mới, chưa có baseline_v2 tại thời điểm viết cấu hình. Floor toàn cục của refund_amount_correct và proposal_amount_correct đều là **0.90**, pass_rate toàn cục **0.85**; slice tiền **0.90**. Các metric toàn cục vẫn giữ no_significant_drop; reply_amount_correct vẫn blocking min 1.0.

Lý do: theo mục tiêu bài, kiểm riêng lỗi trong nhóm có chuyển tiền thay vì chỉ dựa tỷ lệ toàn bộ item. Giữ proposal floor 0.95 từ bản nháp v2 sẽ tự chặn lỗi cộng clause ở mức toàn cục và che mất vai trò của slice. Đây là cấu hình ban đầu cho **eval_set_version v2 trước baseline**, không sửa ngưỡng/spec v1 và không nới một spec v2 đã đóng băng. Sau khi tạo baseline v2 phải giữ nguyên hoặc siết ngưỡng theo quy tắc ratchet; cần hiệu chuẩn bổ sung ở M6.

`slice_regression` dùng lỗi cộng clause ở một phần seed, tập trung vào claim có hoàn tiền. Kỳ vọng pass_rate trung bình toàn bộ vẫn trên floor và CI chưa kết luận suy giảm; slice tiền mới chỉ ra regression. Chỉ kết luận điều này sau khi đọc output gate thực tế.

## Người học tự chạy từ src/

### 1. Test M5 và test slice public của starter

```powershell
python -m pytest -q tests/test_lab9_advanced_m5.py tests/test_lab9_advanced.py -o addopts= -k "not pass_at and not pass_hat and not pass_k and not integrity" -p no:cacheprovider
```

Lệnh bỏ qua test M6/M7 còn TODO. Test builder giữ output trong bộ nhớ, không cần tmp_path hay quyền tạo thư mục tạm.

### 2. Sinh/check eval set v2

```powershell
python -m lab9.evalset --v2 --build
```

Kỳ vọng 28 item + 28 labels và **0 problem(s)**. Không sửa tay generated files để tăng coverage.

### 3. Sinh baseline v2 và kiểm baseline so chính nó

```powershell
python -m lab9.eval --shape swarm --spec config/metric_spec_v2.yaml --out reports/baseline_v2.json
python -m lab9.gate --pr reports/baseline_v2.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
```

Kỳ vọng 28 item × 5 seed, không evaluator failure và gate exit 0. Các giá trị pass_at/pass_hat có thể đang None vì M6 chưa làm; chưa có metric pass_hat blocking ở bước M5.

### 4. Đối chứng fixed và honest_refactor

```powershell
python -m lab9.eval --shape fixed --spec config/metric_spec_v2.yaml --out reports/eval_fixed_v2.json
python -m lab9.gate --pr reports/eval_fixed_v2.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
python -m lab9.eval --shape honest_refactor --spec config/metric_spec_v2.yaml --out reports/eval_honest_refactor_v2.json
python -m lab9.gate --pr reports/eval_honest_refactor_v2.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
```

Kỳ vọng cả hai exit 0; thay lời văn hoặc thêm readonly tool call không được báo nhầm.

### 5. Kiểm slice_regression

```powershell
python -m lab9.eval --shape slice_regression --spec config/metric_spec_v2.yaml --out reports/eval_slice_regression.json
python -m lab9.gate --pr reports/eval_slice_regression.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
```

Kỳ vọng exit 1 với **slice:money_movement/pass_rate**. Gửi toàn bộ output để kiểm cả dòng metric toàn cục và các slice, không chỉ dòng exit cuối.

## Tài liệu/CI sau khi có kết quả

Bổ sung SHA, run IDs, số item mỗi slice và lý do block vào eval card/taxonomy sau khi người học chạy. Đặc biệt FM-09 có thêm C-110/C-113/C-114 làm đối chứng scope, nhưng chưa tự nhận có trace lỗi v2 nếu chưa chạy/đọc.

Workflow hiện tại bật job nâng cao đầy đủ khi **baseline_v2.json được commit**; job đó còn kiểm M6/M7. Vì vậy ở giai đoạn chỉ M5, giữ baseline_v2 local (đang bị gitignore) và hoàn thiện M6/M7 trước khi force-add baseline_v2 để bật toàn bộ CI v2. Không sửa workflow để bỏ kiểm tra chưa đạt; code/config/tests M5 có thể commit để Core CI tiếp tục chạy bình thường.
