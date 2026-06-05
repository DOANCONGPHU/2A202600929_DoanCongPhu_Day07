# Benchmark Queries & Gold Answers
## Domain: Chính sách VinFast (vinfastauto.com)

---

## Bảng tổng hợp

| # | Query | Gold Answer | File nguồn | Metadata filter cần thiết |
|---|-------|-------------|------------|--------------------------|
| 1 | Nếu khách hàng không đến ký hợp đồng mua bán đúng hạn, tiền đặt cọc sẽ được xử lý như thế nào? | Tiền đặt cọc thuộc về VinFast, và VinFast có toàn quyền quyết định việc xử lý tiền đó. | dieukhoandatcoc.md | `category = deposit` |
| 2 | Tôi có thể đổi hoặc trả xe sau khi mua không? | Không. Sản phẩm không áp dụng đổi, trả. Sản phẩm được bảo hành tại hệ thống Showroom và Xưởng dịch vụ của Đại lý phân phối chính hãng VinFast theo chính sách bảo hành. | chinh_sach_san_pham.md | `category = product_policy` |
| 3 | VinFast có giao xe trực tiếp đến nhà tôi không? | Không. Sản phẩm được phân phối qua hệ thống Showroom của Đại lý phân phối chính hãng VinFast trên toàn quốc. VinFast không áp dụng chính sách vận chuyển trực tiếp đến khách hàng mua qua vinfastauto.com. | chinh_sach_san_pham.md | `category = product_policy` |
| 4 | Khách hàng có quyền yêu cầu thay pin khi nào? | Khi dung lượng pin tối đa (SOH) xuống dưới 70%. Việc thay pin phải được thực hiện tại showroom hoặc xưởng dịch vụ của VinFast Trading hoặc nhà phân phối ô tô VinFast chính hãng. | chinhsachthuepin.md | `category = battery_rental` |
| 5 | Thông tin thẻ thanh toán của khách hàng có được lưu trên hệ thống Vinfastauto.com không? | Không. Vinfastauto.com không trực tiếp lưu trữ thông tin thẻ khách hàng. Đối với thẻ quốc tế, thông tin thẻ không được lưu trên hệ thống của Vinfastauto.com mà được Đối Tác Cổng Thanh Toán lưu trữ và bảo mật. Đối với thẻ nội địa (internet banking), chỉ lưu mã đơn hàng, mã giao dịch và tên ngân hàng. | chinhsachbaomat.md | `category = security` |

---

## Chi tiết từng query

### Query 1 — Xử lý tiền đặt cọc khi khách không ký hợp đồng
**Query:** Nếu khách hàng không đến ký hợp đồng mua bán đúng hạn, tiền đặt cọc sẽ được xử lý như thế nào?

**Gold Answer:** Tiền đặt cọc thuộc về VinFast, và VinFast có toàn quyền quyết định việc xử lý khoản tiền đó.

**Chunk chứa thông tin:** Điều 5.2 — `dieukhoandatcoc.md`

**Ghi chú:** Query này yêu cầu metadata filter `category = deposit` để tránh retrieve nhầm sang các file điều khoản chung khác có nội dung tương tự.

---

### Query 2 — Chính sách đổi trả sản phẩm
**Query:** Tôi có thể đổi hoặc trả xe sau khi mua không?

**Gold Answer:** Không. Sản phẩm VinFast không áp dụng chính sách đổi trả. Xe được bảo hành tại hệ thống Showroom và Xưởng dịch vụ của Đại lý phân phối chính hãng theo chính sách bảo hành hiện hành.

**Chunk chứa thông tin:** Đoạn đầu — `chinh_sach_san_pham.md` (merge từ `chinhsachdoitra.md`)

**Ghi chú:** File này rất ngắn (~3 đoạn) nên hầu hết strategy đều retrieve đúng. Dùng để kiểm tra precision khi không cần filter.

---

### Query 3 — Chính sách vận chuyển
**Query:** VinFast có giao xe trực tiếp đến nhà tôi không?

**Gold Answer:** Không. VinFast không áp dụng chính sách vận chuyển trực tiếp đến khách hàng mua qua vinfastauto.com. Xe được nhận tại hệ thống Showroom của Đại lý phân phối chính hãng trên toàn quốc.

**Chunk chứa thông tin:** Toàn bộ nội dung — `chinh_sach_san_pham.md` (merge từ `chinhsachvanchuyen.md`)

**Ghi chú:** Query ngắn, mơ hồ ("giao đến nhà") — dùng để kiểm tra khả năng semantic matching khi query không dùng đúng từ khóa "vận chuyển".

---

### Query 4 — Điều kiện thay pin thuê
**Query:** Khách hàng thuê pin VinFast được quyền yêu cầu thay pin khi nào?

**Gold Answer:** Khách hàng có quyền yêu cầu sửa chữa hoặc thay thế pin khi dung lượng pin tối đa (SOH) xuống dưới 70%. Việc thay pin phải được thực hiện tại showroom, xưởng dịch vụ của VinFast Trading hoặc nhà phân phối chính hãng.

**Chunk chứa thông tin:** Điều 2.1 — `chinhsachthuepin.md`

**Ghi chú:** Bắt buộc cần metadata filter `category = battery_rental` để không retrieve nhầm sang các file khác không đề cập đến pin. Đây là query kiểm tra metadata filtering.

---

### Query 5 — Bảo mật thông tin thẻ thanh toán
**Query:** Vinfastauto.com có lưu trữ thông tin thẻ ngân hàng của tôi không?

**Gold Answer:** Không. Vinfastauto.com không trực tiếp lưu trữ thông tin thẻ. Đối với thẻ quốc tế, thông tin được Đối Tác Cổng Thanh Toán lưu và bảo mật. Đối với thẻ nội địa, chỉ lưu mã đơn hàng, mã giao dịch và tên ngân hàng.

**Chunk chứa thông tin:** Mục 2 (Quy định bảo mật) — `chinhsachbaomat.md`

**Ghi chú:** Query đụng đến hai loại thẻ (quốc tế và nội địa) — dùng để kiểm tra xem chunking có giữ nguyên 2 đoạn liên tiếp hay tách ra làm mất context.

---

## Yêu cầu đa dạng đã đáp ứng

| Yêu cầu | Trạng thái |
|---------|-----------|
| Queries đa dạng chủ đề | ✅ Đặt cọc, đổi trả, vận chuyển, pin thuê, bảo mật |
| Gold answer cụ thể, verify được từ tài liệu | ✅ |
| Ít nhất 1 query cần metadata filtering | ✅ Query 1 (deposit), Query 4 (battery_rental) |
| Có query kiểm tra semantic matching | ✅ Query 3 (dùng "giao đến nhà" thay vì "vận chuyển") |
| Có query kiểm tra chunk coherence | ✅ Query 5 (cần 2 đoạn liên tiếp) |