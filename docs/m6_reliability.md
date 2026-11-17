# M6 — Nhiễu A/A, pass@k và pass^k

## Trạng thái

Người học đã tự chạy: **28 test passed, 3 deselected**, A/A tất cả delta=0, baseline spec 2.1 so chính nó exit 0. Flaky regression đã bị chặn có pass_hat_5. Floor **0.85 đã được đối chiếu với hai seed set MockLLM** (cùng pass_hat_5=0.8929); không suy ra nhiễu LLM thật bằng 0. Người học cũng xác nhận fixed/honest_refactor exit 0 và slice_regression vẫn bị chặn ở money_movement với spec 2.1. M6 đã đạt các kiểm tra public này; M7 và CI nâng cao toàn bộ chưa được xác nhận.

## Kết quả đã nhận

| Metric | Swarm seed gốc | Swarm seed A/A | Delta A/A | Flaky regression |
|---|---:|---:|---:|---:|
| pass_rate / pass_at_1 / pass_hat_1 | 0.9786 | 0.9786 | 0.0000 | 0.9143 |
| pass_at_3 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| pass_hat_3 | 0.9357 | 0.9357 | 0.0000 | 0.7429 |
| pass_at_5 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| pass_hat_5 | 0.8929 | 0.8929 | 0.0000 | **0.5714** |

Nguồn flaky: report E-flaky_regression-20261117-c26e, SHA c26ebe1e1abb, spec 2.1, evaluator_failures rỗng. Baseline cùng SHA/spec có pass_hat_5=0.8929. Gate người học gửi:

```text
exit 1 — blocked: pass_rate, pass_hat_5, proposal_amount_correct, slice:money_movement/pass_rate
```

Pass rate flaky 0.9143 vẫn trên floor 0.85; vì vậy gate pass_rate bị chặn bởi no_significant_drop, không phải floor. Chưa có số CI chi tiết được gửi nên không tự điền CI. Pass_hat_5 0.5714 trực tiếp thấp hơn floor 0.85; pass@5=1 vẫn che lỗi thiếu ổn định, minh họa sự khác biệt hai estimator.

Metric spec v2 tăng từ **2.0 lên 2.1** để ghi nhận metric mới. Eval-set version/SHA vẫn là v2 / **c26ebe1e1abb**; không đổi item hoặc nhãn. Khi code/metric hoàn thiện, phải chạy script sinh lại baseline v2 và các report candidate để có pass_at/pass_hat thật, không thay các giá trị null trong report bằng tay.

## Ý nghĩa hai estimator

Với n trial của cùng item, c trial pass, lấy k trial không hoàn lại:

| Metric | Công thức | Câu hỏi |
|---|---|---|
| pass@k | 1 − C(n−c,k)/C(n,k) | Ít nhất một trong k lần đạt không? |
| pass^k (pass_hat_k) | C(c,k)/C(n,k) | Cả k lần có cùng đạt không? |

Điều kiện n/c/k là số nguyên (không nhận bool), n≥1, 0≤c≤n, 1≤k≤n. Đối số sai raise ValueError ở cả hai hàm. Khi c<k, pass^k=0; khi không đủ trial fail để chọn k lần đều fail, pass@k=1. Code pass@k dùng log1p/expm1 để giữ chính xác khi xác suất thành công rất nhỏ; pass^k dùng tổ hợp nguyên rồi chia.

Luôn có pass^k ≤ pass@1 ≤ pass@k. Ví dụ 4/5 lần pass: pass@1=0.8, pass@5=1 nhưng pass^5=0. Với n=k=5, pass^5 của mỗi item là 1 chỉ khi cả 5 trial đạt; số tổng hợp là tỷ lệ item đạt cả 5 lần. Không dùng pass_rate trung bình thay cho độ ổn định này.

Harness lấy estimator từng item rồi trung bình trên item. Nếu một item có ít hơn k trial, estimator k tương ứng chưa xác định. Với LLM thật cần giữ cùng quy trình lấy mẫu và nhãn; retry đến khi pass rồi bỏ các lần fail sẽ làm sai độ tin cậy.

## Thiết kế ngưỡng và A/A

Spec seeds: **11,22,33,44,55**. Bộ A/A thứ hai: **66,77,88,99,110**. Cùng shape swarm, cùng eval set, cùng spec/grader; chỉ thay seed.

MockLLM của lab có cơ chế lỗi định sẵn: mỗi bộ seed này có một seed chia hết cho 5 nên dự kiến các metric chất lượng giống nhau. M5 baseline có 25/28 item pass cả 5 seed, nên mức pass_hat_5 dự kiến **0.8929**. Floor đề xuất **0.85** cách mức đó khoảng 0.0429, cần kiểm bằng A/A để xác nhận biên không bị nhiễu vượt qua. Đây là suy ra từ cấu trúc trial M5, không phải số đo A/A đã chạy.

Đối chiếu tối thiểu pass_rate, pass_at_1/3/5 và pass_hat_1/3/5. Nếu pass_hat_5 hai bộ seed đều 0.8929 và delta 0, mức 0.85 nằm dưới cả hai mức quan sát, có margin. Nếu dữ liệu thực tế khác, dừng xác nhận và phân tích; không tự nới ngưỡng để ép gate qua.

A/A trên hai bộ seed chỉ là bằng chứng ban đầu. LLM thật có sampling, tool/network noise và thay đổi mô hình; dải nhiễu có thể >0, nên cần nhiều lần A/A hoặc khoảng bất định và đủ item để chọn margin. Delta 0 trên MockLLM không chứng minh nhiễu LLM thật bằng 0.

## Người học tự chạy từ src/, nhánh starter/d09

### 1. Test estimator và public vectors M6

```powershell
python -m pytest -q tests/test_lab9_advanced_m6.py tests/test_lab9_advanced.py -o addopts= -k "not integrity and not slice" -p no:cacheprovider
```

Chỉ loại các test M7 và slice đã kiểm M5; không yêu cầu thư mục tạm.

### 2. Đo A/A trước khi xác nhận ngưỡng

```powershell
python -m lab9.mutation --spec config/metric_spec_v2.yaml --aa 66,77,88,99,110
```

Gửi toàn bộ bảng metric hai seed set và delta, đặc biệt pass_hat_5. Không đưa report hai bộ seed khác nhau vào PR gate như hai phiên bản; A/A ở đây là khảo sát nhiễu, không phải so regression cùng cặp trial.

### 3. Sau khi A/A xác nhận floor, sinh lại baseline spec 2.1

```powershell
python -m lab9.eval --shape swarm --spec config/metric_spec_v2.yaml --out reports/baseline_v2.json
python -m lab9.gate --pr reports/baseline_v2.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
```

Kỳ vọng metric pass_at/pass_hat không còn null và baseline gate exit 0. Không sửa tay report M5; script ghi report mới khi chạy.

### 4. Kiểm flaky_regression

```powershell
python -m lab9.eval --shape flaky_regression --spec config/metric_spec_v2.yaml --out reports/eval_flaky_regression.json
python -m lab9.gate --pr reports/eval_flaky_regression.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
```

Kỳ vọng exit 1 có **pass_hat_5** trong danh sách chặn; pass_rate tổng vẫn có thể trên floor 0.85. Slice tiền có thể cũng chặn, không yêu cầu chỉ riêng pass_hat_5 chặn. Gửi output đầy đủ để xác nhận số đo.

### 5. Kiểm không báo nhầm và bảo toàn M5

```powershell
python -m lab9.eval --shape fixed --spec config/metric_spec_v2.yaml --out reports/eval_fixed_v2.json
python -m lab9.gate --pr reports/eval_fixed_v2.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
python -m lab9.eval --shape honest_refactor --spec config/metric_spec_v2.yaml --out reports/eval_honest_refactor_v2.json
python -m lab9.gate --pr reports/eval_honest_refactor_v2.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
python -m lab9.eval --shape slice_regression --spec config/metric_spec_v2.yaml --out reports/eval_slice_regression.json
python -m lab9.gate --pr reports/eval_slice_regression.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
```

Fixed/honest_refactor phải exit 0; slice_regression vẫn phải bị chặn ở money_movement. Sau khi nhận output mới mới cập nhật eval card là kết quả spec 2.1; các số M5 cũ vẫn là bằng chứng lịch sử spec 2.0.

## Phạm vi còn lại

M7 integrity/ratchet/traps chưa làm. Chưa force-add baseline_v2 để bật workflow nâng cao toàn bộ khi M7 vẫn TODO; có thể kiểm đầy đủ M6 local theo các lệnh trên. Giữ log A/A để đưa vào mô tả PR khi nộp Advanced/Expert.
