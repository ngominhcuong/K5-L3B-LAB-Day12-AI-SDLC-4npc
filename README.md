# Day 12 — AI SDLC: Quán Ăn Chợ Nổi

> **Làm theo nhóm 4–6 người** · Dùng AI để xây game 2D qua **4 phase** trong **3 giờ**: Út Sen lặn bắt cá, hái rau trên mặt nước rồi tối mở quán phục vụ khách.
> **Yêu cầu từng phase mở đúng mốc giờ tại lab board:** **[Chợ Nổi Lab](https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg)** (cần đăng nhập claude.ai; có trợ giảng AI cho từng phase).

## Bắt buộc (chỉ có thế)

Cách làm việc kỹ thuật là **tự do** (push thẳng, nhánh + PR, pair, có hay không CI…). Cái bắt buộc:

1. **Một repo chung:** trưởng nhóm **fork** repo này, đặt tên `K5-L3B-LAB-Day12-AI-SDLC-<ten-nhom>`, thêm mọi thành viên làm collaborator (*Settings → Collaborators*, quyền Write) và để repo **public** (giảng viên xem được, không cần mời).
2. **Cả nhóm cùng commit** bằng tài khoản GitHub của mình, mỗi người **≥ 3 commit có nội dung** (làm cặp thì ghi `Co-authored-by:`).
3. **Điền [`TEAM.md`](TEAM.md):** danh sách thành viên + thỏa thuận làm việc nhóm; sửa `team_size` trong [`game.contract.json`](game.contract.json). Commit của người không có trong `TEAM.md` không được tính.
4. **Gắn tag** `phase-1` … `phase-4` đúng hạn; chạy được tại từng tag.
5. **Ghi chép tối thiểu:** `docs/verification/phase-n.md`, `docs/clarify.md`, `docs/ai-usage-log.md`, `docs/retro.md`, `docs/members/<handle>.md`.

## Bắt đầu nhanh

Chuẩn bị Python 3.12+ và trình duyệt hiện đại. Game, headless và soak dùng thư viện chuẩn Python.

```bash
git clone https://github.com/ngominhcuong/K5-L3B-LAB-Day12-AI-SDLC-4npc.git
cd K5-L3B-LAB-Day12-AI-SDLC-4npc
python3 -m chonoi.live --mode day --days 2
```

Mở `http://127.0.0.1:8000/` và nhấn **Enter**. Dùng **WASD** hoặc **mũi tên** để di chuyển, **E** để tương tác, **Space** để bắt cá, **P/Esc** để tạm dừng, **R** để chơi lại và **H** để bật/tắt tương phản cao. Trong Shop, **1** mua oxy, **2** mua máu và **E/Enter** đóng Shop.

## Test, headless và benchmark

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out gather.jsonl
python3 -m chonoi.soak --seed 7 --days 10 --out soak.json
```

Headless hỗ trợ `gather`, `quan` và `day`. Với `day`, dùng `--days 1..5`. Trên Windows, dùng `python -X utf8` thay cho `python3` và đặt `$env:PYTHONPATH = 'tests;.'` trước khi chạy test.

Benchmark cần Playwright và Chromium, cài trong cùng môi trường Python.

```bash
python3 -m pip install playwright
python3 -m playwright install chromium
python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json
```

Benchmark đo canvas 1280×720 sau 3 giây làm nóng. [Lệnh kiểm chứng và đóng gói](docs/release/phase-4.md) · [Khung Python của lab](docs/STARTER.md)

## Tự do sáng tạo

Ngoài phần đề yêu cầu, nhóm được **thêm** nhân vật, loài cá/cây, sinh vật, món, bản đồ, cơ chế, câu chuyện, đồ họa, âm nhạc… với ba điều kiện: **không phá phần cố định** (tắt ở headless), ghi mục **"Sáng tạo của nhóm"** trong README của nhóm, và **làm lõi đúng trước**.

### Sáng tạo của nhóm

- Cảnh minh họa trong trình duyệt, chẳng hạn `/?demo=fish` để thấy mục tiêu bắt cá và `/?demo=serve` trong chế độ `quan` để thấy mục tiêu phục vụ.
- Giảm chuyển động theo thiết lập `prefers-reduced-motion` của trình duyệt, giảm nội suy và các hiệu ứng lặp.

## Lịch 3 giờ

| Mốc | Phase | Hạn tag |
|---|---|---|
| 0:00 | Phase 1 (PRD-0) | `phase-1` trước 1:00 |
| 1:00 | Phase 2 | `phase-2` trước 1:55 |
| 1:55 | Phase 3 | `phase-3` trước 2:30 |
| 2:30 | Phase 4 | `phase-4` + Release `v1.0.0` trước 3:00 |

Hết giờ mỗi phase thì gắn tag rồi đi tiếp; chỗ chưa xong ghi trung thực trong bằng chứng.

## Đánh giá (100 điểm)

| Hạng mục | Điểm |
|---|---|
| Test tự động ẩn (headless, gồm kiểm tra lại phase trước) | 25 |
| Làm việc nhóm (một repo chung, chia việc, tích hợp, đổi yêu cầu) | 25 |
| Kiểm chứng & bằng chứng | 15 |
| Harness AI (AGENTS.md, skill, nhật ký dùng AI) | 10 |
| Đánh giá & retro | 10 |
| Chất lượng sản phẩm (đúng yêu cầu, mở rộng/sáng tạo) | 10 |
| Demo | 5 |

## Quy định

- Dùng AI thoải mái; **không sao chép repo của nhóm khác**; bằng chứng phải thật.
- Nhân vật, bối cảnh là bản gốc của lab; asset ngoài chỉ dùng CC0/CC-BY/MIT hoặc tự tạo, ghi nguồn trong `CREDITS.md`. Không commit API key, token, `.env`.
