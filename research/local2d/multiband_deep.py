#!/usr/bin/env python
"""Overnight: deep witness re-screen of all multiband survivors.

Each witnessed survivor gets a 300k-trial randomized distance search
(fast backend, 4 threads). Budget: ~75s/code x 336 ~ 7h. Survivors that
keep d_ub >= d at this budget are near-submission-grade; any that fall
are removed from the map (refutation is the point).
"""
import json
import sys
import time

sys.path.insert(0, "research/local2d")
sys.path.insert(0, "research/kit")
from multiband import build  # noqa: E402
from surrogate import distance_rand  # noqa: E402

OUT = "research/candidates/overnight-chamfer4"
TRIALS = 300_000


def main():
    surv = json.load(open(f"{OUT}/multiband-witnessed.json"))
    print(f"{len(surv)} survivors, {TRIALS} trials each", flush=True)
    kept, fell = [], []
    t0 = time.time()
    for i, s in enumerate(surv):
        HX, HZ, _ = build(s["d"], s["rows"], s["m"], s["pitch"])
        try:
            d_ub = distance_rand(HX, HZ, trials=TRIALS, seed=9000 + i,
                                 backend="fast", threads=4)
        except Exception as e:
            print(f"  [{i}] backend err: {e}", flush=True)
            continue
        if d_ub >= s["d"]:
            kept.append(s)
        else:
            fell.append(s)
            print(f"  FELL [[{s['n']},{s['k']},{s['d']}]] d_ub={d_ub} "
                  f"({i}/{len(surv)})", flush=True)
        if i % 25 == 0:
            print(f"  ...{i}/{len(surv)} kept={len(kept)} fell={len(fell)} "
                  f"({(time.time()-t0)/60:.0f}min)", flush=True)
            json.dump({"kept": kept, "fell": fell},
                      open(f"{OUT}/multiband-deep.json", "w"), indent=1)
    json.dump({"kept": kept, "fell": fell},
              open(f"{OUT}/multiband-deep.json", "w"), indent=1)
    print(f"FINAL: kept={len(kept)} fell={len(fell)}", flush=True)


if __name__ == "__main__":
    main()
