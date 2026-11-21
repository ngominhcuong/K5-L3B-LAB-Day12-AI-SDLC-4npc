# ngominhcuong — phản tư cá nhân

- Tôi đã làm:
  - Phase 1: Lát 4 Quán (`chonoi/sim/quan.py` — nấu, bưng, phục vụ, tiền, boa, uy tín, đóng ca; `tests/test_quan_slice4.py`) và tài liệu nhóm ([bfe5b89](https://github.com/ngominhcuong/K5-L3B-LAB-Day12-AI-SDLC-4npc/commit/bfe5b89)).
  - Phase 2: Nâng `game.contract.json` v1.1, triển khai `--mode day`, Shop nâng cấp, `pause`/`resumed` (`chonoi/sim/day.py`, `chonoi/runner.py`, `chonoi/headless.py`, `tests/test_day_shop_pause.py`) ([c40042a](https://github.com/ngominhcuong/K5-L3B-LAB-Day12-AI-SDLC-4npc/commit/c40042a)).
  - Phase 3: Lập kế hoạch ([6569382](https://github.com/ngominhcuong/K5-L3B-LAB-Day12-AI-SDLC-4npc/commit/6569382)), chốt `base_price` & `tip` theo độ tươi, giữ `IdAllocator` họ `I` xuyên Ngày ([30d03cb](https://github.com/ngominhcuong/K5-L3B-LAB-Day12-AI-SDLC-4npc/commit/30d03cb)).
  - Phase 4: Triển khai `chonoi/soak.py` (chạy 10 Ngày lặp kế hoạch D1–D5, `tests/test_soak.py`) ([8e82507](https://github.com/ngominhcuong/K5-L3B-LAB-Day12-AI-SDLC-4npc/commit/8e82507)).
- Tôi đã review & phối hợp: Giải quyết conflict và ghép sạch Lát 3 + Lát 4 trên `chonoi/sim/quan.py` qua các phase.
- AI sai ở đâu và tôi phát hiện thế nào: Ở Phase 1, test `ready_ticks` của AI tính nhầm số tick sau khi chín (5 thay vì 4) do không trừ tick chuyển sang `ready`; ở Phase 2, thiếu truyền `day` sang `GatherSim` cho Cá Sấu M2. Tôi tự đọc lại diff và chạy unit test để sửa.
- Điều tôi học được: Khóa hợp đồng sớm và giữ ranh giới hàm rõ giúp giảm conflict khi nhiều người sửa chung file.
