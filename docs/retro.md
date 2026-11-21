# Retro nhóm

## Phase 2 (nhanh)
- Điều tốt: lát quán đọc 2 bếp, 4 bàn và 6 món trực tiếp từ contract v1.1; kiểm tra riêng cho lọc món theo kế hoạch ngày đã chạy đạt.
- Điều tệ: luồng `day` chưa có trong runner tại thời điểm làm lát quán, nên chưa thể kiểm chứng tích hợp qua CLI. Toàn bộ test repo hiện lỗi ở gather vì contract v1.1 đổi `fish_initial` thành số nhưng `GatherSim` còn duyệt như danh sách; lát quán có 13 test liên quan đạt.
- 1 hành động cho Phase 3: thêm kiểm thử tích hợp `day` để xác nhận mỗi ngày chỉ nhận các món trong `day_plan` sau khi luồng ngày được ghép.

## Phase 3 (nhanh)
- Điều tốt: lát quán có test riêng cho hao tươi, biên 30, thứ tự `spoiled` và giữ lại nguyên liệu theo id; luật v1.1 vẫn chạy khi chưa bật schema mới.
- Điều vướng: contract và file kho vẫn ở v1.1 khi làm lát quán; phần tiêu nguyên liệu/tính giá của Cương và bàn giao `day` cần ghép với schema v1.2 trước khi chạy smoke toàn tuyến.
- Hành động tiếp: ghép các nhánh schema, quán và `day`, rồi chạy smoke file kho cá thể và kiểm thử đơn vừa ươn tại commit bàn giao.
- QA (`hungdt31`), bài học từ lần đổi schema kho: các lát merge vào `main` khi test đỏ (20/78 ở `39be0e1`), vì mỗi lát chỉ chạy test của mình. Đổi schema là thay đổi phá vỡ, nên **người đổi schema phải chạy toàn bộ test và chuyển fixture cùng PR**, hoặc báo QA trước khi merge. Hai lát dùng chung một giao diện (`day.py` gọi `GatherSim(item_ids=…)`) mà không ai chạy thử cùng nhau, nên lỗi id `I1` lặp mỗi Ngày chỉ lộ ra khi smoke 5 Ngày. **Hành động Phase 4:** CI bắt buộc xanh trước khi merge (người nhận: Integrator `tranha1764`); chạy `tools/qa_autoplay.py` + `qa_check_day.py` trước mỗi tag (người nhận: `hungdt31`).

## Phase 4 (cuối)
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
- Điều tốt / điều tệ:
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
- Một lần AI sai và cách nhóm phát hiện:
- Nếu làm lại, đổi gì:
- `nguyenquangtiep`: 4 commit đầu của tôi bị GitHub tính cho tài khoản phụ `asuradeva-afk`, vì git trên máy ghi email của tài khoản đó, dù tôi push bằng `nguyenquangtiep`. Tôi chỉ phát hiện khi rà trang Contributors ở Phase 4. Lần sau mỗi người nên chạy `git config user.email` và mở trang Contributors ngay sau commit đầu tiên của Phase 1.
