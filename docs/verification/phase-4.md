# Ma trận truy vết Phase 4 (TICKET-04 · Phát hành v1.0.0 · Test Contract v1.3)

- **QA:** `hungdt31` · **Commit được kiểm:** `main` `54a98cf` + khai contract 1.3 (nhánh `qa/p4-verification`) · Python 3.14.4 / Linux.
- Ticket không đánh số AC, nên QA đặt mã `AC-P4-xx` theo thứ tự mục trong TICKET-04 và DoD.
- **Phải chạy lại bảng này trên commit gắn tag `phase-4`** trước 3:00, rồi sửa cột Kết quả nếu khác.

| AC | Yêu cầu (TICKET-04) | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|---|
| AC-P4-01 | `contract_version: "1.3"`; khai `bench_cmd` và `soak_cmd` ở gốc `game.contract.json` | Đọc contract; `python3 tools/check_team.py` | [game.contract.json](../../game.contract.json), [check_team.log](../proof/phase-4/check_team.log) | **Một phần**: QA khai `1.3` và `soak_cmd` trong PR này; **chưa có `bench_cmd`** |
| AC-P4-02 | `bench_cmd --seed 42 --duration 30 --out bench.json` chạy cảnh lõi có render 1280×720 (làm nóng 3 s, đo 30 s), xuất `avg_fps`, `p1_low_fps`, `frames`, `measured_s`, `load_ms` | Chạy lệnh; tính lại `avg_fps = frames / measured_s`; báo cáo các mốc 60 / 30 FPS và load ≤ 10 s | `docs/proof/phase-4/bench.json` (chưa có) | **Chưa đạt**: chưa có lệnh (xem "Rủi ro") |
| AC-P4-03 | `soak_cmd --seed 7 --days 10 --out soak.json` có `days, days_completed, crashes, results[{day, earned, reputation, score}], duration_s`; đạt khi `days_completed = days` và `crashes = 0`; tất định ở trường gameplay | Chạy 2 lần, so mọi trường trừ `duration_s`; tham số sai; `tests/test_soak.py` | [soak.json](../proof/phase-4/soak.json), [soak-run2.json](../proof/phase-4/soak-run2.json), [soak.log](../proof/phase-4/soak.log) | **Đạt**: 10/10 Ngày, 0 crash, ~6 s; hai lần giống nhau; `--days 0` / `x` / thiếu cờ → mã 2 |
| AC-P4-04 | Mỗi Ngày đi qua gather → quan → shop; D1–D5 lặp ở Ngày 6–10; tiền, tổng thu, uy tín, nâng cấp, số Ngày, id cá thể tiếp tục | `tools/qa_soak_trace.py 7 10`: chạy đúng `chonoi.soak.run_soak` và ghi lại event | [soak-trace.log](../proof/phase-4/soak-trace.log) | **Đạt**: `day_plan` 9/9 Ngày (2–10) khớp D((n−1) mod 5 + 1); id `I1..I40` không trùng; mỗi Ngày có `phase_start` quan và shop; `oxygen` mua ở Ngày 8 có hiệu lực từ Ngày 9; `earned` không giảm (43 → 258) |
| AC-P4-05 | Gameplay, tuning, kho, JSONL giữ như v1.2 | Chạy lại inputs P3 với contract 1.3, `cmp` với bằng chứng P3 | [regression-smoke.log](../proof/phase-4/regression-smoke.log) | **Đạt**: integration gather/kho/quan và day5 giống **từng byte** P3; 23/23 giá chốt đúng |
| AC-P4-06 | Regression P1–P3 còn hiệu lực đạt | `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`; `tools/qa_check_day.py` | [unittest.log](../proof/phase-4/unittest.log), regression-smoke.log | **Đạt**: 88/88; 5 Ngày kho bàn giao đúng, không có đơn ngoài kế hoạch, Cá Sấu đúng |
| AC-P4-07 | Ba cảnh báo dùng chữ hoặc biểu tượng; có chế độ tương phản cao; chơi thử cả ba ở chế độ đó | Đọc code UI + chơi thủ công | `chonoi/web/index.html`: "Thủy quái!" (Cá Sấu `chase`), "Hết hơi!" (oxy < 25%), "Sắp rời bàn" (kiên nhẫn ≤ 20%) | **Một phần**: 3 cảnh báo chữ **có**; **chưa có chế độ tương phản cao**; QA chưa chụp ảnh chơi thử |
| AC-P4-08 | Từ clone sạch, chạy bản có giao diện theo `README.md` trong ≤ 3 lệnh (macOS/Linux); README ghi môi trường, điều khiển, lệnh test, headless, benchmark | Clone sạch rồi chạy test, soak, `chonoi.live --mode day` (kiểm `GET /` 200 và `/state`) | [clean-clone.log](../proof/phase-4/clean-clone.log) | **Một phần**: chạy được, không cần cài gói (`git clone`, `cd`, `python3 -m chonoi.live --mode day`); **README chưa cập nhật** lệnh, điều khiển, benchmark |
| AC-P4-09 | Release v1.0.0 có bản đóng gói và release notes; `CHANGELOG.md` theo phase; rà `CREDITS.md`, `LICENSE` | Xem Release, các file | [CHANGELOG.md](../../CHANGELOG.md) | **Một phần**: CHANGELOG có phase-1..4; **chưa có Release, `LICENSE`** |
| AC-P4-10 | Tag `phase-4` và Release v1.0.0 cùng trỏ một commit trên `main`, trước 3:00 | `git ls-remote --tags origin` | | **Chưa**. `phase-1` → `9b691bd`, `phase-2` → `285cdc9` (đúng); **`phase-3` → `39be0e1` (đỏ 20/78)**, bản xanh là `a7a8ccd` |
| AC-P4-11 | Cập nhật clarify, ai-usage-log; retro rà hành động P2; `docs/members/<handle>.md` đủ 6 người | Đọc file | [clarify.md](../clarify.md), [ai-usage-log.md](../ai-usage-log.md), [members/](../members/) | **Một phần**: QA đã cập nhật phần mình; retro P4 và phản tư của người khác do từng người viết |
| AC-P4-12 | Mở rộng (nhóm 6 người ≥ 2 mục) có test và bằng chứng | | | **Chưa làm** |

## Rủi ro / việc cần chốt người nhận trước 3:00

- **`bench_cmd` (AC-P4-02):** cảnh render nằm trong trình duyệt (`index.html`, canvas + `requestAnimationFrame`). Đề xuất (clarify #9):
  - Thêm chế độ `?bench=1`: ghi thời gian từng khung hình sau 3 s làm nóng, đo 30 s, rồi `POST /bench` về `chonoi.live`.
  - `chonoi/bench.py` mở trình duyệt 1280×720 và tính 5 trường.
  - QA đã thử Firefox headless trên máy QA, nhưng đó là bản snap: chặn profile trong `/tmp` và chặn tín hiệu dừng. Người làm bench nên thử trên máy có Chrome/Firefox bản thường.
- **Chế độ tương phản cao (AC-P4-07):** lát UI.
- **README, `LICENSE`, Release v1.0.0, tag `phase-4` (AC-P4-08..10):** vai Đóng gói / Release. Nên gắn lại `phase-3` vào `a7a8ccd`.
