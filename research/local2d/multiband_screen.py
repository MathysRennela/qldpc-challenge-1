#!/usr/bin/env python
"""Witness-screen the multiband sweep survivors.

For each Pareto-surviving (d, rows, m, pitch) config: rebuild H, run the
fast randomized distance search, and keep configs whose d upper bound
meets the target (the mask's design distance). Only witness-backed
survivors are staged via the kit path.
"""
import json
import sys
import time

import numpy as np

sys.path.insert(0, "research/local2d")
sys.path.insert(0, "research/kit")
from multiband import build  # noqa: E402
from surrogate import distance_rand  # noqa: E402

OUT = "research/candidates/overnight-chamfer4"


def main():
    sweep = json.load(open(f"{OUT}/multiband-sweep.json"))
    # dedupe by (n, k, d): keep one representative per triplet
    best = {}
    for s in sweep:
        key = (s["n"], s["k"], s["d"])
        if key not in best or s["g"] > best[key]["g"]:
            best[key] = s
    sweep = sorted(best.values(), key=lambda x: -x["g"])
    print(f"{len(sweep)} unique survivors to screen", flush=True)
    passed = []
    for i, s in enumerate(sweep):
        d, rows, m, pitch, n, k, g = (s["d"], s["rows"], s["m"], s["pitch"],
                                      s["n"], s["k"], s["g"])
        HX, HZ, _ = build(d, rows, m, pitch)
        try:
            d_ub = distance_rand(HX, HZ, trials=4000, seed=i,
                                 backend="fast", threads=4)
        except Exception as e:
            print(f"  [{i}] d={d} r={rows} m={m} p={pitch}: backend err {e}",
                  flush=True)
            continue
        ok = d_ub >= d
        if ok:
            print(f"  PASS d={d} rows={rows} m={m} pitch={pitch} "
                  f"[[{n},{k},{d}]] g={g:.4f} (d_ub={d_ub})", flush=True)
            passed.append(s)
        if i % 50 == 0:
            print(f"  ...{i}/{len(sweep)} screened, {len(passed)} passed "
                  f"({time.strftime('%H:%M:%S')})", flush=True)
    with open(f"{OUT}/multiband-witnessed.json", "w") as f:
        json.dump(passed, f, indent=1)
    print(f"WITNESS-PASSED: {len(passed)} of {len(sweep)}", flush=True)
    for s in sorted(passed, key=lambda x: -x["g"])[:20]:
        print(f"  [[{s['n']},{s['k']},{s['d']}]] g={s['g']:.4f} "
              f"(rows={s['rows']} m={s['m']} pitch={s['pitch']})", flush=True)


if __name__ == "__main__":
    main()
