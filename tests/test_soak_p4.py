"""QA Phase 4 (hungdt31): soak_cmd (Test Contract v1.3) và kế hoạch lặp ở Ngày 6–10."""

import copy
import json
import subprocess
import sys
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import BUTTONS_V11, InputState
from chonoi.runner import Session

from helpers import ROOT, Workdir

T = load_contract()["tuning"]


def _soak(w, *args):
    p = subprocess.run([sys.executable, "-m", "chonoi.soak", *args], cwd=ROOT, capture_output=True, text=True)
    return p.returncode, p.stderr


class DayPlanCycles(unittest.TestCase):
    def test_day6_reuses_d1_plan(self):
        # Mỗi pha hết giờ ngay (1 tick), Shop đóng bằng shop_done -> 6 Ngày rất nhanh.
        sc = {"gather": {"time_left_ticks": 1, "random_fish": False},
              "quan": {"time_left_ticks": 1, "random_customers": False}}
        sess = Session("day", copy.deepcopy(T), sc, 1, days=6)
        plans = [e["data"]["dishes"] for e in sess.initial_events() if e["name"] == "day_plan"]
        prev = False
        for _ in range(200):
            if sess.done:
                break
            want = sess.snapshot()["phase"] == "shop" and not prev
            prev = want
            for e in sess.step(InputState((0.0, 0.0), {b: (b == "shop_done" and want) for b in BUTTONS_V11},
                                          {"shop_done"} if want else set())):
                if e["name"] == "day_plan":
                    plans.append(e["data"]["dishes"])
        self.assertEqual(sess.sim.days_completed, 6)
        self.assertEqual(len(plans), 6)
        d = {p["day"]: p["dishes"] for p in T["day_plan"]}
        self.assertEqual(plans, [d[1], d[2], d[3], d[4], d[5], d[1]])


class SoakCmd(unittest.TestCase):
    def test_soak_json_shape_pass_and_deterministic(self):
        with Workdir() as w:
            outs = []
            for name in ("a.json", "b.json"):
                code, err = _soak(w, "--seed", "7", "--days", "2", "--out", w.path(name))
                self.assertEqual(code, 0, err)
                with open(w.path(name), encoding="utf-8") as f:
                    outs.append(json.load(f))
            a, b = outs
            self.assertEqual(set(a), {"days", "days_completed", "crashes", "results", "duration_s"})
            self.assertEqual((a["days"], a["days_completed"], a["crashes"]), (2, 2, 0))
            self.assertEqual([r["day"] for r in a["results"]], [1, 2])
            for r in a["results"]:
                self.assertEqual(set(r), {"day", "earned", "reputation", "score"})
            # điểm tại lúc Shop đóng = earned + 100 × floor(reputation); earned không giảm
            mult = T["score"]["reputation_multiplier"]
            for r in a["results"]:
                self.assertEqual(r["score"], r["earned"] + mult * int(r["reputation"]))
            self.assertLessEqual(a["results"][0]["earned"], a["results"][1]["earned"])
            # tất định: so mọi trường gameplay, bỏ thời gian thực
            a.pop("duration_s"), b.pop("duration_s")
            self.assertEqual(a, b)

    def test_bad_args_exit_2(self):
        with Workdir() as w:
            for args in (["--seed", "7", "--days", "0", "--out", w.path("x.json")],
                         ["--seed", "x", "--days", "2", "--out", w.path("x.json")],
                         ["--days", "2", "--out", w.path("x.json")]):
                self.assertEqual(_soak(w, *args)[0], 2, args)


if __name__ == "__main__":
    unittest.main()
