#!/usr/bin/env python3
"""Probe dense-packed surface qubit removal (route 5).

The [[101,5,5]] dense-packed code (arXiv:2511.06758) is reconstructed by
research/build_dense_surface.py.  This probe removes qubits one at a time
(graft-style: remove a qubit that participates in exactly one check of some
type, together with that check), keeping k unchanged and the screened distance
>= a floor.  It reports (n,k,d) with the kit's exact GF(2) core (distance is
an UPPER BOUND via surrogate).  A smaller (n,k,d) point that stays on the
frontier would be a find.

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


def probe(trials=1500, seed=0, d_floor=5, max_removals=20):
    HX, HZ, coords, data, allcoords = build(5)
    n = HX.shape[1]
    k0 = compute_k(HX, HZ)
    d0 = distance_rand(HX, HZ, trials=trials, seed=seed)
    print(f"base [[{n},{k0},d<={d0}]]")
    rng = np.random.default_rng(seed)
    removed = 0
    while removed < max_removals:
        wx = HX.sum(axis=0) if HX.size else np.zeros(HX.shape[1])
        wz = HZ.sum(axis=0) if HZ.size else np.zeros(HZ.shape[1])
        cands = ([('X', int(q)) for q in np.where(wx == 1)[0]] +
                 [('Z', int(q)) for q in np.where(wz == 1)[0]])
        if not cands:
            break
        rng.shuffle(cands)
        accepted = False
        for (t, q) in cands:
            H = HX if t == 'X' else HZ
            r = int(np.where(H[:, q] == 1)[0][0])
            HX2 = np.delete(HX, r, axis=0) if t == 'X' else HX
            HZ2 = np.delete(HZ, r, axis=0) if t == 'Z' else HZ
            HX2 = np.delete(HX2, q, axis=1)
            HZ2 = np.delete(HZ2, q, axis=1)
            if compute_k(HX2, HZ2) != k0:
                continue
            if not verify_css(HX2, HZ2):
                continue
            d2 = distance_rand(HX2, HZ2, trials=trials, seed=1)
            if d2 < d_floor:
                continue
            HX, HZ = HX2, HZ2
            removed += 1
            accepted = True
            n2 = HX.shape[1]
            print(f"  removed qubit (type {t}): n={n2} k={k0} d<={d2} "
                  f"eff={k0*d2*d2/n2:.3f}")
            break
        if not accepted:
            break
    n2 = HX.shape[1]
    d2 = distance_rand(HX, HZ, trials=trials, seed=1)
    print(f"final: n={n2} k={k0} d<={d2} removed={removed}")
    return {"n": n2, "k": k0, "d": d2, "removed": removed,
            "eff": k0 * d2 * d2 / n2}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=1500)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--d-floor", type=int, default=5)
    ap.add_argument("--max-removals", type=int, default=20)
    ap.add_argument("--output", type=Path, default=ROOT / "research" / "candidates" / "dense-remove-probe.json")
    args = ap.parse_args()
    results = []
    for s in range(3):
        r = probe(trials=args.trials, seed=args.seed + s, d_floor=args.d_floor,
                  max_removals=args.max_removals)
        r["seed"] = args.seed + s
        results.append(r)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2) + "\n")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()