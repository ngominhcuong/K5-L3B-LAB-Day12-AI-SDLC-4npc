"""QA Phase 4: chạy lại đúng soak_cmd của nhóm (chonoi.soak.run_soak) và ghi lại event để kiểm:
kế hoạch D1–D5 lặp ở Ngày 6+, id cá thể họ I không trùng xuyên Ngày, nâng cấp giữ xuyên Ngày,
earned không giảm, mỗi Ngày đi đủ gather -> quan -> shop.

    PYTHONPATH=. python3 tools/qa_soak_trace.py 7 10
"""
import sys
from unittest.mock import patch

from chonoi import runner, soak
from chonoi.contract import load_contract

seed, days = int(sys.argv[1]), int(sys.argv[2])
t = load_contract()["tuning"]
plans = {p["day"]: p["dishes"] for p in t["day_plan"]}
seen = []  # (day, name, phase, data)
_orig_step = runner.Session.step
_orig_initial_events = runner.Session.initial_events


def _spy_initial_events(self):
    # Ngày 1 phát day_plan và phase_start trước tick đầu tiên.
    evs = _orig_initial_events(self)
    seen.extend((e["day"], e["name"], e["phase"], e["data"]) for e in evs)
    return evs


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


with patch.object(runner.Session, "initial_events", _spy_initial_events), patch.object(runner.Session, "step", _spy):
    report = soak.run_soak(seed, days, t)

expected_days = list(range(1, days + 1))
plan_events = [(day, d["dishes"]) for day, n, _, d in seen if n == "day_plan"]
expected_plans = [(day, plans[(day - 1) % len(plans) + 1]) for day in expected_days]
plan_ok = plan_events == expected_plans
ids = [x["id"] for day, n, _, d in seen if n == "gather_end" for x in d["inventory"]["items"]]
ids_ok = len(ids) == len(set(ids))
phases = {}
for day, n, ph, _ in seen:
    if n == "phase_start":
        phases.setdefault(day, []).append(ph)
phases_ok = phases == {day: ["gather", "quan", "shop"] for day in expected_days}
earned = [r["earned"] for r in report["results"]]
earned_ok = len(earned) == days and earned == sorted(earned)
print("soak:", {k: report[k] for k in ("days", "days_completed", "crashes")})
print(f"day_plan Ngày 1..{days} khớp D((n-1)%5+1): {plan_ok} ({len(plan_events)}/{days})")
print(f"id cá thể không trùng xuyên {days} Ngày: {ids_ok} | tổng {len(ids)}")
print("mỗi Ngày có phase_start gather → quan → shop:", phases_ok)
print("earned không giảm:", earned_ok, earned)
soak_ok = report["days_completed"] == days and report["crashes"] == 0
sys.exit(0 if all((soak_ok, plan_ok, ids_ok, phases_ok, earned_ok)) else 1)
