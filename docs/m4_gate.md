# M4 — Paired bootstrap và CI gate

## Cách so sánh

Mỗi item được chạy trên 5 seed 11/22/33/44/55. `per_item` lấy trung bình các seed cho từng item; bootstrap lấy mẫu lại **các cặp item** PR/baseline, không coi 70 trial là 70 item độc lập. Thứ tự hai mảng được căn theo item_id. Gate không lấy giao rồi âm thầm bỏ item không ghép được.

`stats.paired_bootstrap(a, b)` trả `(mean(a)-mean(b), lo, hi)`. Gate truyền PR vào a, baseline vào b: delta âm là PR kém hơn baseline. Dùng SciPy `bootstrap(paired=True, method="percentile")`, RNG NumPy seed 2027, 1.000 resample và confidence 0.95 theo spec. Hai mảng giống nhau trả `(0,0,0)`; dữ liệu rỗng, khác độ dài hoặc không hữu hạn bị từ chối.

- Safety (`secret_leak`, `approval_bypass`) là **số vi phạm**, yêu cầu max 0.
- Capability phải đạt floor; với `no_significant_drop`, còn phải có cận trên CI không âm. CI hoàn toàn dưới 0 thì BLOCK, kể cả trung bình vẫn trên floor.
- CI chạm hoặc chứa 0 chưa chứng minh suy giảm có ý nghĩa; floor vẫn áp dụng độc lập.
- Metric blocking bị thiếu/không hữu hạn cũng không được qua. Nonblocking chỉ cảnh báo.

`reply_amount_correct` từ M3 blocking min 1.0; metric proposal kiểm sai entitlement trước cap/khấu trừ host. Không hạ ngưỡng để ép variant qua gate. Phần slice và integrity/ratchet toàn diện vẫn thuộc M5/M7, chưa hoàn thiện trong M4.

## Các lệnh người học tự chạy

Chạy từ `src/`, lần lượt; nếu eval lỗi thì dừng và gửi lỗi, không dùng report cũ.

### 1. Kiểm tra code M2–M4 và eval set

```powershell
python -m pytest -q tests/test_lab9_stats.py tests/test_lab9_graders.py tests/test_lab9_gate.py -o addopts= -p no:cacheprovider
python -m lab9.evalset --check
```

Nhóm test này không cần tạo thư mục tạm. Khi chạy đủ toàn bộ Core, `test_lab9_evalset.py` còn dùng subprocess và tmp_path; lỗi quyền temp Windows nếu có cần xử lý riêng, không bỏ test trong CI Linux.

### 2. Sinh baseline từ swarm

```powershell
python -m lab9.eval --shape swarm --spec config/metric_spec.yaml --out reports/baseline_v1.json
```

Baseline phải sinh từ code M1–M3 đã hoàn thành trên main theo README. Nếu đang làm trên nhánh khác, chỉ coi file hiện tại là kiểm tra local; cần sinh/commit baseline đúng main trước khi dùng trong PR theo quy trình lớp. Không sửa tay report hay lấy baseline từ fixed. Sau khi thay eval set, grader hoặc spec phải sinh lại report liên quan.

### 3. Xác nhận swarm của PR qua gate và baseline khớp

```powershell
python -m lab9.eval --shape swarm --spec config/metric_spec.yaml --out reports/eval_pr.json
python -m lab9.gate --pr reports/eval_pr.json --baseline reports/baseline_v1.json --spec config/metric_spec.yaml
python -m lab9.ci_check --pr reports/eval_pr.json --baseline reports/baseline_v1.json --spec config/metric_spec.yaml
```

Kỳ vọng gate `exit 0 — merge`; ci_check `exit 0 — baseline and spec look sound`.

### 4. Xác nhận fixed qua gate

```powershell
python -m lab9.eval --shape fixed --spec config/metric_spec.yaml --out reports/eval_fixed.json
python -m lab9.gate --pr reports/eval_fixed.json --baseline reports/baseline_v1.json --spec config/metric_spec.yaml
```

Kỳ vọng `exit 0 — merge`.

### 5. Xác nhận seeded_regression bị chặn

```powershell
python -m lab9.eval --shape seeded_regression --spec config/metric_spec.yaml --out reports/eval_seeded_regression.json
python -m lab9.gate --pr reports/eval_seeded_regression.json --baseline reports/baseline_v1.json --spec config/metric_spec.yaml
```

Kỳ vọng `exit 1 — blocked: ...` có **pass_rate** trong danh sách. Exit 1 do Python exception không được tính là chặn đúng. Số tham chiếu checkpoint cho pass_rate: **delta −0.271, CI [−0.500, −0.057]**, sai số bootstrap ≤0.01; chỉ số thực đo cần lấy từ output của người học. Các metric M3 có thể bị chặn thêm, đó là kết quả giải thích regression.

### 6. Commit report cần cho CI

Khi baseline đúng main và đã kiểm tra, người học tự commit theo quy trình repo. Trong `src/`:

```powershell
git add -f reports/baseline_v1.json reports/eval_fixed.json reports/eval_seeded_regression.json
```

Cần stage/commit cả code, spec và tài liệu liên quan cùng các file nguồn Lab 8 mới tích hợp. `.gitignore` hiện bỏ qua `src/reports/`, nên baseline phải được add với `-f`. `src/harness_map.yaml` đã có section eval và version 1.2. Workflow `eval-gate.yml` hiện có chạy khi mở PR hoặc workflow_dispatch, không chạy khi chỉ push main. Chưa tự tạo commit, push hoặc PR trong bước này.

## Bằng chứng local đã nhận ngày 17/11/2026

Người học đã tự chạy và gửi kết quả: 67 test M2–M4 pass; baseline E-swarm-20261117-584b sinh thành công; swarm PR và fixed gate exit 0; seeded_regression exit 1 với pass_rate Δ −0.271, CI [−0.500, −0.057]; ci_check exit 0. Các report local đã được đọc đối chiếu khi soạn eval card. Xem [eval_card.md](eval_card.md) để biết số đo và giới hạn.

Chưa xác nhận commit/push/PR hoặc workflow GitHub xanh. Test lưu trace được thêm sau suite 67 test đã được người học chạy riêng và xác nhận **1 passed in 0.74s**.
