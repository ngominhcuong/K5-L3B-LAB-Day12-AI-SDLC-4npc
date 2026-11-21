# Changelog

Định dạng theo [Keep a Changelog](https://keepachangelog.com/vi/1.1.0/). Phiên bản game bám theo Test Contract (`contract_version` trong `game.contract.json`).

## [Unreleased]

## [phase-4] Test Contract v1.3 · TICKET-04 "Phát hành v1.0.0" (đang làm)

### Added
- `soak_cmd` = `python3 -m chonoi.soak --seed <int> --days <N> --out <soak.json>` (`ngominhcuong`):
  - Chạy N Ngày bằng bot tất định trong một tiến trình.
  - Xuất `soak.json` gồm `{days, days_completed, crashes, results[{day, earned, reputation, score}], duration_s}`.
  - Mã thoát `0` khi hoàn tất, `1` khi có lỗi hoặc chưa hoàn tất, `2` khi đầu vào sai.
- `contract_version: "1.3"`, khai `soak_cmd`. Gameplay, tuning, kho, JSONL giữ như v1.2 (output giống từng byte bằng chứng P3).
- Kịch bản demo `docs/demo.md`; công cụ QA `tools/qa_soak_trace.py`.

### Changed
- `--mode day` cho Ngày 6+ dùng lại kế hoạch D1–D5 (Ngày n dùng D((n − 1) mod 5 + 1)). Headless vẫn giới hạn `--days 1..5`.

### Chưa xong
- `bench_cmd`, chế độ tương phản cao, README hướng dẫn chạy, `LICENSE`, Release v1.0.0.

## [phase-3] Test Contract v1.2 · Change Request "Mùa Nước Nổi"

### ⚠️ Breaking: schema kho đổi từ đếm theo loại sang **kho cá thể**

| Nơi | v1.1 | v1.2 |
|---|---|---|
| File kho (`--inventory`, `--inventory-out`, `gather_end.inventory`) | `{"items": {"ca_loc": 1, "bong_sung": 2}}` | `{"items": [{"id": "I1", "kind": "ca_loc", "fresh": 97.5}, ...]}`, sắp theo `id` |
| Scenario `gather.hold` | `["ca_loc", "bong_sung"]` | `[{"id", "kind", "fresh"}, ...]`, cuối mảng là mới nhất (LIFO) |
| Scenario `quan.stock` | `{"ca_loc": 1}` | `[{"id", "kind", "fresh"}, ...]` |
| `customers[].reserved` | `{"ca_loc": 1}` | mảng id `["I1"]` |
| Snapshot `hold`, `stock`; `lost` trong `monster_hit` / `faint` | chuỗi / đếm | cá thể |
| Kho rỗng | `{"items": {}}` | `{"items": []}` |

- Kho **dạng đếm cũ bị từ chối với mã thoát 2**. Các trường hợp sau cũng ra mã 2: thiếu `fresh`, `fresh` ngoài `[0, 100]`, `id` trùng, `kind` lạ.
- `id` là chuỗi duy nhất trong mỗi kho. Mỗi `id` chỉ được giữ cho tối đa một đơn.

### Added
- `tuning.freshness`: `initial: 100`, `gather_decay_per_s: 0.5`, `quan_decay_per_s: 0.25`, `spoiled_below: 30`.
- Độ tươi từng cá thể:
  - Hao **ở đầu mỗi bước**, kẹp đáy 0. Hàng vừa nhặt hoặc bắt có `fresh = 100` và bắt đầu hao từ bước sau.
  - **Ươn khi `fresh < 30`**; đúng 30 vẫn dùng được. Hàng ươn vẫn nằm trong kho nhưng không được giữ chỗ hay nấu.
  - `pause` thì không hao; chuyển pha không hao thêm.
- Event `spoiled {item_id, kind, location: "hold" | "stock"}`, phát một lần khi vừa ươn, sắp theo `id`.
- Giữ chỗ theo `id`:
  - Chọn cá thể tươi nhất, hòa thì `id` nhỏ hơn. Đơn chưa khai giữ chỗ được cấp theo `(order_tick, table_id)`.
  - Hàng đang giữ mà ươn thì nhả ra và giữ lại đúng 1 lần; không đủ hàng thì đơn thành `unfulfillable`.
- **Giá chốt theo độ tươi** lúc `cook_started`: `base_price = floor(giá niêm yết × avg_fresh / 100)`. `items` sắp theo `(kind, id)`. `tip` tính trên giá đã chốt.
- `--mode day`: id họ `I` **nối tiếp xuyên Ngày**. Ngày 1 giữ id trong scenario mẫu; từ Ngày 2 cấp id mới, không dùng lại.
- HUD: hiện độ tươi từng cá thể, cảnh báo **Ươn (< 30)**, báo khi có hàng ươn, hiện giá món thực tế.

### Fixed (phát hiện khi kiểm chứng Phase 3)
- Quán crash (exit 1) khi scenario có khách chưa khai `reserved` và kho đến từ `--inventory` (`760cb34`).
- Snapshot pha Shop crash khi còn kho dư dạng cá thể (`760cb34`).
- Id cá thể quay về `I1` mỗi Ngày trong `--mode day` (`32883d0`).

### Cách cập nhật fixture/test từ v1.1 lên v1.2
1. Dựng kho bằng helper trong `tests/helpers.py`:
   - `items("ca_loc", "bong_sung")` → `[{"id": "I1", ...}, {"id": "I2", ...}]`, mặc định `fresh = 100`; có thể truyền `fresh=` và `start=`.
   - `stock_of({"ca_loc": 1, "bong_sung": 2})` đổi kho đếm cũ sang mảng cá thể.
2. So kết quả theo loại bằng `kinds(...)` (giữ thứ tự) hoặc `kind_counts(...)` (đếm). Nếu cần kiểm LIFO thì so theo `id`.
3. Kho rỗng là `{"items": []}`. `reserved` là mảng id.
4. Đừng so `fresh` bằng số cứng sau khi đã chạy vài bước. Tính từ contract (`freshness.*_decay_per_s / tick_hz`). Riêng giá chốt thì dùng `helpers.locked_price(...)`, lưu ý quán đã hao 1 bước khi nấu ở bước 0.
5. Commit đổi test phải ghi lý do (quy tắc trong `AGENTS.md`); xem ví dụ ở `8da292b`.

## [phase-2] Test Contract v1.1 · TICKET-02 "Một ngày ở chợ nổi"

### Added
- Số liệu chuẩn:
  - 6 nguyên liệu (thêm `ca_keo`, `keo_neo`, nút N5/N6), 6 món, 2 bếp (B1, B2), 4 bàn (T1–T4).
  - Cá bơi 1.5 m/s, phản xạ ở mép, đổi hướng mỗi 120 bước. Sinh cá mỗi 360 tick (đầu ca 8 đàn, trần 12), event `fish_spawned`.
- Cá Sấu Năm Chèo:
  - M1 từ Ngày 1, M2 từ Ngày 3; trạng thái `patrol` / `chase` / `recoil`.
  - Mỗi cú hit trừ 1 Máu, rơi `floor(n/2)` món theo LIFO, bất tử 90 tick. Event `monster_hit {monster_id, hp, lost, pos}`, `faint(cause: "monster")`.
- `--mode day --days 1..5`:
  - Vòng `day_start → day_plan → gather → quan → shop`, kế hoạch D1–D5.
  - Shop nâng cấp `oxygen` / `hp`, có hiệu lực từ Ngày kế; `buy_failed`; Shop tự đóng sau 600 tick.
- `pause` / `resumed` ở cả 3 mode.
- Menu chính, DayIntro, EveningIntro, DayResult, Summary, menu Pause, HUD sáng/tối.

### Changed
- `fish_initial` từ danh sách 6 đàn thành số `8`. Bắt cá chỉ xét đàn gần nhất và cần đủ chỗ cho cả đàn.

### Fixed
- `monster_hit` trước thiếu `pos` và thừa `kind` so với Test Contract (`d4ce64e`).

## [phase-1] Test Contract v1.0 · PRD-0

### Added
- Buổi sáng `gather`: bơi (ramp ≤ 6 tick), oxy và ngạt, hái nút (mọc lại sau 20 s), bắt cá có hồi, giỏ 12 ô LIFO, cập bến, hết giờ.
- Buổi tối `quan`: khách đến theo lịch và giữ nguyên liệu, kiên nhẫn, bếp, bưng, phục vụ, boa, uy tín, hết ca.
- Nối kho 2 tiến trình: `gather --inventory-out` → `quan --inventory`.
- Headless theo Test Contract (tất định theo seed) và cửa sổ chơi `chonoi.live`.
