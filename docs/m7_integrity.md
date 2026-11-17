# M7 — Integrity, ratchet và mutation scorecard

## Trạng thái

Người học đã tự chạy và xác nhận: **73 test Advanced passed, 399 deselected**, baseline so chính nó exit 0, cả 4 trap public bị chặn, mutation score **3/3 · false alarms 0**. Đây là kết quả kiểm tra local; còn kiểm lại Core, commit/push baseline_v2 và xác nhận CI nâng cao xanh. Không tự suy ra kết quả hidden tests.

## Kiểm tra tính toàn vẹn

Gate kiểm cả PR và baseline trước khi so chất lượng:

- Metric phải hữu hạn; metric blocking không được thiếu/None.
- Manifest có số item dương và seed hợp lệ, không trùng seed; số row đúng items × số seed.
- Mỗi cặp item_id/seed xuất hiện đúng một lần; không được bỏ item/seed rồi sửa manifest để che mất.
- PR và baseline có cùng tập item/seed; khi spec khai seed, manifest phải khớp spec.
- evaluator_failures phải là danh sách rỗng, kể cả khi tất cả metric hiển thị xanh.
- Điểm row cho grader trong spec/summary phải hữu hạn trong [0,1], không bỏ None khỏi trung bình; cost cần thiết phải hữu hạn và không âm.
- Tags slice của một item nhất quán qua seed và không thay so baseline.
- Tính lại metric đã báo từ rows, gồm safety counts, trung bình, pass@k/pass^k và cost_per_success; sửa riêng số tổng hợp bị từ chối.
- Không nhận metric/slice ID trùng hoặc threshold NaN/inf.

Vi phạm trả `INTEGRITY ...` và `exit 1 — blocked: integrity`. Đây khác regression hợp lệ bị chặn ở metric chất lượng. Không sửa variant/trap để qua bài.

## Ratchet

Với cùng eval_set_version, khi truyền base_spec:

- Không bỏ metric/slice cũ, bỏ blocking hoặc bỏ no_significant_drop.
- Không hạ min, tăng max hoặc tăng max_increase; không bỏ bound đang có.
- Không đổi grader/kind/level của metric cũ để thay thước đo âm thầm.
- Slice được ghép bằng cặp name/metric, nên đổi metric của slice cũng là bỏ rule cũ.

Đã lưu bản spec **2.1** hiện tại thành `config/metric_spec_v2.baseline.yaml` để đối chiếu. Đây là snapshot cấu hình đã chọn ở M6, không phải report tự dựng. Người học/reviewer cần giữ snapshot được tin cậy: khi dùng thật, lấy base_spec từ nhánh main được bảo vệ. Nếu người sửa được cả spec hiện tại lẫn snapshot hoặc baseline, kiểm tra hai bản tự khai không chứng minh được tính toàn vẹn nguồn gốc. Không cập nhật snapshot chỉ để làm một PR lỗi qua gate.

Thêm metric chặt hơn vẫn được phép; đổi eval-set version cần baseline mới. M7 không nới floor 0.85 của pass_hat_5 hoặc các slice/metric đã chọn.

## Các trap public

| Trap | Cách làm đẹp kết quả | Lý do integrity/ratchet phải chặn |
|---|---|---|
| evaluator_errors_as_nan | Đổi các điểm fail thành None/NaN rồi bỏ khỏi trung bình | Điểm row thiếu/không hữu hạn hoặc summary không hợp lệ |
| dropped_failing_rows | Bỏ row lỗi rồi tính lại summary | Số row, coverage và tập cặp item/seed |
| cherry_picked_seeds | Chỉ giữ seed tốt, sửa manifest | Seed khác spec/baseline, tập cặp thiếu |
| loosened_spec | Hạ floor, bỏ CI và toàn bộ slice | Ratchet với base_spec giữ thước đo gốc |

Test bổ sung còn kiểm row trùng thay row khác (giữ nguyên số lượng), evaluator_failures trên run xanh, sửa slice tag, sửa summary, baseline hỏng, threshold không hữu hạn và các đường nới spec.

## Người học tự chạy từ src/, nhánh starter/d09

### 1. Tất cả test Advanced M5–M7

```powershell
python -m pytest -q -m student -o addopts= -k advanced -p no:cacheprovider
```

Các test M4–M6 dùng report mẫu đã được cập nhật manifest/coverage để kiểm đúng schema M7; không bỏ yêu cầu cũ. Chưa chạy các test này thay người học.

### 2. Kiểm Core sau khi thay gate

```powershell
python -m pytest -q tests/test_lab9_stats.py tests/test_lab9_graders.py tests/test_lab9_gate.py tests/test_lab9_trace_case.py tests/test_lab9_evalset_hash.py -o addopts= -p no:cacheprovider
```

Lệnh không dùng tmp_path; CI Linux vẫn chạy thêm các test CLI evalset đầy đủ.

### 3. Xác nhận baseline spec 2.1 vẫn hợp lệ

```powershell
python -m lab9.gate --pr reports/baseline_v2.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml --base-spec config/metric_spec_v2.baseline.yaml
```

Kỳ vọng exit 0. Không sửa report nếu bị báo INTEGRITY; cần gửi nguyên lý do để phân tích. Baseline spec 2.1 người học đã sinh ở M6 vẫn dùng được vì M7 chỉ đổi gate, không đổi item/grader/metric values.

### 4. Chạy trap suite

```powershell
python -m lab9.traps --pr reports/eval_slice_regression.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
```

Lệnh sinh các trap trong reports/traps rồi gọi gate. Kỳ vọng 4 trap đều `blocked`, dòng cuối **exit 0 — the gate blocked every public trap**. Trap là output script phục vụ thử nghiệm, không tự sửa report đo agent.

Muốn lấy 4 dòng gate exit 1 riêng để dán PR:

```powershell
python -m lab9.gate --pr reports/traps/evaluator_errors_as_nan.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
python -m lab9.gate --pr reports/traps/dropped_failing_rows.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
python -m lab9.gate --pr reports/traps/cherry_picked_seeds.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
python -m lab9.gate --pr reports/traps/loosened_spec.json --baseline reports/baseline_v2.json --spec reports/traps/loosened_spec.spec.yaml --base-spec config/metric_spec_v2.yaml
```

Mỗi lệnh gate riêng phải exit 1 có lý do INTEGRITY/RATCHET, không tính Python exception là chặn đúng.

### 5. Mutation scorecard

```powershell
python -m lab9.mutation --spec config/metric_spec_v2.yaml --baseline reports/baseline_v2.json --base-spec config/metric_spec_v2.baseline.yaml
```

Kỳ vọng **mutation score 3/3 · false alarms 0**, fixed/honest_refactor merge, seeded/slice/flaky regression block. Gate không đọc tên variant để quyết định.

## Commit và CI sau khi kiểm tra local đạt

Từ gốc repo, người học tự stage code/config/tests/docs/workflow cùng generated eval set v2. Report v2 bị ignore, nên baseline phải force-add để bật CI nâng cao:

```powershell
git add .github/workflows/eval-gate.yml SUBMISSION.md docs src/config src/lab9 src/tests src/data/eval/eval_set_v2.jsonl src/data/eval/labels_v2.json
git add -f src/reports/baseline_v2.json src/reports/eval_fixed_v2.json src/reports/eval_honest_refactor_v2.json src/reports/eval_slice_regression.json src/reports/eval_flaky_regression.json
git commit -m "feat: complete lab9 advanced reliability and integrity gates"
git push
```

PR hiện tại tự cập nhật. Workflow eval-gate-v2 chỉ bật các bước nâng cao khi baseline_v2 được commit; hiện đã thêm mutation với base-spec và trap suite. Cần xác nhận cả Core và Advanced CI xanh, rồi cập nhật eval card/SUBMISSION bằng output thật. Không khẳng định đạt hidden tests chỉ vì public traps đều bị chặn.

## Giới hạn

Report có mọi row/metric được giả mạo nhất quán vẫn có thể lọt nếu không có nguồn run tin cậy/chữ ký hoặc replay độc lập. Schema checks không thay kiểm chứng ledger/trace gốc. Snapshot spec phải được bảo vệ; code grader, label và baseline cũng cần review. Hidden traps có thể thử thêm tổ hợp lỗi, nên public score không đảm bảo điểm bộ chấm ẩn.
