#!/usr/bin/env python3
"""Probe the boundary_engine planar family (route 5, new intrinsic geometry).

Uses the validated open-boundary planar builder (research/local2d/boundary_engine)
to build planar codes at several sizes with the flagship supports, then probes
whether any advance a current 2d-local frontier cell.  Distance is an UPPER
BOUND via the surrogate.

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
for _p in (str(ROOT / "research" / "local2d"), str(ROOT / "research" / "kit"),
           str(ROOT / "verify")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from boundary_engine import build_planar, reduce_weights, compute_k  # noqa: E402
from css import verify_css  # noqa: E402
from surrogate import distance_rand  # noqa: E402


def probe(Lx, Ly, S_f, S_g, trials=1500, seed=0):
    HX, HZ, info = build_planar(Lx, Ly, S_f, S_g)
    HX = reduce_weights(HX)
    HZ = reduce_weights(HZ)
    n = HX.shape[1]
    css = verify_css(HX, HZ)
    k = compute_k(HX, HZ)
    d = distance_rand(HX, HZ, trials=trials, seed=seed)
    wmax = max(int(HX.sum(1).max()), int(HZ.sum(1).max()))
    return {
        "Lx": Lx, "Ly": Ly, "n": n, "k": k, "css": bool(css), "d": d,
        "wmax": wmax, "eff": k * d * d / n if n else 0.0,
        "info": {k2: (v2 if isinstance(v2, (int, float, str, bool)) else None)
                  for k2, v2 in info.items()},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", type=int, nargs="*", default=[6, 8, 10, 12])
    ap.add_argument("--trials", type=int, default=1500)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--output", type=Path, default=ROOT / "research" / "candidates" / "planar-family-probe.json")
    args = ap.parse_args()

    # flagship supports ([[288,8,12]] family)
    S_f = [(1, 0), (2, 0), (0, 2)]
    S_g = [(0, 0), (2, 1), (2, 2)]

    results = []
    for L in args.sizes:
        for Lx, Ly in ((L, L), (L, L + 2)):
            try:
                r = probe(Lx, Ly, S_f, S_g, trials=args.trials, seed=args.seed)
            except Exception as exc:  # noqa: BLE001
                print(f"{Lx}x{Ly}: ERROR {exc}")
                continue
            results.append(r)
            print(f"{Lx}x{Ly}: n={r['n']} k={r['k']} css={r['css']} d<={r['d']} "
                  f"wmax={r['wmax']} eff={r['eff']:.3f}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2) + "\n")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()