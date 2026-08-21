#!/usr/bin/env python3
"""Probe planar families with graft shrinking (route 5, new intrinsic geometry).

The boundary_engine builds planar codes; graft_r1_safe removes qubits while
preserving k and d.  This probe builds several planar families at multiple
sizes, shrinks them with graft_r1_safe, and reports (n,k,d) to find points
that might advance a 2d-local frontier.  Distance is an UPPER BOUND.

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

from boundary_engine import build_planar, reduce_weights, compute_k, graft_r1_safe  # noqa: E402
from css import verify_css  # noqa: E402
from surrogate import distance_rand  # noqa: E402


FAMILIES = {
    "flagship": ([(1, 0), (2, 0), (0, 2)], [(0, 0), (2, 1), (2, 2)]),
    "w4_f1": ([(1, 0), (0, 2)], [(0, 0), (2, 1)]),
    "w4_f2": ([(1, 0), (0, 1)], [(0, 0), (1, 1)]),
}


def probe(Lx, Ly, S_f, S_g, trials=1500, seed=0, d_floor=None, graft=False):
    HX, HZ, info = build_planar(Lx, Ly, S_f, S_g)
    HX = reduce_weights(HX)
    HZ = reduce_weights(HZ)
    n0 = HX.shape[1]
    k0 = compute_k(HX, HZ)
    d0 = distance_rand(HX, HZ, trials=trials, seed=seed)
    n_removed = 0
    if graft and d_floor is not None:
        HX, HZ, n_removed = graft_r1_safe(HX, HZ, d_floor=d_floor,
                                          trials=trials, seed=seed)
    n = HX.shape[1]
    css = verify_css(HX, HZ)
    k = compute_k(HX, HZ)
    d = distance_rand(HX, HZ, trials=trials, seed=seed)
    wmax = max(int(HX.sum(1).max()), int(HZ.sum(1).max()))
    return {
        "Lx": Lx, "Ly": Ly, "n0": n0, "n": n, "k0": k0, "k": k,
        "css": bool(css), "d": d, "d0": d0, "wmax": wmax,
        "n_removed": n_removed, "eff": k * d * d / n if n else 0.0,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", type=int, nargs="*", default=[10, 12, 14])
    ap.add_argument("--trials", type=int, default=1500)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--graft", action="store_true")
    ap.add_argument("--output", type=Path, default=ROOT / "research" / "candidates" / "planar-graft-probe.json")
    args = ap.parse_args()

    results = []
    for name, (S_f, S_g) in FAMILIES.items():
        for L in args.sizes:
            for Lx, Ly in ((L, L), (L, L + 2)):
                try:
                    # estimate d first to set a floor
                    HX0, HZ0, _ = build_planar(Lx, Ly, S_f, S_g)
                    HX0 = reduce_weights(HX0); HZ0 = reduce_weights(HZ0)
                    d0 = distance_rand(HX0, HZ0, trials=args.trials, seed=args.seed)
                    d_floor = max(1, int(d0) - 1) if args.graft else None
                    r = probe(Lx, Ly, S_f, S_g, trials=args.trials, seed=args.seed,
                              d_floor=d_floor, graft=args.graft)
                except Exception as exc:  # noqa: BLE001
                    print(f"{name} {Lx}x{Ly}: ERROR {exc}")
                    continue
                r["family"] = name
                results.append(r)
                print(f"{name} {Lx}x{Ly}: n={r['n']} (from {r['n0']}) k={r['k']} "
                      f"css={r['css']} d<={r['d']} wmax={r['wmax']} "
                      f"removed={r['n_removed']} eff={r['eff']:.3f}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2) + "\n")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()