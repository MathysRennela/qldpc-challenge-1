#!/usr/bin/env python3
"""Probe dense-packed surface check mutations (route 5).

The [[101,5,5]] dense-packed code (arXiv:2511.06758) is reconstructed by
research/build_dense_surface.py.  This probe tries local check mutations:
removing one check at a time from HX or HZ (which increases k by 1 if the
check is independent), keeping variants where k increases and the screened
distance stays >= the base d.  Distance is an UPPER BOUND via surrogate.

It is a probe: it does NOT claim a find.  Promising candidates are persisted
for later packaging through the standard kit + trusted validator.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "research" / "kit"), str(ROOT / "verify")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from css import compute_k, verify_css  # noqa: E402
from surrogate import distance_rand  # noqa: E402

sys.path.insert(0, str(ROOT / "research"))
from build_dense_surface import build  # noqa: E402


def probe(trials=1500, seed=0, d_floor=5):
    HX, HZ, coords, data, allcoords = build(5)
    n = HX.shape[1]
    k0 = compute_k(HX, HZ)
    d0 = distance_rand(HX, HZ, trials=trials, seed=seed)
    print(f"base [[{n},{k0},d<={d0}]]")
    results = [{"variant": "base", "n": n, "k": k0, "d": d0,
                "eff": k0 * d0 * d0 / n}]

    # Try removing each X check
    for side, H in (("X", HX), ("Z", HZ)):
        for r in range(H.shape[0]):
            H2 = np.delete(H, r, axis=0)
            if side == "X":
                HX2, HZ2 = H2, HZ
            else:
                HX2, HZ2 = HX, H2
            if not verify_css(HX2, HZ2):
                continue
            k2 = compute_k(HX2, HZ2)
            if k2 <= k0:
                continue
            d2 = distance_rand(HX2, HZ2, trials=trials, seed=seed)
            if d2 < d_floor:
                continue
            res = {"variant": f"remove-{side}-{r}", "n": n, "k": k2, "d": d2,
                   "eff": k2 * d2 * d2 / n}
            results.append(res)
            print(f"  remove {side} check {r}: k={k2} d<={d2} "
                  f"eff={k2*d2*d2/n:.3f}")

    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=1500)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--d-floor", type=int, default=5)
    ap.add_argument("--output", type=Path, default=ROOT / "research" / "candidates" / "dense-check-mutation-probe.json")
    args = ap.parse_args()
    results = probe(trials=args.trials, seed=args.seed, d_floor=args.d_floor)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2) + "\n")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()