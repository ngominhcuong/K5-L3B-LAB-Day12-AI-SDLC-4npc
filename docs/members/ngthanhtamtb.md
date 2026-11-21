# ngthanhtamtb — phản tư cá nhân

- Tôi đã làm (kèm link commit):
  - Phase 1: Lát 2 `sim/gather` — hái nút, bắt cá, giỏ LIFO và `tests/test_gather_rules.py` (`75a5a92`).
  - Phase 2: Cá Sấu Năm Chèo (`M1`/`M2`, `patrol`/`chase`/`recoil`, rơi `floor(hold/2)` LIFO, `invuln_ticks: 90`, `faint(cause: "monster")`), `tests/test_gather_monsters.py` và `docs/clarify.md` (`797186e`); sửa validate `invuln_ticks` & test v1.1; làm lại giao diện Anime Ghibli, tối ưu nội suy 60 Hz (`e410a09`, `b594851`), nối `--mode day`/`pause`/`shop` + camera 2D + minimap + HUD nổi (`3fbf4b1`).
  - Phase 3: Hiển thị độ tươi cá thể, cảnh báo hàng ươn (`< 30`), sự kiện `spoiled` và giá món thực tế (`a0613bb`).
  - Phase 4: Bổ sung chế độ tương phản cao (`[C]`, `AC-P4-07`), chốt các mục PO trong `docs/clarify.md` và hoàn thiện log AI.
- Tôi đã review (kèm link):
  - Rà soát `chonoi/scenario.py`, `chonoi/sim/gather.py`, `chonoi/live.py` khi ghép contract `v1.1` và `v1.2`, kiểm tra lại luồng `day` và giao diện trực tiếp trên trình duyệt.
- AI sai ở đâu và tôi phát hiện thế nào:
  - Khi thêm camera zoom ở `gather`, AI khai báo trùng `const p = snap.player` gây `SyntaxError` trắng màn hình; phát hiện ngay khi mở chơi thử và kiểm bằng `node --check`.
  - Lần đầu tạo hình Cá Sấu Năm Chèo còn đơn giản và nhân vật hơi nhỏ; kiểm tra trực quan trên `chonoi.live` để yêu cầu chỉnh tỷ lệ và chi tiết lại.
  - AI từng viết thiếu kiểm tra `d >= 10` và hướng `recoil +x` khi trùng tâm; phát hiện khi đối chiếu từng dòng với đặc tả Phase 2.
- Điều tôi học được:
  - Luôn đối chiếu từng điều kiện biên trong spec (độ sâu, hướng lùi, thứ tự ưu tiên) và chạy `node --check` + `unittest` đầy đủ trước khi commit.
