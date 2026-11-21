"""QA autoplay: sinh file inputs chơi hợp lý cho gather / quan / day để làm smoke e2e.

Bot chỉ ĐỌC snapshot (như người chơi nhìn HUD) rồi quyết định input; file inputs sinh ra
được chạy lại bằng headless để lấy bằng chứng (và để kiểm tất định).

    PYTHONPATH=. python3 tools/qa_autoplay.py --mode day --days 2 --seed 1 --out-inputs in.json
    PYTHONPATH=. python3 tools/qa_autoplay.py --mode gather --seed 42 --out-inputs g.json --want ca_loc=2,bong_sung=2
    PYTHONPATH=. python3 tools/qa_autoplay.py --mode quan --seed 42 --inventory kho.json --out-inputs q.json

Bot nằm ở chonoi/bot.py (dùng chung với soak_cmd); file này chỉ sinh inputs cho headless.
"""

import argparse
import json

from chonoi.bot import Bot
from chonoi.contract import load_contract
from chonoi.inputs import BUTTONS_V11, InputPlayer
from chonoi.inventory import read_inventory
from chonoi.runner import Session


def autoplay(mode, seed, days=1, inventory=None, want=None, max_ticks=200000):
    t = load_contract()["tuning"]
    sess = Session(mode, t, {}, seed, inventory=inventory, days=days)
    ip = InputPlayer([], buttons=BUTTONS_V11)
    bot = Bot(t, want=want)
    frames, last, k = [], None, 0
    while not sess.done and k < max_ticks:
        fr = bot.decide(sess.snapshot())
        key = json.dumps(fr, sort_keys=True)
        if key != last or "buy" in fr:
            fr = {"tick": k, **fr}
            frames.append(fr)
            ip._frames[k] = fr
            last = key
        sess.step(ip.advance(k))
        k += 1
    return {"frames": frames}, k, sess.end_row()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["gather", "quan", "day"])
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--days", type=int, default=1)
    ap.add_argument("--inventory")
    ap.add_argument("--want", help="gather độc lập: kind=n,kind=n")
    ap.add_argument("--out-inputs", required=True)
    a = ap.parse_args()
    want = None
    if a.want:
        want = {k: int(v) for k, v in (x.split("=") for x in a.want.split(","))}
    ver = load_contract().get("contract_version", "1.1")
    inv = read_inventory(a.inventory, contract_version=ver) if a.inventory else None
    data, ticks, end = autoplay(a.mode, a.seed, a.days, inv, want)
    with open(a.out_inputs, "w", encoding="utf-8") as f:
        json.dump(data, f)
    print(f"ticks={ticks} frames={len(data['frames'])} end={json.dumps(end, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
