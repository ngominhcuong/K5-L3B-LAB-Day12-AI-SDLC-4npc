"""QA Phase 4: chạy lại đúng soak_cmd của nhóm (chonoi.soak.run_soak) và ghi lại event để kiểm:
kế hoạch D1–D5 lặp ở Ngày 6+, id cá thể họ I không trùng xuyên Ngày, nâng cấp giữ xuyên Ngày,
earned không giảm, mỗi Ngày đi đủ gather -> quan -> shop.

    PYTHONPATH=. python3 tools/qa_soak_trace.py 7 10
"""
import sys

from chonoi import runner, soak
from chonoi.contract import load_contract

seed, days = int(sys.argv[1]), int(sys.argv[2])
t = load_contract()["tuning"]
plans = {p["day"]: p["dishes"] for p in t["day_plan"]}
seen = []  # (day, name, phase, data)
_orig_step = runner.Session.step


def _spy(self, inp):
    evs = _orig_step(self, inp)
    for e in evs:
        seen.append((e.get("day"), e["name"], e["phase"], e["data"]))
        if e["name"] == "gather_end":
            ids = [x["id"] for x in e["data"]["inventory"]["items"]]
            print("D%-2d gather_end %-7s %-14s (%2d cá thể) | active_upgrades %s" % (
                e["day"], e["data"]["reason"], f"{ids[0]}..{ids[-1]}" if ids else "-", len(ids),
                self.snapshot().get("active_upgrades")))
    return evs


runner.Session.step = _spy
report = soak.run_soak(seed, days, t)
runner.Session.step = _orig_step

plan_ok = [d["dishes"] == plans[(day - 1) % len(plans) + 1] for day, n, _, d in seen if n == "day_plan"]
ids = [x["id"] for day, n, _, d in seen if n == "gather_end" for x in d["inventory"]["items"]]
phases = {}
for day, n, ph, _ in seen:
    if n == "phase_start":
        phases.setdefault(day, []).append(ph)
earned = [r["earned"] for r in report["results"]]
print("soak:", {k: report[k] for k in ("days", "days_completed", "crashes")})
print("day_plan Ngày 2..%d khớp D((n-1)%%5+1): %s (%d/%d)" % (days, all(plan_ok), sum(plan_ok), len(plan_ok)))
print("id cá thể không trùng xuyên %d Ngày: %s | tổng %d" % (days, len(ids) == len(set(ids)), len(ids)))
print("mỗi Ngày có phase_start quan + shop:", all(phases.get(d, [])[-2:] == ["quan", "shop"] or
                                                    phases.get(d, []) [:2] == ["quan", "shop"] for d in range(1, days + 1)))
print("earned không giảm:", earned == sorted(earned), earned)
