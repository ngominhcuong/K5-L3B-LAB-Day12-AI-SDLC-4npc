# Chế độ tương phản cao (AC-P4-07) · `nguyenquangtiep`

**Cách bật:** nhấn **H** ở bất kỳ màn nào (menu, đang chơi, tạm dừng), hoặc mở `http://127.0.0.1:<port>/?contrast=high`. Trình duyệt nhớ lựa chọn trong `localStorage`; `?contrast=normal` để tắt. Menu chính và menu Tạm dừng có ghi phím H, kèm trạng thái đang bật hay đang tắt.

**Khi bật:**
- Cả khung hình được tăng tương phản (`contrast(1.25) saturate(1.15)`). Chữ màu sáng có viền đen dày 4 px.
- Ba cảnh báo dùng thẻ nền đen, viền vàng `#ffeb3b` dày 3 px, chữ vàng đậm 18 px và biểu tượng ⚠:
  - **"Thủy quái!"**: trên đầu Cá Sấu khi `chase` và ở giữa đầu màn hình.
  - **"Hết hơi!"**: khi oxy < 25%, dòng Oxy chuyển vàng và có thêm thẻ ⚠ ở giữa màn hình.
  - **"Sắp rời bàn"**: thẻ khách có kiên nhẫn ≤ 20%.
- Chỉ đổi cách vẽ ở client, không gửi input mới lên server, nên headless và JSONL không đổi.

## Kiểm chứng tự động (Node, canvas giả)
Trạng thái thật lấy từ `GET /state` của `python -m chonoi.live --mode gather|quan` (cả hai trả `GET /` 200). Sau đó ép đủ ba cảnh báo: Cá Sấu `chase`, oxy 200/1800 tick, khách còn 300 tick kiên nhẫn. Chạy `frame()` của `index.html` với canvas giả và ghi lại mọi chữ được vẽ (chuỗi, màu, font):

Mở thường, rồi nhấn H:
```
highContrast lúc đầu = false | canvas.filter = ""
gather: "Thủy quái!" #f2b8ff 700 12px ; "Oxy 4s · Hết hơi!" #ff6e54 700 16px
quan: "Cá lóc nướng trui · Sắp rời bàn · 5s" #ffab91 700 12px
sau phím H: highContrast = true | storage = high | filter = "contrast(1.25) saturate(1.15)"
gather: "⚠ Thủy quái!" #ffeb3b 800 18px ; "Oxy 4s · Hết hơi!" #ffeb3b 700 16px ; "⚠ Hết hơi!" #ffeb3b 800 18px
quan: "⚠ Cá lóc nướng trui · Sắp rời bàn · 5s" #ffeb3b 800 18px
```
Mở với `?contrast=high`:
```
highContrast lúc đầu = true | canvas.filter = "contrast(1.25) saturate(1.15)"
gather: "⚠ Thủy quái!" #ffeb3b 800 18px ; "Oxy 4s · Hết hơi!" #ffeb3b 700 16px ; "⚠ Hết hơi!" #ffeb3b 800 18px
quan: "⚠ Cá lóc nướng trui · Sắp rời bàn · 5s" #ffeb3b 800 18px
```
Chế độ thường giữ nguyên màu và font như trước. `node --check` hợp lệ; unittest Ran 91, OK.

## Chưa làm
- **Chơi thử bằng mắt cả ba cảnh báo trên trình duyệt thật** (yêu cầu của AC-P4-07): bước này **chưa chạy**. Kiểm chứng trên chỉ chứng minh đúng chữ, màu và cỡ được vẽ, không thay được việc nhìn thực tế. Cần chơi thử và chụp ảnh trước khi tag `phase-4`.
