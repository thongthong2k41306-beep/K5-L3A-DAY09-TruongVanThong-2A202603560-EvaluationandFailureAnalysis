# Hồ sơ Core — M0 đến M4

Người thực hiện: **Trương Văn Thông**. Repo nhánh **starter/d09**. Ngày tổng hợp **17/11/2026**, múi giờ Asia/Bangkok. Chỉ tổng hợp kết quả người học đã tự chạy và report/trace hiện có, không chạy chương trình trong lúc soạn hồ sơ.

## Bản nộp và CI

- PR [#1, starter/d09 → main](https://github.com/thongthong2k41306-beep/K5-L3A-Day09-TruongVanThong-Evaluation-and-Failure-Analysis/pull/1).
- Commit code/report đã được kiểm tra: **9a445ea** (normalize eval-set SHA), kế thừa các commit Core trước đó.
- Người học gửi ảnh: workflow **#4** (pull_request synchronize) và **#5** (workflow_dispatch) đều xanh trên starter/d09. Xem [workflow eval-gate](https://github.com/thongthong2k41306-beep/K5-L3A-Day09-TruongVanThong-Evaluation-and-Failure-Analysis/actions/workflows/eval-gate.yml).
- Đợt rà soát cuối bổ sung tài liệu và bản sao trace; cần commit/push các file mới để chúng xuất hiện trên PR. Không tự nhận đợt chỉnh sửa mới đã được commit.

## Bảng đối chiếu M0–M4

| Mốc | File/bằng chứng | Kết quả đã nhận | Trạng thái |
|---|---|---|---|
| M0 | lab8 package, requirements, public data, lab9.smoke; item/labels riêng | M0 PASS; 14 item + 14 labels | Đạt kiểm tra môi trường |
| M1 | failure_taxonomy.md, m1_coding_sheet.md, evalset.py, eval_set_v1.jsonl | Checker 0 problem; 9 FM; 5 case public có đối chứng và bước sai đầu tiên | Code/tài liệu public đã điền; còn xác nhận danh sách 5 anchor lớp |
| M2 | stats.py, judge.py, judge_audit.md | 17 test pass; tone PASS κ=.757/P=.857/R=.8; helpful FAIL κ=.375/R=.3; audit 15 bất đồng | Đạt kiểm tra public |
| M3 | graders.py, metric_spec.yaml, m3_trajectory.md | 27 test pass; detection 100%, false alarms 0%; FM-08 blocking | Đạt kiểm tra public |
| M4 | paired_bootstrap, gate.py, test_lab9_gate.py, harness_map.yaml, eval-gate.yml | 67 test M2–M4 pass; fixed/swarm merge; regression block đúng; ci_check exit 0; CI xanh | Đạt kiểm tra local và CI |
| Trace case | trace_case.md, test_lab9_trace_case.py, trace fixtures | 1 passed trong lần chạy riêng | Đạt |
| SHA cross-platform | evalset.sha12, test_lab9_evalset_hash.py | 2 passed; baseline và CI cùng SHA cbefbfa97628 | Đạt |
| Tài liệu sản phẩm | eval_card.md, PRD_v1.1.md | Điền metric, số report, trách nhiệm, giới hạn và CI | Đã soạn; không thay phê duyệt Product |

Không cộng các lượt test riêng thành một lần chạy suite mới. Các số 67, 1 và 2 là các lần chạy khác nhau do người học gửi. Workflow xanh chứng minh suite CI đã qua; chưa trích số lượng test từ log CI để tự tạo một số mới.

## Report hiện hành

Eval-set SHA **cbefbfa97628**, spec **1.0**, MockLLM, 14 item × seed 11/22/33/44/55. SHA chuẩn hóa newline CRLF→LF; không thay dữ liệu/nhãn khi sửa tương thích Windows/Linux.

| Shape | Run ID | pass_rate | Gate |
|---|---|---:|---|
| swarm baseline | E-swarm-20261117-cbef | 0.9857 | PR swarm cùng thước đo được merge |
| fixed | E-fixed-20261117-cbef | 1.0000 | exit 0 — merge |
| seeded_regression | E-seeded_regression-20261117-cbef | 0.7143 | exit 1 — blocked |

Report nguồn được script sinh, đã commit: [baseline](../src/reports/baseline_v1.json), [fixed](../src/reports/eval_fixed.json), [seeded regression](../src/reports/eval_seeded_regression.json). CI sinh eval_pr.json mới trước khi so baseline; không dùng file eval_pr local cũ làm report hiện hành.

Output gate đã được người học xác nhận:

```text
pass_rate 0.7143 Δ -0.271 CI [-0.500, -0.057] BLOCK
exit 1 — blocked: refund_amount_correct, proposal_amount_correct, reply_amount_correct, pass_rate
```

## File cần reviewer đọc

1. [Taxonomy](failure_taxonomy.md) và [phiếu đọc 5 case public](m1_coding_sheet.md): coverage và bước sai đầu tiên.
2. [Trace case C-002@11](trace_case.md): lỗi FM-03 và regression test.
3. [Judge audit](judge_audit.md): confusion, floors, lý do loại helpful, review nhãn/rubric.
4. [Eval card](eval_card.md): metric đầy đủ, delta/CI, nguồn report và giới hạn.
5. [PRD v1.1](PRD_v1.1.md): định nghĩa đạt, gate và trách nhiệm.
6. [Hướng dẫn M4](m4_gate.md) và [SUBMISSION](../SUBMISSION.md): tái lập/nộp bài.

## Điều kiện chưa thể tự xác nhận

Danh sách 5 anchor chính thức và key riêng không có trong repo; người học chưa có danh sách. Coding sheet đã hoàn thiện cho 5 case public nhưng không thay đáp án chấm. Cần giảng viên xác nhận hoặc giao đúng anchor để hoàn tất yêu cầu này. Không tự đánh dấu “M1 khớp key” hoặc cam kết đủ điểm.

Không có phê duyệt Product/reviewer mới, không tự merge PR. M5–M7 là bài nâng cao chưa làm trong đợt này; CI Core xanh không chứng minh bộ chấm ẩn đạt. MockLLM/public replay không phải đánh giá khách hàng hay LLM thật.

## Commit phần tài liệu cuối

Từ thư mục gốc repo, người học tự chạy khi muốn cập nhật PR:

```powershell
git branch --show-current
git add SUBMISSION.md docs src/tests/fixtures/lab9
git commit -m "docs: finalize lab9 core evidence and submission checklist"
git push
```

Nhánh phải là starter/d09. Không cần sinh lại report vì đợt rà soát này chỉ sửa tài liệu và lưu nguyên trace đã có; không đổi eval set, label, spec, grader hay code agent. PR hiện tại tự cập nhật, không cần tạo PR mới.
