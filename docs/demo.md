# Kịch bản Demo ≤ 5 phút (sau 3:00)

Dùng cho demo trực tiếp hoặc quay video `.mp4`, theo checklist của TICKET-04. Người dẫn: `hungdt31`. Nên mở sẵn 2 terminal và trình duyệt trước khi bắt đầu.

**Chuẩn bị (trước giờ demo):**
```bash
git clone <repo> && cd <repo> && git checkout phase-4
PYTHONPATH=tests:. python3 -m unittest discover -s tests   # chạy thử một lần cho nóng máy
```

| Thời gian | Nội dung | Thao tác / lời nói |
|---|---|---|
| 0:00–0:20 | Giới thiệu | "Quán Ăn Chợ Nổi, nhóm 4npc, 6 người, 4 phase. Một Ngày gồm lặn và hái → mở quán → Shop." |
| 0:20–2:20 | **Chơi một Ngày đến khi đóng Shop** | Terminal 1: `python3 -m chonoi.live --mode day`, mở địa chỉ in ra. **Lặn & Hái**: hái bông súng N3 (E), lặn bắt cá lóc (Space); chỉ HUD độ tươi, oxy, "Thủy quái!" khi lại gần Cá Sấu; về bến (E). **Mở Quán**: nấu ở bếp, bưng, phục vụ; chỉ giá chốt theo độ tươi, kiên nhẫn của khách. Nếu thời gian ca dài, nói rõ "ca 180 s, tua nhanh trong video". **Shop**: mua `oxygen` nếu đủ tiền, nhấn "Xong" để đóng Shop → sang DayIntro Ngày 2. Chỉ 3 cảnh báo chữ: "Thủy quái!" (Cá Sấu đuổi), "Hết hơi!" (oxy < 25%), "Sắp rời bàn" (khách còn ≤ 20% kiên nhẫn). Bật chế độ tương phản cao nếu UI đã có. |
| 2:20–3:00 | **Chạy test, cho thấy đạt** | Terminal 2: `PYTHONPATH=tests:. python3 -m unittest discover -s tests` → `Ran 88 tests … OK`. Sau đó `python3 -m chonoi.soak --seed 7 --days 10 --out soak.json` → `days_completed=10 crashes=0` (≈ 6 s). |
| 3:00–4:00 | **Bằng chứng chia việc và đóng góp** | Mở `TEAM.md` (vai, người dự phòng) → `docs/plan/phase-1..3.md` (việc theo người) → `git shortlog -sn --all` → GitHub *Pull requests (closed)*: mỗi lát một PR. Chỉ `docs/members/*.md` của 6 người. |
| 4:00–4:45 | **Ma trận truy vết → bằng chứng** | Mở `docs/verification/phase-4.md`: chọn `AC-P4-03` (soak) → bấm link `docs/proof/phase-4/soak.json`. Mở `docs/verification/phase-3.md`: chọn dòng "Id `I1..` xuyên Ngày" → `docs/proof/phase-3/day5-ids.log`. Nhắc 3 bug QA bắt được ở P3 (crash, id lặp) và test đỏ trước khi sửa. |
| 4:45–5:00 | Kết | Giới hạn đã biết (xem Release notes) và một bài học từ retro. |

**Dự phòng nếu demo trực tiếp lỗi:** mở `docs/proof/phase-3/integration.md` (bảng một Ngày đã chạy headless) và chạy `python3 -m chonoi.headless --mode day --days 1 --seed 1 --ticks 30000 --out d.jsonl`, rồi `tail -1 d.jsonl` để thấy `days_complete`.
