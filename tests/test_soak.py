"""Unit & CLI tests cho Phase 4 soak headless (`chonoi.soak`)."""

import json
import os
import tempfile
import unittest

from chonoi.contract import load_contract
from chonoi.soak import main as soak_main, run_soak


class SoakTests(unittest.TestCase):
    def test_soak_10_days_deterministic_and_repeats_plan(self):
        tuning = load_contract()["tuning"]
        r1 = run_soak(seed=7, days=10, tuning=tuning)
        r2 = run_soak(seed=7, days=10, tuning=tuning)
        self.assertEqual(r1["days"], 10)
        self.assertEqual(r1["days_completed"], 10)
        self.assertEqual(r1["crashes"], 0)
        self.assertEqual(len(r1["results"]), 10)
        self.assertEqual([x["day"] for x in r1["results"]], list(range(1, 11)))
        self.assertEqual(r1["results"], r2["results"])

    def test_soak_cli_writes_json_and_rejects_bad_days(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_p = os.path.join(tmp, "soak.json")
            self.assertEqual(soak_main(["--seed", "7", "--days", "0", "--out", out_p]), 2)
            self.assertEqual(soak_main(["--seed", "7", "--days", "10", "--out", out_p]), 0)
            with open(out_p, encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["days"], 10)
            self.assertEqual(data["days_completed"], 10)
            self.assertEqual(data["crashes"], 0)
            self.assertEqual(len(data["results"]), 10)


if __name__ == "__main__":
    unittest.main()
