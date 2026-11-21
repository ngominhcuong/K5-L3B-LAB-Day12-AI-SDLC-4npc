"""Bot chơi tất định: chỉ đọc snapshot (như người chơi nhìn HUD) rồi trả input cho bước kế.

Dùng cho soak (`python3 -m chonoi.soak`) và công cụ QA (`tools/qa_autoplay.py`).
Không dùng số ngẫu nhiên hay đồng hồ, nên cùng seed thì cùng chuỗi input.
"""

import math
from collections import Counter


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _toward(p, q, stop=0.4):
    dx, dy = q[0] - p[0], q[1] - p[1]
    d = math.hypot(dx, dy)
    if d <= stop:
        return [0, 0]
    return [round(dx / d, 3), round(dy / d, 3)]


class Bot:
    def __init__(self, tuning, want=None, buy_order=("oxygen", "hp", "oxygen", "hp")):
        self.g = tuning["gather"]
        self.shop = tuning.get("shop", {})
        self.want_fixed = want
        self.buy_order = list(buy_order)
        self.prev = {}          # nút đã giữ ở bước trước (để tạo cạnh lên)
        self.shop_step = 0

    # ---- gather ----
    def _gather(self, sn):
        g = self.g
        pl = sn["player"]
        p = pl["pos"]
        want = Counter(self.want_fixed or sn.get("day_plan", {}).get("ingredients", {}))
        # v1.2: hold là mảng cá thể {id, kind, fresh}; v1.1 là mảng chuỗi
        have = Counter(x["kind"] if isinstance(x, dict) else x for x in sn["hold"])
        need = {k: want[k] - have[k] for k in want if want[k] > have[k]}
        room = sn["hold_capacity"] - sn["hold_count"]
        speed = g["swim_speed"] / 60.0
        dock = g["dock_pos"]
        back_ticks = _dist(p, dock) / speed + p[1] / speed + 120
        out = {"move": [0, 0]}

        if not need or room <= 0 or sn["time_left_ticks"] < back_ticks:
            if _dist(p, dock) <= g["dock_radius"] - 0.5 and p[1] <= g["surface_depth"]:
                out["interact"] = True
            else:
                out["move"] = _toward(p, dock)
            return out

        # oxy: còn ít hơn thời gian ngoi lên + đệm thì ngoi lên
        underwater = p[1] > g["surface_depth"]
        if underwater and pl["oxygen_ticks"] < p[1] / speed + 90:
            out["move"] = [0, -1]
            return out
        if not underwater and pl["oxygen_ticks"] < pl["oxygen_max_ticks"] * 0.9 and self._last_target_fish:
            return out  # đứng ở mặt nước nạp oxy trước khi lặn tiếp

        cands = []
        for n in sn["nodes"]:
            if n["ready"] and need.get(n["kind"], 0) > 0:
                cands.append((_dist(p, n["pos"]), n["id"], "node", n))
        for f in sn["fish"]:
            y = g["fish_yield"][f["kind"]]
            # chỉ lặn nếu đủ oxy cho đi + về
            if need.get(f["kind"], 0) > 0 and y <= room and f["pos"][1] / speed * 2 + 120 < pl["oxygen_ticks"]:
                cands.append((_dist(p, f["pos"]) + 3, f["id"], "fish", f))
        if not cands:
            self.want_fixed = {}  # không còn gì lấy được → về bến
            out["move"] = _toward(p, dock)
            return out
        _, _, kind, tgt = min(cands, key=lambda c: (c[0], c[1]))
        self._last_target_fish = kind == "fish"
        if kind == "node":
            if _dist(p, tgt["pos"]) <= g["interact_radius"] - 0.5 and not underwater:
                out["interact"] = True
            else:
                out["move"] = _toward(p, tgt["pos"])
        else:
            d = _dist(p, tgt["pos"])
            if d <= g["catch_radius"] - 0.4 and underwater and pl["catch_cd_ticks"] == 0:
                out["catch"] = True
            out["move"] = _toward(p, tgt["pos"], stop=0.2)
        return out

    _last_target_fish = False

    # ---- quan ----
    def _quan(self, sn):
        p = sn["player"]["pos"]
        tables = {t["id"]: t["pos"] for t in sn["tables"]}
        out = {"move": [0, 0]}
        target = None
        if sn["hand"]:
            c = [c for c in sn["customers"] if c["id"] == sn["hand"]["order_id"]]
            if c:
                target = tables[c[0]["table_id"]]
        else:
            ready = [s for s in sn["stoves"] if s["state"] == "ready"]
            idle = [s for s in sn["stoves"] if s["state"] == "idle"]
            waiting = any(c.get("order_status") == "reserved" for c in sn["customers"])
            if ready:
                target = min(ready, key=lambda s: (_dist(p, s["pos"]), s["id"]))["pos"]
            elif idle and waiting:
                target = min(idle, key=lambda s: (_dist(p, s["pos"]), s["id"]))["pos"]
        if target:
            if _dist(p, target) <= 0.4:
                out["interact"] = True
            else:
                out["move"] = _toward(p, target)
        return out

    # ---- shop ----
    def _shop(self, sn):
        self.shop_step += 1
        if self.shop_step == 1:
            ups = self.shop.get("upgrades", {})
            for kind in list(self.buy_order):
                lvl = sn["upgrades"].get(kind, 0)
                if lvl < len(ups.get(kind, [])) and ups[kind][lvl]["price"] <= sn["money"]:
                    self.buy_order.remove(kind)
                    return {"buy": kind}
            return {}
        if self.shop_step == 3:
            return {"shop_done": True}
        return {}

    def decide(self, sn):
        phase = sn.get("phase", sn.get("mode"))
        if phase != "shop":
            self.shop_step = 0
        if phase == "gather":
            out = self._gather(sn)
        elif phase == "quan":
            out = self._quan(sn)
        else:
            out = self._shop(sn)
        # cạnh lên: không giữ một nút 2 bước liên tiếp
        for b in ("interact", "catch", "shop_done"):
            v = bool(out.get(b)) and not self.prev.get(b)
            out[b] = v
            self.prev[b] = v
        return out
