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

## Advanced / Expert M5–M7 — chưa làm trong đợt Core

- [ ] fm_map.yaml, metric_spec_v2.yaml đầy đủ slices/pass_hat_5; stats.pass_at_k/pass_hat_k; gate.slice_check và integrity_check.
- [ ] Eval set v2, nhãn riêng và baseline_v2 do script sinh.
- [ ] Mutation scorecard, A/A, traps và workflow v2 đạt.
- [ ] Eval card bổ sung phân tích v2 và giới hạn cỡ mẫu.

CI Core xanh không chứng minh M5–M7 hoàn tất hoặc đã qua bộ chấm ẩn. Chưa có phê duyệt Product; đây là lab offline, không phải release chạy với khách hàng thật.
