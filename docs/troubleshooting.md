# Xử lý sự cố

Mọi lệnh chạy trong thư mục `src/` (xem [src/README.md](../src/README.md)).

| Triệu chứng | Cách xử lý |
| --- | --- |
| `No module named 'lab8'` | Đứng trong `src/` (thư mục có `requirements.txt`), không phải gốc repo; chạy bằng `python -m lab8...` |
| `No module named 'yaml'` hoặc `No module named pytest` | Kiểm tra đang dùng đúng interpreter của venv và chạy `python -m pip install -r requirements.txt` trong `src/` |
| Windows: gõ `python` mà mở Microsoft Store | Dùng `py -3 -m venv .venv`. Sau khi activate venv thì `python` trỏ vào venv |
| Windows: `py` báo không tìm thấy Python nhưng `python --version` chạy được | Nếu phiên bản là 3.11–3.13, tạo venv bằng `python -m venv .venv`; hoặc dùng venv đã có qua `.\.venv\Scripts\python.exe -m ...` |
| Windows: `running scripts is disabled` | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` rồi activate lại |
| Windows: `UnicodeEncodeError` khi in tiếng Việt từ code của nhóm | Đặt biến môi trường UTF-8: PowerShell `$env:PYTHONUTF8=1`, cmd `set PYTHONUTF8=1`. Các CLI của lab đã tự chuyển stdout sang UTF-8 |
| Windows: `PermissionError: [WinError 32] The process cannot access the file because it is being used by another process` với file `.sqlite` | Có connection chưa đóng. Mở bằng `connect()` thì đóng trong `finally: conn.close()`, như `swarm_reference.py` |
| Trial fail với `missing_trace`, `stale_trace`, `invalid_trace` hoặc `trace_run_id_mismatch` | Shape chưa ghi trace đúng contract. Xem mục [Trace contract v1](contracts.md#trace-contract-v1). Nhớ ghi trace cả ở các nhánh return sớm (`needs_info`, `escalated`) |
| Benchmark báo `exception:<lỗi>` cho một shape | `run_claim` ném lỗi. Xem `reason` trong `src/reports/benchmark.json`, các shape khác vẫn được chấm |
| T12 báo `crash did not fire` | Shape chưa truyền `crash_at` vào `durability.issue_refund`, hoặc đã nuốt `InjectedCrash`. Bắt để flush trace rồi `raise` lại vẫn đúng |
| CLI trả exit code 2 và `crashed: true` | Fault injection đã kích hoạt đúng. Resume bằng cùng DB và bỏ `--crash-at`; không sửa code để biến crash thành resolved |
| `PytestCacheWarning: Access is denied` nhưng mọi test passed | Cache pytest không ghi được; có thể chạy với `-p no:cacheprovider`. Cảnh báo này khác test failure; vẫn phải kiểm exit code và các dòng failed/error |
| `check_submission` báo WARN còn thay đổi chưa commit | Commit các thay đổi liên quan rồi kiểm lại. ADR có thể giữ hash commit code đã benchmark nếu các commit sau chỉ sửa tài liệu |
| Benchmark ghi pass rate 0 nhưng ma trận student của code hiện tại xanh | Nếu shape còn stub thì 0 là đúng; nếu đã triển khai, report có thể cũ. Chạy lại benchmark đủ bốn shape; không sửa JSON bằng tay |
| Chạy lần hai trên cùng `data/run.sqlite` không tạo refund mới | Ledger đang làm đúng. Benchmark tự tạo DB mới cho từng trial |
| Muốn gọi model thật | Không được. MockLLM cố định theo seed để mọi nhóm so cùng điều kiện |
