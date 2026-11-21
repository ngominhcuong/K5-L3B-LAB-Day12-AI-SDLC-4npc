# Ma trận truy vết Phase 4 (TICKET-04 · Phát hành v1.0.0 · Test Contract v1.3)

- **Kiểm chứng lần này:** `tranha1764`, nhánh `feat/p4-integrator-release` dựa trên `main` `436fdfa`. [Log kiểm lại](../proof/phase-4/integrator-release.log)
- **Bằng chứng lịch sử:** `hungdt31` kiểm `54a98cf` + khai contract 1.3 bằng Python 3.14.4 / Linux.
- Ticket không đánh số AC, nên QA đặt mã `AC-P4-xx` theo thứ tự mục trong TICKET-04 và DoD.
- **Phải chạy lại bảng này trên commit gắn tag `phase-4`** trước 3:00, rồi sửa cột Kết quả nếu khác.

| AC | Yêu cầu (TICKET-04) | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|---|
| AC-P4-01 | Contract v1.3 khai `bench_cmd` và `soak_cmd` ở gốc manifest | Đọc manifest và chạy hai lệnh đã khai | [Manifest](../../game.contract.json) | **Đạt**. Có đủ ba khóa |
| AC-P4-02 | Benchmark canvas 1280×720, làm nóng 3 s và đo 30 s, xuất đủ năm trường | Seed `42`, kiểm công thức FPS và mốc tải cảnh | [JSON đo thật](../proof/phase-4/integrator-bench.json) | **Đạt local**. FPS trung bình và 1% low vượt mốc 60/30, tải dưới 10 s |
| AC-P4-03 | `soak_cmd --seed 7 --days 10 --out soak.json` có `days, days_completed, crashes, results[{day, earned, reputation, score}], duration_s`; đạt khi `days_completed = days` và `crashes = 0`; tất định ở trường gameplay | Chạy 2 lần, so mọi trường trừ `duration_s`; tham số sai; `tests/test_soak.py` | [soak.json](../proof/phase-4/soak.json), [soak-run2.json](../proof/phase-4/soak-run2.json), [soak.log](../proof/phase-4/soak.log) | **Đạt**: 10/10 Ngày, 0 crash, ~6 s; hai lần giống nhau; `--days 0` / `x` / thiếu cờ → mã 2 |
| AC-P4-04 | Mỗi Ngày đi qua gather → quan → shop; D1–D5 lặp ở Ngày 6–10; tiền, tổng thu, uy tín, nâng cấp, số Ngày, id cá thể tiếp tục | `tools/qa_soak_trace.py 7 10`: chạy đúng `chonoi.soak.run_soak` và ghi lại event | [soak-trace.log](../proof/phase-4/soak-trace.log) | **Đạt**: `day_plan` 9/9 Ngày (2–10) khớp D((n−1) mod 5 + 1); id `I1..I40` không trùng; mỗi Ngày có `phase_start` quan và shop; `oxygen` mua ở Ngày 8 có hiệu lực từ Ngày 9; `earned` không giảm (43 → 258) |
| AC-P4-05 | Gameplay, tuning, kho, JSONL giữ như v1.2 | Chạy lại inputs P3 với contract 1.3, `cmp` với bằng chứng P3 | [regression-smoke.log](../proof/phase-4/regression-smoke.log) | **Đạt**: integration gather/kho/quan và day5 giống **từng byte** P3; 23/23 giá chốt đúng |
| AC-P4-06 | Regression P1–P3 còn hiệu lực | Unittest, smoke headless và `tools/qa_check_day.py` | [Log kiểm lại](../proof/phase-4/integrator-release.log) | **Đạt local**. 92/92 test, 5 lượt bàn giao kho đúng và 23 giá chốt hợp lệ |
| AC-P4-07 | Có tương phản cao và thử đủ ba cảnh báo | Bật/tắt bằng H trong Chromium với scenario có cảnh báo thật | [Gather](../proof/phase-4/contrast-gather.png), [Quán](../proof/phase-4/contrast-quan.png) | **Đạt local**. Cả ba cảnh báo có chữ vàng, biểu tượng ⚠ và nền đen |
| AC-P4-08 | Chạy UI từ checkout sạch trong ≤ 3 lệnh macOS/Linux, ghi đủ môi trường, phím chơi, test, headless, benchmark | Rà README và smoke `GET /`, `GET /state` | [README](../../README.md), [bằng chứng clone sạch](../proof/phase-4/clean-clone.log) | **Đạt local**. Chạy lại ở checkout của tag khi phát hành |
| AC-P4-09 | Release v1.0.0 có bản đóng gói, release notes, CHANGELOG, CREDITS và LICENSE | Rà tài liệu và giải nén chạy thử | [Hướng dẫn phát hành](../release/phase-4.md), [Credits](../../CREDITS.md) | **Một phần**. Giấy phép và GitHub Release đang chờ |
| AC-P4-10 | Tag `phase-4` và Release v1.0.0 cùng trỏ một commit trên `main`, trước 3:00 | `git ls-remote --tags origin` | | **Chưa**. `phase-1` → `9b691bd`, `phase-2` → `285cdc9` (đúng); **`phase-3` → `39be0e1` (đỏ 20/78)**, bản xanh là `a7a8ccd` |
| AC-P4-11 | Clarify, AI log, retro Phase 4 và đủ 6 phản tư | So với danh sách TEAM | [Clarify](../clarify.md), [AI log](../ai-usage-log.md), [Hồ sơ](../members/) | **Một phần**. Còn phản tư của `ngthanhtamtb` và `danhhieu204ns` |
| AC-P4-12 | Mở rộng (nhóm 6 người ≥ 2 mục) có test và bằng chứng | Kiểm `?demo=fish` và thiết lập `prefers-reduced-motion` trên trình duyệt | [README](../../README.md#sáng-tạo-của-nhóm), [log](../proof/phase-4/integrator-release.log) | **Hai mục có bằng chứng**. Chờ PO xác nhận tính vào chỉ tiêu |

## Kiểm lại sau khi xử lý xung đột

Bản merge local của `453b482` và `afb70a8` chạy trên Windows với Python 3.12.10. Các log trong bảng ghi kết quả lịch sử trên Linux.

- `python -m unittest discover -s tests -v` với `PYTHONPATH=tests;.` đạt 91/91, gồm cả `test_soak.py` và `test_soak_p4.py`.
- Hai lần chạy `python -m chonoi.soak --seed 7 --days 10 --out <file>` hoàn tất 10/10 Ngày và không có crash. Các trường gameplay khớp nhau và khớp [kết quả đã lưu](../proof/phase-4/soak.json). Mô phỏng crash sau Ngày 1 trả mã `1` và vẫn ghi kết quả của Ngày 1. Báo cáo chưa hoàn tất cũng trả mã `1`.
- `python tools/qa_soak_trace.py 7 10` với `PYTHONPATH=.` xác nhận 10/10 kế hoạch, thứ tự gather → quan → shop, 40 ID cá thể không trùng và `earned` không giảm. Nâng cấp `oxygen` có hiệu lực từ Ngày 9.
- Chạy lại [inputs Phase 3](../proof/phase-3/integration.md). Kho, JSONL của gather, quan và day5 khớp bản lưu sau khi chuẩn hóa xuống dòng. Cả 5 lượt bàn giao kho và 23 lần chốt giá đều đạt.

## Xác nhận trước khi phát hành

- Chạy CI và lấy duyệt PR theo thỏa thuận nhóm. Kiểm lại trên đúng commit đã merge trước khi gắn `phase-4` và tạo Release `v1.0.0`. [Hướng dẫn](../release/phase-4.md)
- Kiểm tra W/↑ đi lên và S/↓ đi xuống khi `day` chuyển vào quán. Chromium đã chạy ca giữ W qua lúc nhấn E cập bến. [Log kiểm lại](../proof/phase-4/integrator-release.log)
