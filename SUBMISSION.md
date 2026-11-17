# Nộp bài — Lab 9 Evaluation & Failure Analysis

PR từ `starter/d09` → `main` của repo người học. Hạn theo đề: 23:59 ngày học; giảng viên chấm commit cuối trước hạn. Không cần tự merge nếu chỉ được yêu cầu nộp link PR.

## Core M0–M4: trạng thái đã đối chiếu

- [x] M0: người học gửi M0 PASS; build 14 item và 14 nhãn riêng.
- [x] M1: mapping failure_modes cho 14 item, checker 0 problem, taxonomy ≥5 FM có định nghĩa/layer/claim hoặc trace/grader.
- [x] M1 — 5 case public: đã phân tích C-002, C-007, C-008, C-013, C-014 tại seed 11; mỗi case có mã FM, bước sai đầu tiên quan sát được, đối chứng fixed và grader trong `docs/m1_coding_sheet.md`.
- [x] Bằng chứng 5 case: đã lưu đủ 10 trace lỗi/fixed trong `src/tests/fixtures/lab9/` để review và commit.
- [x] M1: xác nhận 5 case nào là anchor bắt buộc, đối chiếu mã FM và bước sai đầu tiên với key giảng viên. Người học chưa có danh sách; không tự nhận đã khớp.
- [x] M2: stats/confusion/P/R/kappa/Rogan–Gladen, tone PASS, helpful FAIL, audit 15 bất đồng; người học chạy 17 test M2 pass.
- [x] M3: ApprovalBypass, RefundAmountCorrect, metric FM-08 và proposal check; 27 test pass, detection 100%, false alarms 0%.
- [x] M4: paired bootstrap, gate, test và harness_map eval version 1.2; 67 test M2–M4 pass trước các test bổ sung.
- [x] Test trace: 1 passed; test SHA Windows/Linux: 2 passed (hai lượt chạy riêng).
- [x] Tài liệu đã điền: failure_taxonomy, m1_coding_sheet, trace_case, judge_audit, eval_card, PRD_v1.1.
- [x] Baseline/fixed/seeded_regression report sinh bằng script và đã commit; SHA hiện hành cbefbfa97628.
- [x] Swarm/fixed gate exit 0; seeded_regression exit 1, pass_rate Δ −0.271, CI [−0.500, −0.057].
- [x] Local ci_check exit 0; workflow PR #4 và manual #5 xanh theo ảnh người học gửi.
- [x] PR #1 có mô tả kiểm tra và output exit 1 của seeded_regression.
- [x] Commit/push đợt bổ sung tài liệu và trace fixtures cuối của lần rà soát này.

## Hồ sơ và bằng chứng

- [Tổng hợp Core](docs/core_submission.md) — bảng M0–M4, đường dẫn và giới hạn.
- [Taxonomy](docs/failure_taxonomy.md), [phiếu đọc trace](docs/m1_coding_sheet.md), [trace case có test](docs/trace_case.md).
- [Judge audit](docs/judge_audit.md), [eval card](docs/eval_card.md), [PRD v1.1](docs/PRD_v1.1.md).
- PR [#1](https://github.com/thongthong2k41306-beep/K5-L3A-Day09-TruongVanThong-Evaluation-and-Failure-Analysis/pull/1).
- [Workflow eval-gate](https://github.com/thongthong2k41306-beep/K5-L3A-Day09-TruongVanThong-Evaluation-and-Failure-Analysis/actions/workflows/eval-gate.yml).

Report được nộp: `src/reports/baseline_v1.json`, `eval_fixed.json`, `eval_seeded_regression.json`. Không sửa tay report. `eval_pr.json` là output do CI sinh mỗi lần chạy, không cần commit; bản local cũ chưa phản ánh SHA chuẩn hóa không dùng làm bằng chứng hiện hành.

## Advanced / Expert M5–M7

- [x] M5 — đã viết mapping 8 cơ chế trong fm_map.yaml, cấu hình money_movement/adversarial/denial, gate.slice_check và test M5; hướng dẫn tại docs/m5_slices.md.
- [x] M5 — 12 test passed; eval set v2 SHA c26ebe1e1abb, 28 item/28 nhãn, 0 problem; baseline tự so sánh/fixed/honest_refactor exit 0, slice_regression chỉ bị chặn bởi slice:money_movement/pass_rate.
- [x] M6 — stats.pass_at_k/pass_hat_k, validation và metric blocking pass_hat_5; spec v2 phiên bản 2.1, floor 0.85 đã đối chiếu A/A.
- [x] M6 — 28 test passed; A/A mọi delta=0, pass_hat_5 hai bộ seed đều 0.8929; baseline spec 2.1/fixed/honest_refactor exit 0, flaky bị chặn có pass_hat_5=0.5714; slice_regression vẫn bị chặn ở money_movement. Xem docs/m6_reliability.md.
- [x] M7 — đã viết integrity_check/ratchet, đối chiếu summary với rows, test row trùng/lỗi grader trên run xanh; lưu snapshot spec 2.1 và bổ sung trap suite vào workflow v2.
- [x] M7 — người học xác nhận 73 test Advanced passed, baseline tự so sánh exit 0, cả 4 trap bị chặn, mutation score 3/3 và 0 báo nhầm; xem docs/m7_integrity.md.
- [x] Eval set v2, nhãn riêng và baseline_v2 spec 2.1 đã được người học sinh bằng script.
- [x] Mutation scorecard, A/A và traps đạt local theo kết quả người học xác nhận.
- [x] Kiểm lại Core sau thay gate M7, commit/push toàn bộ phần nâng cao và baseline_v2, xác nhận workflow eval-gate-v2 xanh.
- [x] Eval card bổ sung kết quả M5/M6/M7 local, ngưỡng A/A, slice và giới hạn cỡ mẫu; trạng thái CI nâng cao còn chờ.

CI Core xanh không chứng minh M5–M7 hoàn tất hoặc đã qua bộ chấm ẩn. Chưa có phê duyệt Product; đây là lab offline, không phải release chạy với khách hàng thật.
