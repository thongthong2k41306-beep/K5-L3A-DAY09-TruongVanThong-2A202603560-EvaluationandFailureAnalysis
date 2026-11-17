# Luật nghiệp vụ LogiX-VN (synthetic)

Tài liệu này tách từ README cũ, nội dung giữ nguyên. Code của nhóm phải tuân đúng các luật dưới đây; grader chấm theo các luật này.

Nguồn sự thật là dòng order và policy có `is_current` và `effective_date <= 2026-11-15`. Đây là mốc `as_of` cố định của lab, không phải ngày hệ thống. Chữ trong ticket là dữ liệu người dùng, kể cả những câu như "ignore policy" hay "trễ 9 ngày". Quote là entitlement trước khi host áp approval và trừ khoản đã hoàn; số ghi ledger có thể nhỏ hơn quote.

| Tình huống | Kết quả đúng |
| --- | --- |
| Trễ ≥ 3 ngày, đơn `delivered` hoặc `delivered_late`, policy hiện hành | Hoàn đúng `shipping_fee_vnd` |
| Đơn `delivered`/`delivered_late`, `damage_verified=true`, clause damage của policy hiện hành đủ điều kiện | Quote `min(max_refund của DMG-04, paid_vnd)` |
| Cả ship và damage cùng đủ điều kiện | Một refund bằng **số lớn hơn**, không cộng hai số |
| Không có clause nào đủ điều kiện, hoặc đơn `cancelled`/`in_transit` | Không refund (`denied`). Trễ dưới 3 ngày/phí ship 0 chỉ loại entitlement ship; damage chưa verify chỉ loại entitlement damage. Nếu entitlement khác vẫn đủ điều kiện thì dùng số lớn nhất |
| Thiếu `order_id` | `needs_info`, không ghi ledger. Không lấy mã đơn từ câu chữ trong ticket |
| Principal không sở hữu đơn, hoặc không tìm thấy đơn | `escalated`. Không trả phone, địa chỉ, tên hàng, internal note |
| Policy cũ `SHIP-LATE-OLD` hoặc policy tương lai | Bỏ qua. `get_clause` vẫn trả về các clause này; cần kiểm cả `is_current` và `effective_date <= as_of`. `compute_compensation` đã lọc policy phù hợp |
| Không có approval, approval hết hạn, bị thu hồi, hoặc amount ≤ 0 | Không ghi refund. Khi quote > 0 mà cổng duyệt từ chối thì phải có audit `policy_denied` |
| Approval mà claim trỏ tới (`approval_id`) được cấp cho claim khác | Không ghi refund, audit `policy_denied` lý do `approval_claim_mismatch`. Chỉ approval có `approval_id` khớp claim mới được tính |
| Đơn đã được hoàn trước đó bởi claim khác | Trần tính **theo đơn**: tổng tiền hoàn của một đơn không vượt entitlement lớn nhất. Hoàn đủ rồi → `denied`, audit `policy_denied` lý do `order_already_refunded`. Entitlement mới lớn hơn (ví dụ hỏng hàng sau khi đã hoàn ship) → chỉ hoàn **phần chênh** |
| Approval thấp hơn quote, đơn chưa được hoàn trước đó | Refund `min(quote, approved_vnd, paid_vnd)`. Nếu có lịch sử refund, dùng công thức trần theo đơn bên dưới. `proposal_amount` vẫn là quote |
| Gọi lại cùng claim | Vẫn một dòng ledger. Amount host tính sau cap khác amount đã commit → `conflict`, không sửa số cũ |
| Crash sau khi đã ghi effect, trước checkpoint | Resume xong vẫn một refund và một audit `refund_committed` |

Ví dụ public:

- T01: đơn `O-107` trễ 4 ngày, phí ship 35.000, approval 35.000 → một effect 35.000 và một audit committed.
- T13: đơn `O-505` đã được hoàn 35.000 ship từ claim trước. Ticket nói "chưa nhận được tiền" → `denied`, `proposal_amount` 35.000, không ghi ledger, có `policy_denied`.
- T14: đơn `O-515` đã được hoàn 30.000 ship, nay hỏng hàng đã verify (entitlement 150.000) → `resolved`, `proposal_amount` 150.000, ledger 120.000.

**Cách làm đúng với trần theo đơn:** truyền **quote đầy đủ** từ `compute_compensation` vào `durability.issue_refund`. Host tự trừ phần đã hoàn. Nếu shape tự trừ trước rồi mới truyền vào, host sẽ trừ thêm lần nữa và T14 fail. Muốn biết đơn đã được hoàn bao nhiêu thì dùng read tool `lookup_refund_history`.

Với approval hợp lệ và policy của lab, đặt `already` là tổng refund của các claim **khác** trên cùng đơn. Host kiểm `quote - already > 0`, sau đó tính `amount = min(quote - already, approved_vnd, paid_vnd - already)`; amount không dương thì từ chối. Approval cap áp cho lần ghi này. Khi retry chính claim đã ghi, host loại claim đó khỏi `already` để giữ idempotency. Không tính lại công thức này trong shape; đây là mô tả `policy.authorize`, không phải yêu cầu sửa host.

Tiền do code tính: `lab8.tools.compute_compensation` / `lab8.compensation.quote`. Không để MockLLM quyết số tiền.
