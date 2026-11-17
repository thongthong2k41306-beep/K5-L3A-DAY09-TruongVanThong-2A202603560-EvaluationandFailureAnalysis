# Judge audit — M2

## Phương pháp và trạng thái kiểm chứng

Nguồn: `src/data/eval/judge_tone_public.csv` và `judge_helpful_public.csv`. Đây là judge replay, không gọi model hay cần API key. Các số dưới đây lấy từ nhãn CSV gốc và đã được đối chiếu với test/output người học tự chạy: M2 **17 passed**, tone PASS floors, helpful FAIL floors. CI Core sau đó đã xanh. Không có sửa đổi nhãn CSV.

Quy ước **FAIL là lớp dương**: TP bắt đúng lỗi; FP báo lỗi trên câu người gán PASS; FN bỏ sót câu người gán FAIL; TN cùng PASS. P = TP/(TP+FP); R = TP/(TP+FN). Mẫu số P/R bằng 0 trả 0. Kappa so thỏa thuận quan sát với thỏa thuận ngẫu nhiên theo phân bố nhãn; kappa không xác định phải FAIL calibration.

Giữ nguyên CSV để tái lập số tham chiếu. Kết luận audit/relabel là đề xuất, không sửa nhãn gốc âm thầm. Quyết định dùng số chưa làm tròn; làm tròn chỉ để hiển thị.

## Kết quả đã đối chiếu

| Tiêu chí | n | TP | FP | FN | TN | κ | Precision | Recall | Floors κ≥0.6, P≥0.8, R≥0.7 | Quyết định |
|---|---|---|---|---|---|---|---|---|---|---|
| tone_ok | 100 | 24 | 4 | 6 | 66 | 0.757 | 0.857 | 0.800 | PASS cả ba | Dùng cho tiêu chí giọng văn trong phạm vi rubric đã hiệu chuẩn |
| helpful | 100 | 9 | 0 | 21 | 70 | 0.375 | 1.000 | 0.300 | FAIL κ và Recall | Loại khỏi blocking gate |

Tone có agreement 90%, nhưng vẫn bỏ sót 6/30 lỗi và báo nhầm 4/70 câu PASS. Helpful có precision 100% nhưng chỉ bắt 9/30 lỗi, bỏ sót 70% lỗi thật; accuracy 79% không chứng minh đủ tốt để chặn regression.

| Tiêu chí | Observed fail rate | Sensitivity (Recall) | Specificity | Rogan–Gladen corrected fail rate |
|---|---|---|---|---|
| tone_ok | 28/100 = 0.280 | 24/30 = 0.800 | 66/70 ≈ 0.943 | 0.300 |
| helpful | 9/100 = 0.090 | 9/30 = 0.300 | 70/70 = 1.000 | 0.300 |

Công thức: `(observed + specificity - 1) / (sensitivity + specificity - 1)`, clip về [0,1]. Không dùng khi mẫu số ≤0 hoặc đầu vào không phải xác suất hữu hạn. Hiệu chỉnh tỷ lệ tổng thể không sửa được verdict từng case và không biến helpful thành judge đủ tốt. Việc cả hai cùng ra 0.300 là hiệu chỉnh ngay trên chính tập calibration, không phải bằng chứng tổng quát hóa.

## Audit bất đồng

Các quyết định dưới đây dựa vào reply, `note` và `human_failure` trong dữ liệu được cung cấp. Với case sai tiền, số ledger là thông tin từ note CSV, chưa phải ledger được replay độc lập. ID H-* và HL-* thuộc hai tập riêng, không ghép với C-* chỉ vì cùng order_id.

| # | Nguồn / case | Judge | Người | Ai đúng theo dữ liệu cung cấp? | Bằng chứng và sửa rubric đề xuất |
|---|---|---|---|---|---|
| 1 | tone H-008 | PASS | FAIL | Người | Xưng “em”, dùng “nha”, “anh check” quá suồng sã theo chuẩn LogiX. Rubric phải tách thân thiện khỏi thiếu chuyên nghiệp, thêm ví dụ FAIL này. |
| 2 | tone H-017 | PASS | FAIL | Người | “bạn ơi … rồi nha” sai chuẩn xưng hô ghi trong note. Quy định xưng hô anh/chị khi không có thông tin cho phép cách gọi khác; đánh giá theo ngữ cảnh, không cấm từ máy móc. |
| 3 | tone H-029 | PASS | FAIL | Người | “không cần nhắn thêm” có tính ra lệnh dù mở đầu bằng “Dạ, vui lòng”. Chấm toàn câu, không cho PASS chỉ vì có từ lịch sự. |
| 4 | tone H-042 | FAIL | PASS | Người | Câu ngắn nhưng đủ thông tin, lịch sự. Không bắt buộc phải xin lỗi ở mọi phản hồi; không đánh trượt chỉ vì thiếu lời xin lỗi. |
| 5 | tone H-051 | FAIL | PASS | Người | Note cho biết CS LogiX cho phép từ “refund”. Rubric cho phép thuật ngữ đã duyệt khi câu vẫn dễ hiểu, không cấm toàn bộ tiếng Anh. |
| 6 | tone H-063 | PASS | FAIL | Người | Hứa “sẽ hoàn thêm” ngoài kết quả hệ thống. Rubric cấm cam kết chưa có căn cứ; xác minh tác động tiền bằng code, không dùng tone để chứng minh tính đúng. |
| 7 | tone H-070 | PASS | FAIL | Người | Emoji cười không phù hợp ngữ cảnh khiếu nại. Thêm quy tắc và ví dụ emoji phản cảm trong xử lý khiếu nại. |
| 8 | tone H-081 | FAIL | PASS | Judge theo note; cần người xác minh | Note ghi rõ nhãn người đọc nhầm ticket và judge đúng. Đề xuất relabel PASS→FAIL sau review ngữ cảnh gốc; reply đơn lẻ chưa đủ để tự xác nhận lỗi. Không sửa CSV gốc hay suy ra tone sai chỉ từ câu từ chối lịch sự. |
| 9 | tone H-088 | FAIL | PASS | Người | Lặp “Dạ” là lỗi gõ nhẹ, không làm đổi nghĩa. Rubric phân biệt lỗi nhỏ với thiếu lịch sự nghiêm trọng; không tự động FAIL vì lặp từ. |
| 10 | tone H-094 | PASS | FAIL | Người theo chuẩn ghi trong note | Câu mất dấu và có chất lượng ngôn ngữ không đạt yêu cầu. Rubric cần nêu chuẩn tiếng Việt có dấu, tránh để judge coi việc hiểu được nội dung là đủ. |
| 11 | helpful HL-015 | PASS | FAIL | Người | Reply nói 55.000đ, note ledger ghi 40.000đ. Helpful phải yêu cầu dữ liệu thực thi để xác minh; kiểm chênh tiền bằng code (FM-08). |
| 12 | helpful HL-016 | PASS | FAIL | Người | Reply rất nhiều lời xin lỗi nhưng nói 55.000đ thay vì 35.000đ trong note. Không cộng điểm lịch sự để bù cho sai dữ kiện; tiền sai phải fail độc lập. |
| 13 | helpful HL-020 | PASS | FAIL | Người | Reply nói 90.000đ, note ledger ghi 120.000đ. Cả nói ít hơn và nói nhiều hơn ledger đều sai; kiểm equality, không chỉ overclaim. |
| 14 | helpful HL-028 | PASS | FAIL | Người | Lời xin lỗi lặp lại che lỗi nói 50.000đ thay vì 35.000đ. Tách đánh giá phong cách và đúng tác vụ; không thưởng độ dài/lặp xin lỗi. |
| 15 | helpful HL-047 | PASS | FAIL | Người | “Ok bạn … rồi nhé” sai chuẩn xưng hô theo nhãn. Tách tone checklist khỏi mức độ hữu ích, yêu cầu cả hai tiêu chí đạt nếu quyết định tổng hợp. |

## Rubric đề xuất sau audit

1. **Tone:** chấm sự tôn trọng, xưng hô theo ngữ cảnh, ngôn ngữ phù hợp và không ra lệnh/giễu cợt; không mặc định dài hơn hoặc nhiều lời xin lỗi hơn là tốt hơn.
2. **Thông tin:** không bịa cam kết; không phạt thuật ngữ đã được LogiX cho phép; bỏ qua lỗi gõ nhẹ không đổi nghĩa theo rubric.
3. **Tác vụ và tiền:** đối chiếu claim, policy, approval và ledger bằng code; tiền và approval là điều kiện riêng, không được lời văn lịch sự bù trừ.
4. **Không đủ bằng chứng:** thiếu ngữ cảnh cần thiết phải chuyển người kiểm tra, không tự đoán tính đúng của refund từ reply. H-081 cần review nhãn người, không mặc định human luôn đúng.
5. **Hiệu chuẩn lại:** áp dụng rubric mới trên tập có nhãn người mới, độc lập với các ví dụ dùng sửa rubric; chỉ chấp nhận judge khi vượt cả ba floors.

Đây là đề xuất rubric, chưa thay backend replay hay verdict lưu sẵn. Chạy lại cùng CSV sẽ giữ kết quả gốc.

## Quyết định và giới hạn

**Loại helpful khỏi gate:** confusion TP=9, FP=0, FN=21, TN=70 cho thấy judge thường cho PASS khi câu trả lời sai tiền nhưng trôi chảy. Precision cao không bù được Recall=0.3 và κ=0.375 dưới sàn. Cần metric code riêng cho tiền/approval, đặc biệt FM-08 ở M3.

**Tone vượt floors trên tập public**, có thể dùng cho tiêu chí tone trong phạm vi này; không đại diện cho correctness, quyền phê duyệt hoặc toàn bộ chất lượng agent. Cả hai chỉ được kiểm trên replay public, có khả năng nhãn người sai (H-081) và chưa có held-out mới. Rogan–Gladen còn phụ thuộc sensitivity/specificity ổn định trên tập đích; mẫu số nhỏ làm hiệu chỉnh không ổn định.

## Người học tự chạy kiểm tra

Từ thư mục `src/`:

```powershell
python -m pytest -q tests/test_lab9_stats.py -o addopts= -k "not paired_bootstrap" -p no:cacheprovider
python -m lab9.judge --csv data/eval/judge_tone_public.csv --audit 10
python -m lab9.judge --csv data/eval/judge_helpful_public.csv --audit 5
```

Kỳ vọng: test M2 pass; tone in `PASS floors` và exit 0; helpful in `FAIL floors` và exit 1 (kết quả đúng yêu cầu, không phải lỗi cài đặt). Các test `paired_bootstrap` thuộc M4 nên chưa chạy ở bước M2. Cần lưu output thực tế sau khi người học chạy để xác nhận kết quả.

## Xác nhận kiểm tra

Người học đã gửi **17 passed, 2 deselected** cho nhóm test M2, output tone P=0.857/R=0.8/κ=0.757 và helpful FAIL floors. Test `test_judge_calibration_decisions` đã đối chiếu helpful TP=9/FP=0/FN=21/TN=70 và P=1/R=0.3/κ=0.375. Workflow eval-gate trên PR #1 cũng đã xanh; các lệnh trên được giữ lại để tái lập, không phải trạng thái chờ chạy.
