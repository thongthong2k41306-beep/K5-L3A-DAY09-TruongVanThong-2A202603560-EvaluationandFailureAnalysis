# Nộp bài (hạn 23:59 cùng ngày)
PR từ `starter/d09` → `main` của repo nhóm. Chấm commit cuối trước 23:59; commit sau hạn không tính.

## Core (nên xong trước 17:00)
- [x] `src/lab9/{stats,graders,evalset}.py` đã hoàn thành TODO M1–M4
- [x] `src/data/eval/eval_set_v1.jsonl` có `failure_modes`, `labels_v1.json` tách riêng
- [ ] `docs/failure_taxonomy.md`, `docs/trace_case.md` (1 case + regression test), `docs/judge_audit.md`, `docs/eval_card.md`, `docs/PRD_v1.1.md`
- [x] `src/reports/baseline_v1.json`, `eval_fixed.json`, `eval_seeded_regression.json` (sinh bằng script; có local, còn cần force-add/commit)
- [x] `src/harness_map.yaml` có section `eval` (version 1.2)
- [ ] Job `eval-gate` xanh; dán output gate exit 1 của `seeded_regression` vào mô tả PR

## Trạng thái đối chiếu local ngày 17/11/2026

- Người học xác nhận 67 test M2–M4 pass, detection 100% / false alarms 0%, swarm và fixed gate exit 0, seeded_regression gate exit 1 đúng ở pass_rate; ci_check exit 0.
- Eval card, PRD, judge audit và trace case đã điền từ report/trace. Nhóm tài liệu ở checklist vẫn chưa đánh dấu hoàn tất vì M1 còn xác nhận 5 anchor được giao. Regression test lưu trace đã được người học xác nhận **1 passed in 0.74s**.
- Test mới: từ `src/`, chạy `python -m pytest -q tests/test_lab9_trace_case.py -o addopts= -p no:cacheprovider`; đã xác nhận **1 passed in 0.74s**. Hai trace lỗi/fixed đã lưu trong `src/tests/fixtures/lab9/` để commit cùng test.
- Chưa có bằng chứng workflow GitHub xanh, commit baseline, PR hoặc phê duyệt Product. PRD ghi trạng thái chưa duyệt; không tự điền ngày ký duyệt.
- Baseline và report nằm trong thư mục bị ignore: cần `git add -f` theo `docs/m4_gate.md`. Không sửa tay các report.

## Advanced / Expert (tới 23:59)
- [ ] `config/fm_map.yaml`, `config/metric_spec_v2.yaml` (slices, `pass_hat_5`, metric FM-08), `stats.pass_at_k/pass_hat_k`, `gate.slice_check`, `gate.integrity_check`
- [ ] `src/data/eval/eval_set_v2.jsonl` + `labels_v2.json` (sinh bằng `evalset --v2 --build`)
- [ ] `src/reports/baseline_v2.json` (sinh bằng script) → job `eval-gate-v2` chạy và xanh
- [ ] Mô tả PR: output `lab9.mutation` (scorecard + `--aa`) và 4 dòng `exit 1` của các trap
- [ ] `docs/eval_card.md` thêm mục v2: ngưỡng chọn từ A/A, slice nào bắt lỗi nào, và giới hạn cỡ mẫu (bug 1/3 seed không phát hiện ổn định với 5 seed)
