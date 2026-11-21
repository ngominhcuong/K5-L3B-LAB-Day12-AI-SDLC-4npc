"""Soak headless (Contract v1.3): python3 -m chonoi.soak --seed 7 --days 10 --out soak.json.

Mã thoát: 0 khi hoàn tất mọi Ngày, 1 khi soak lỗi hoặc chưa xong, 2 khi đầu vào sai.
"""

import argparse
import json
import math
import os
import sys
import time

from .contract import load_contract
from .errors import BadInput
from .inputs import InputState
from .runner import Session


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write(f"lỗi: {message}\n")
        sys.exit(2)


def _int(name):
    def conv(s):
        try:
            return int(s)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{name} phải là số nguyên")
    return conv


def _steer(px, py, tx, ty):
    dx, dy = tx - px, ty - py
    dist = math.hypot(dx, dy)
    if dist < 1e-6:
        return (0.0, 0.0)
    return (dx / dist, dy / dist)


class _DeterministicBot:
    """Bot tất định: thu gom nhanh rồi cập bến, nấu & phục vụ, mua nâng cấp nếu đủ tiền."""

    def __init__(self, tuning):
        self.t = tuning
        self._toggle = False

    def next_input(self, sess: Session) -> InputState:
        self._toggle = not self._toggle
        snap = sess.snapshot()
        phase = snap["phase"]
        edges = set()
        move = (0.0, 0.0)
        buy = None

        if phase == "gather":
            px, pd = snap["player"]["pos"]
            hold = snap.get("hold", [])
            dock = self.t["gather"]["dock_pos"]
            dock_r = self.t["gather"]["dock_radius"]
            if len(hold) >= 4 or snap["time_left_ticks"] <= 1200:
                if math.hypot(px - dock[0], pd - dock[1]) <= dock_r:
                    if self._toggle:
                        edges.add("interact")
                else:
                    move = _steer(px, pd, dock[0], dock[1])
            else:
                ready_node = next((n for n in snap.get("nodes", []) if n.get("ready")), None)
                if ready_node is not None:
                    nx, nd = ready_node["pos"]
                    if math.hypot(px - nx, pd - nd) <= self.t["gather"]["interact_radius"]:
                        if self._toggle:
                            edges.add("interact")
                    else:
                        move = _steer(px, pd, nx, nd)
                else:
                    move = _steer(px, pd, dock[0], dock[1])

        elif phase == "quan":
            px, pz = snap["player"]["pos"]
            hand = snap.get("hand")
            stoves = snap.get("stoves", [])
            tables = {tb["id"]: tb for tb in snap.get("tables", [])}
            customers = snap.get("customers", [])
            r = self.t["quan"]["interact_radius"]

            if hand is not None:
                cust = next((c for c in customers if c["id"] == hand["order_id"]), None)
                if cust and cust["table_id"] in tables:
                    tx, tz = tables[cust["table_id"]]["pos"]
                    if math.hypot(px - tx, pz - tz) <= r:
                        if self._toggle:
                            edges.add("interact")
                    else:
                        move = _steer(px, pz, tx, tz)
            else:
                ready_stove = next((s for s in stoves if s["state"] == "ready"), None)
                if ready_stove is not None:
                    sx, sz = ready_stove["pos"]
                    if math.hypot(px - sx, pz - sz) <= r:
                        if self._toggle:
                            edges.add("interact")
                    else:
                        move = _steer(px, pz, sx, sz)
                else:
                    has_reserved = any(c["order_status"] == "reserved" for c in customers)
                    idle_stove = next((s for s in stoves if s["state"] == "idle"), None)
                    if has_reserved and idle_stove is not None:
                        sx, sz = idle_stove["pos"]
                        if math.hypot(px - sx, pz - sz) <= r:
                            if self._toggle:
                                edges.add("interact")
                        else:
                            move = _steer(px, pz, sx, sz)

        elif phase == "shop":
            upgrades = snap.get("upgrades", {})
            money = snap.get("money", 0)
            shop_ups = self.t.get("shop", {}).get("upgrades", {})
            for key in ("oxygen", "hp"):
                cur = upgrades.get(key, 0)
                nxt = next((u for u in shop_ups.get(key, []) if u["level"] == cur + 1), None)
                if nxt is not None and money >= nxt["price"]:
                    buy = key
                    break
            if self._toggle:
                edges.add("shop_done")

        return InputState(move, {}, edges, buy=buy)


def run_soak(seed: int, days: int, tuning: dict | None = None) -> dict:
    """Chạy các Ngày trong một Session. Bỏ duration_s khi so tính tất định."""
    if tuning is None:
        tuning = load_contract()["tuning"]
    t0 = time.perf_counter()
    crashes = 0
    results = []
    days_completed = 0
    try:
        sess = Session("day", tuning, {}, seed=seed, days=days)
        sess.initial_events()
        bot = _DeterministicBot(tuning)
        max_ticks = days * 23000
        for _ in range(max_ticks):
            if sess.done:
                break
            inp = bot.next_input(sess)
            evs = sess.step(inp)
            for ev in evs:
                if ev["name"] == "shop_end":
                    snap = sess.snapshot()
                    results.append({
                        "day": ev["day"],
                        "earned": sess.sim.earned,
                        "reputation": sess.sim.reputation,
                        "score": snap["score"],
                    })
        days_completed = sess.sim.days_completed
    except Exception as e:
        crashes += 1
        # Giữ các Ngày đã ghi nhận shop_end nếu mô phỏng vấp lỗi giữa chừng.
        days_completed = len(results)
        sys.stderr.write(f"lỗi soak: {e}\n")
    return {
        "days": days,
        "days_completed": days_completed,
        "crashes": crashes,
        "results": results,
        "duration_s": round(time.perf_counter() - t0, 4),
    }


def main(argv=None) -> int:
    p = _Parser(prog="chonoi.soak")
    p.add_argument("--seed", required=True, type=_int("seed"))
    p.add_argument("--days", required=True, type=_int("days"))
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    try:
        if a.days < 1:
            raise BadInput("--days phải >= 1")
        tuning = load_contract()["tuning"]
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2

    report = run_soak(a.seed, a.days, tuning)
    try:
        out_dir = os.path.dirname(os.path.abspath(a.out))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            f.write("\n")
    except OSError as e:
        sys.stderr.write(f"lỗi ghi: {e}\n")
        return 1
    print(f"soak seed={a.seed} days={a.days} days_completed={report['days_completed']} "
          f"crashes={report['crashes']} duration_s={report['duration_s']}", file=sys.stderr)
    # Ghi báo cáo trước để QA còn dữ liệu khi soak thất bại hoặc chạm giới hạn tick.
    ok = report["days_completed"] == a.days and report["crashes"] == 0
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
