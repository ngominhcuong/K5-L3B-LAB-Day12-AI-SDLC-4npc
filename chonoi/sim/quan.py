"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Lát 3: khách đến theo lịch, chọn món nấu được, giữ chỗ nguyên liệu, kiên nhẫn,
       bỏ đi (customer_left), no_dish, vòng đời khách, hao tươi & ươn.
Lát 4: interact tại bếp/bàn (cook_started chốt giá theo tươi, dish_ready, dish_picked, served),
       ăn xong trả tiền (paid), boa, uy tín, hết ca (quan_end).
"""

import math
from fractions import Fraction

from ..ids import id_key, sort_by_id
from .ramp import ramp_velocity

TICK = 60.0


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None, day=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        # Trong vòng ngày, chỉ các món được ghi ở kế hoạch ngày mới được nhận đơn.
        # Chế độ quan độc lập giữ toàn bộ menu để thử từng món bằng fixture.
        if day is None:
            self.day_dishes = set(self.menu)
        else:
            from ..errors import BadInput
            plans = tuning["day_plan"]
            plan_day = ((day - 1) % len(plans)) + 1
            plan = next((p for p in plans if p["day"] == plan_day), None)
            if plan is None:
                raise BadInput(f"ngày không có trong day_plan: {day}")
            self.day_dishes = set(plan["dishes"])
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        source_stock = inventory if inventory is not None else scenario.get("stock", [] if "freshness" in tuning else {})
        self.individual_stock = "freshness" in tuning or isinstance(source_stock, list)
        if self.individual_stock:
            self.stock = [dict(item) for item in source_stock]
            fresh_cfg = tuning.get("freshness", {"quan_decay_per_s": 0.25, "spoiled_below": 30})
            self._fresh_step = (
                Fraction(str(fresh_cfg["quan_decay_per_s"])) / int(TICK)
                if "freshness" in tuning
                else Fraction(0)
            )
            # Giữ đúng giá trị fixture; chỉ sửa sai số biểu diễn sát bội số của một tick.
            self._fresh = {item["id"]: self._initial_fresh(item["fresh"]) for item in self.stock}
            self._spoiled_below = Fraction(str(fresh_cfg["spoiled_below"]))
        else:
            self.stock = dict(source_stock)
        self.hand = dict(scenario["hand"]) if scenario.get("hand") is not None else None
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.phase_tick = 0
        self.random_customers = scenario.get("random_customers", True)
        self.stoves = [dict(s, state=s.get("state", "idle"),
                            dish=dict(s["dish"]) if s.get("dish") is not None else None,
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        raw_customers = scenario.get("customers", [])
        self.customers = [self._init_customer(c) for c in raw_customers]
        # v1.2: đơn chưa khai giữ chỗ được cấp SAU khi đã có đủ danh sách khách (reserve_items đọc
        # self.customers để biết id nào đã bị giữ), theo (order_tick, table_id) như docs/clarify.md #3.
        if self.individual_stock:
            pending = [c for c, raw in zip(self.customers, raw_customers)
                       if c["order_status"] == "reserved" and "reserved" not in raw]
            for c in sorted(pending, key=lambda c: (c["order_tick"], id_key(c["table_id"]))):
                c["reserved"] = self.reserve_items(self.menu[c["dish_id"]]["recipe"])
        for e in self.customers:
            ids.reserve(e["id"])
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    def _initial_fresh(self, value):
        exact = Fraction(str(value))
        if self._fresh_step <= 0:
            return exact
        snapped = round(exact / self._fresh_step) * self._fresh_step
        return snapped if abs(exact - snapped) <= Fraction(1, 10**12) else exact

    def _init_customer(self, raw: dict) -> dict:
        c = dict(raw)
        c.setdefault("order_tick", 0)
        c.setdefault("state", "waiting")
        c.setdefault("order_status", "reserved")
        if c["state"] == "waiting":
            c.setdefault("patience_ticks_left", int(round(self.t["patience_s"] * TICK)))
            c.setdefault("eat_ticks_left", 0)
        else:
            c.setdefault("patience_ticks_left", 0)
            c.setdefault("eat_ticks_left", int(round(self.t["eat_s"] * TICK)))
        if "reserved" not in c:
            if c["order_status"] == "reserved":
                c["reserved"] = [] if self.individual_stock else dict(self.menu[c["dish_id"]]["recipe"])
            else:
                c["reserved"] = [] if self.individual_stock else {}
        else:
            c["reserved"] = list(c["reserved"]) if self.individual_stock else dict(c["reserved"])
        c.setdefault("base_price", self.menu[c["dish_id"]]["price"] if c["state"] == "eating" else 0)
        c.setdefault("tip", 0)
        return c

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                from ..errors import BadInput
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def available_stock(self):
        """Kho vật lý trừ nguyên liệu đã giữ cho những đơn chưa nấu."""
        if self.individual_stock:
            claimed = {ident for c in self.customers for ident in c["reserved"]}
            available = {}
            for item in self.stock:
                if item["id"] not in claimed and self._fresh[item["id"]] >= self._spoiled_below:
                    available[item["kind"]] = available.get(item["kind"], 0) + 1
            return available
        available = dict(self.stock)
        for customer in self.customers:
            for kind, count in customer["reserved"].items():
                available[kind] = available.get(kind, 0) - count
        return available

    def reserve_items(self, recipe, released=()):
        """Chọn cá thể chưa ươn, tươi nhất rồi id nhỏ; trả [] nếu không đủ cả món."""
        claimed = {ident for c in self.customers for ident in c["reserved"] if ident not in released}
        selected = []
        for kind, count in sorted(recipe.items()):
            choices = sorted((item for item in self.stock if item["kind"] == kind
                              and item["id"] not in claimed and self._fresh[item["id"]] >= self._spoiled_below),
                             key=lambda item: (-self._fresh[item["id"]], id_key(item["id"])))
            if len(choices) < count:
                return []
            selected.extend(item["id"] for item in choices[:count])
        return selected

    def _decay_stock(self, events):
        if not self.individual_stock or self._fresh_step <= 0:
            return
        spoiled = []
        for item in self.stock:
            ident = item["id"]
            old = self._fresh[ident]
            new = max(Fraction(0), old - self._fresh_step)
            self._fresh[ident] = new
            item["fresh"] = float(new)
            if old >= self._spoiled_below > new:
                spoiled.append(item)
        for item in sort_by_id(spoiled):
            events.append(("spoiled", {"item_id": item["id"], "kind": item["kind"], "location": "stock"}))
        if not spoiled:
            return
        spoiled_ids = {item["id"] for item in spoiled}
        # Nhả toàn bộ phần giữ của đơn bị ảnh hưởng, rồi thử chọn lại đúng một lần.
        for c in sorted(self.customers, key=lambda c: (c["order_tick"], id_key(c["table_id"]))):
            if c["order_status"] != "reserved" or not spoiled_ids.intersection(c["reserved"]):
                continue
            released = c["reserved"]
            c["reserved"] = []
            replacement = self.reserve_items(self.menu[c["dish_id"]]["recipe"], released)
            if replacement:
                c["reserved"] = replacement
            else:
                c["order_status"] = "unfulfillable"

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos},
            "stock": sort_by_id([dict(x) for x in self.stock]) if self.individual_stock else
                     {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": sort_by_id(self.customers),
        }

    def step(self, inp):
        events = []
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self._tick_timers(events)
        self._decay_stock(events)
        self._finish_cooking(events)
        self._move(inp)
        if inp.pressed("interact"):
            self._interact(events)
        self._process_customers_and_closing(events)
        if self.time_left_ticks > 0:
            self._arrive(events)
        else:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        return events

    def _tick_timers(self, events):
        """Giảm timer nấu/ăn/kiên nhẫn; tăng ready_ticks cho món đã ready từ đầu bước."""
        for s in self.stoves:
            if s["state"] == "ready":
                s["ready_ticks"] += 1
            elif s["state"] == "cooking":
                s["cook_ticks_left"] = max(0, s["cook_ticks_left"] - 1)
        for c in self.customers:
            if c["state"] == "eating":
                c["eat_ticks_left"] = max(0, c["eat_ticks_left"] - 1)
            elif c["state"] == "waiting":
                c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)

    def _finish_cooking(self, events):
        for s in sort_by_id(self.stoves):
            if s["state"] == "cooking" and s["cook_ticks_left"] == 0:
                s["state"] = "ready"
                s["ready_ticks"] = 0
                dish = s["dish"]
                events.append(("dish_ready", {"stove_id": s["id"], "order_id": dish["order_id"],
                                              "dish_id": dish["dish_id"]}))

    def _interaction_target(self):
        """Tối đa một interact: chọn theo (khoảng cách, bếp trước bàn, id)."""
        r = self.t["interact_radius"]
        px, pz = self.pos
        candidates = []
        for s in self.stoves:
            d = math.hypot(px - s["pos"][0], pz - s["pos"][1])
            if d <= r:
                candidates.append((d, 0, id_key(s["id"]), "stove", s))
        for tb in self.tables:
            d = math.hypot(px - tb["pos"][0], pz - tb["pos"][1])
            if d <= r:
                candidates.append((d, 1, id_key(tb["id"]), "table", tb))
        if not candidates:
            return None
        candidates.sort(key=lambda item: (item[0], item[1], item[2]))
        _, _, _, kind, obj = candidates[0]
        return kind, obj

    def live_hints(self):
        target = None if self.done else self._interaction_target()
        if target is None:
            return {}
        kind, obj = target
        if kind == "stove" and obj["state"] == "idle" and self._next_reserved_order() is not None:
            return {"interact_target": {"id": obj["id"], "action": "cook_started"}}
        if kind == "stove" and obj["state"] == "ready" and self.hand is None and self.t.get("carry_limit", 1) >= 1:
            return {"interact_target": {"id": obj["id"], "action": "dish_picked"}}
        if kind == "table" and self._serving_customer(obj) is not None:
            return {"interact_target": {"id": obj["id"], "action": "served"}}
        return {}

    def _interact(self, events):
        target = self._interaction_target()
        if target is None:
            return
        kind, obj = target
        if kind == "stove":
            self._interact_stove(obj, events)
        else:
            self._interact_table(obj, events)

    def _next_reserved_order(self):
        return min(
            (c for c in self.customers if c["state"] == "waiting" and c["order_status"] == "reserved"),
            key=lambda c: (c["order_tick"], id_key(c["table_id"])),
            default=None,
        )

    def _interact_stove(self, stove, events):
        if stove["state"] == "idle":
            c = self._next_reserved_order()
            if c is None:
                return
            dish_id = c["dish_id"]
            list_price = self.menu[dish_id]["price"]
            if self.individual_stock:
                reserved_ids = set(c["reserved"])
                used = [x for x in self.stock if x["id"] in reserved_ids]
                self.stock = [x for x in self.stock if x["id"] not in reserved_ids]
                used.sort(key=lambda x: (x["kind"], id_key(x["id"])))
                if used:
                    avg_fresh = sum(self._fresh.pop(x["id"]) for x in used) / len(used)
                    base_price = math.floor(list_price * avg_fresh / 100)
                else:
                    base_price = list_price
                items = [dict(x) for x in used]
                c["reserved"] = []
            else:
                base_price = list_price
                items = []
                for k in sorted(c["reserved"]):
                    amt = c["reserved"][k]
                    self.stock[k] = max(0, self.stock.get(k, 0) - amt)
                    items.extend([k] * amt)
                c["reserved"] = {}
            c["order_status"] = "assigned"
            stove["state"] = "cooking"
            stove["dish"] = {"order_id": c["id"], "dish_id": dish_id, "base_price": base_price}
            stove["cook_ticks_left"] = int(round(self.menu[dish_id]["cook_s"] * TICK))
            stove["ready_ticks"] = 0
            events.append(("cook_started", {
                "stove_id": stove["id"],
                "order_id": c["id"],
                "dish_id": dish_id,
                "items": items,
                "base_price": base_price,
            }))
        elif stove["state"] == "ready":
            if self.hand is not None or self.t.get("carry_limit", 1) < 1:
                return
            dish = stove["dish"]
            self.hand = dict(dish)
            stove["state"] = "idle"
            stove["dish"] = None
            stove["cook_ticks_left"] = 0
            stove["ready_ticks"] = 0
            events.append(("dish_picked", {
                "stove_id": stove["id"],
                "order_id": dish["order_id"],
                "dish_id": dish["dish_id"],
            }))

    def _serving_customer(self, table):
        if self.hand is None:
            return None
        return next(
            (c for c in self.customers
             if c["table_id"] == table["id"] and c["state"] == "waiting" and c["id"] == self.hand["order_id"]),
            None,
        )

    def _interact_table(self, table, events):
        cust = self._serving_customer(table)
        if cust is None:
            return
        dish = self.hand
        self.hand = None
        patience_max = int(round(self.t["patience_s"] * TICK))
        ratio = (cust["patience_ticks_left"] / patience_max) if patience_max > 0 else 0.0
        base_price = dish["base_price"]
        tip = math.floor(base_price * self.t["tip_rate"]) if ratio >= self.t["tip_min_patience_ratio"] else 0
        cust["state"] = "eating"
        cust["order_status"] = "served"
        cust["eat_ticks_left"] = int(round(self.t["eat_s"] * TICK))
        cust["base_price"] = base_price
        cust["tip"] = tip
        events.append(("served", {
            "order_id": cust["id"],
            "table_id": table["id"],
            "dish_id": dish["dish_id"],
            "patience_ticks_left": cust["patience_ticks_left"],
            "base_price": base_price,
            "tip": tip,
        }))

    def _clamp_reputation(self, val: float) -> float:
        lo, hi = self.t["reputation_min"], self.t["reputation_max"]
        return min(hi, max(lo, round(val, 10)))

    def _pay_customer(self, c, reason: str, events):
        amount = c["base_price"] + c["tip"]
        self.money += amount
        self.earned += amount
        self.shift_earned += amount
        if c["tip"] > 0:
            self.reputation = self._clamp_reputation(self.reputation + self.t["tip_reputation"])
        events.append(("paid", {
            "order_id": c["id"],
            "table_id": c["table_id"],
            "base_price": c["base_price"],
            "tip": c["tip"],
            "amount": amount,
            "reason": reason,
        }))

    def _cleanup_customer_order(self, c):
        c["reserved"] = [] if self.individual_stock else {}
        if self.hand is not None and self.hand["order_id"] == c["id"]:
            self.hand = None
        for s in self.stoves:
            if s["dish"] is not None and s["dish"]["order_id"] == c["id"]:
                s["state"] = "idle"
                s["dish"] = None
                s["cook_ticks_left"] = 0
                s["ready_ticks"] = 0

    def _process_customers_and_closing(self, events):
        ordered = sorted(self.customers, key=lambda c: id_key(c["table_id"]))
        remaining = []
        closing = self.time_left_ticks <= 0
        for c in ordered:
            if not closing:
                if c["state"] == "eating" and c["eat_ticks_left"] == 0:
                    self._pay_customer(c, "finished_eating", events)
                elif c["state"] == "waiting" and c["patience_ticks_left"] == 0:
                    self.reputation = self._clamp_reputation(self.reputation + self.t["left_reputation_delta"])
                    events.append(("customer_left", {
                        "order_id": c["id"],
                        "table_id": c["table_id"],
                        "reason": "patience",
                        "reputation": self.reputation,
                    }))
                    self._cleanup_customer_order(c)
                else:
                    remaining.append(c)
            else:
                if c["state"] == "eating":
                    self._pay_customer(c, "closing", events)
                else:
                    events.append(("customer_left", {
                        "order_id": c["id"],
                        "table_id": c["table_id"],
                        "reason": "closing",
                        "reputation": self.reputation,
                    }))
                    self._cleanup_customer_order(c)
        self.customers = remaining

    def _arrive(self, events):
        first = self.t["first_customer_tick"]
        interval = int(round(self.t["customer_interval_s"] * TICK))
        if not self.random_customers or self.phase_tick < first or (self.phase_tick - first) % interval:
            return
        occupied = {c["table_id"] for c in self.customers}
        table = next((tb for tb in sort_by_id(self.tables) if tb["id"] not in occupied), None)
        if table is None:
            return
        available = self.available_stock()
        choices = [dish for dish in sorted(self.day_dishes) if all(available.get(k, 0) >= n
                   for k, n in self.menu[dish]["recipe"].items())]
        if not choices:
            events.append(("no_dish", {}))
            return
        dish_id = self.rng.get("customer_order").choice(choices)
        order_id = self.ids.new("C")
        self.customers.append({"id": order_id, "table_id": table["id"], "dish_id": dish_id,
                               "order_tick": self.phase_tick, "state": "waiting",
                               "patience_ticks_left": int(round(self.t["patience_s"] * TICK)),
                               "eat_ticks_left": 0, "order_status": "reserved",
                               "reserved": self.reserve_items(self.menu[dish_id]["recipe"])
                                           if self.individual_stock else dict(self.menu[dish_id]["recipe"]),
                               "base_price": 0, "tip": 0})
        events.append(("customer_arrived", {"order_id": order_id, "table_id": table["id"],
                                            "dish_id": dish_id}))

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
