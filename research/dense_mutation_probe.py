#!/usr/bin/env python3
"""Probe dense-packed surface layout (route 5, five-patch variants).

The board's [[101,5,5]] dense-packed surface code (arXiv:2511.06758) is
reconstructed by research/build_dense_surface.py.  This probe rebuilds the
code and checks whether any empty odd,odd site in the dense lattice has
occupied diagonal ancillas (i.e. whether the layout can be extended by adding
a data qubit).  It reports the base (n,k,d) with the kit's exact GF(2) core
(distance is an UPPER BOUND via surrogate).

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

from css import compute_k  # noqa: E402
from surrogate import distance_rand  # noqa: E402

sys.path.insert(0, str(ROOT / "research"))
from build_dense_surface import build  # noqa: E402


def probe(trials=1500, seed=0):
    HX, HZ, coords, data, allcoords = build(5)
    n = HX.shape[1]
    k0 = compute_k(HX, HZ)
    d0 = distance_rand(HX, HZ, trials=trials, seed=seed)
    print(f"base [[{n},{k0},d<={d0}]]")
    results = [{"variant": "base", "n": n, "k": k0, "d": d0,
                "eff": k0 * d0 * d0 / n}]

    # normalized coord -> index
    coord2idx = {tuple(c): i for i, c in enumerate(coords)}
    # data qubits are at normalized (odd/2, odd/2).  Find empty odd,odd sites
    # in the dense lattice whose 4 diagonal-neighbor ancilla sites are all
    # occupied (a necessary condition for adding a data qubit with checks).
    xmax = int(max(c[0] for c in coords)) * 2
    ymax = int(max(c[1] for c in coords)) * 2
    site_set = set(allcoords)
    candidates = []
    for x in range(1, xmax + 1, 2):
        for y in range(1, ymax + 1, 2):
            if (x / 2, y / 2) in coord2idx:
                continue
            anc = [(x + dx, y + dy) for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]]
            if not all(a in site_set for a in anc):
                continue
            nbrs = [(x + dx, y + dy) for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2)]]
            have = sum(1 for nb in nbrs if (nb[0] / 2, nb[1] / 2) in coord2idx)
            candidates.append((x, y, have))
    print(f"candidate empty sites: {len(candidates)}")
    for x, y, have in candidates:
        print(f"  ({x},{y}) existing diagonal data neighbors: {have}")
    results.append({"variant": "empty_sites", "count": len(candidates)})
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=1500)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--output", type=Path, default=ROOT / "research" / "candidates" / "dense-add-probe.json")
    args = ap.parse_args()
    results = probe(trials=args.trials, seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2) + "\n")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()