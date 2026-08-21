#!/usr/bin/env python3
"""Probe checkerboard-plaquette boundary shaping (route 5).

The board's [[656,114,3]] code is a single-layer weight-4 checkerboard
plaquette code with boundary shaping that boosts k.  A clean checkerboard has
weight-1 corner logicals (d=1).  This probe tests systematic boundary-shaping
variants -- corner removal, edge-qubit removal, and plaquette trimming -- to
find a clean, reproducible family with d>=3 and high k, and reports (n,k,d)
with the kit's exact GF(2) core (distance is an UPPER BOUND via surrogate).

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


def build_checkerboard(L, keep):
    """Checkerboard plaquette code on an LxL grid restricted to `keep` sites.

    X-checks: 2x2 plaquettes with top-left (i+j) even; Z-checks: (i+j) odd.
    A plaquette is placed only if all 4 qubits are in `keep`.
    Returns (HX, HZ, coords) restricted to kept qubits.
    """
    n = L * L
    def idx(i, j):
        return i * L + j
    xrows, zrows = [], []
    for i in range(L - 1):
        for j in range(L - 1):
            if not all((i + di, j + dj) in keep for di in (0, 1) for dj in (0, 1)):
                continue
            qs = [idx(i, j), idx(i, j + 1), idx(i + 1, j), idx(i + 1, j + 1)]
            row = np.zeros(n, dtype=np.int8)
            row[qs] = 1
            if (i + j) % 2 == 0:
                xrows.append(row)
            else:
                zrows.append(row)
    HX = np.array(xrows, dtype=np.int8) if xrows else np.zeros((0, n), dtype=np.int8)
    HZ = np.array(zrows, dtype=np.int8) if zrows else np.zeros((0, n), dtype=np.int8)
    occidx = sorted(idx(x, y) for (x, y) in keep)
    HX = HX[:, occidx]
    HZ = HZ[:, occidx]
    coords = [[float(x), float(y)] for (x, y) in keep]
    return HX, HZ, coords


def full_grid(L):
    return {(i, j) for i in range(L) for j in range(L)}


def remove_corners(keep, L, n_corners=1):
    """Remove the n_corners qubits at each corner of the grid."""
    k = set(keep)
    corners = [(0, 0), (0, L - 1), (L - 1, 0), (L - 1, L - 1)]
    for c in corners[:n_corners]:
        k.discard(c)
    return k


def probe(L, keep, trials=1500, seed=0):
    HX, HZ, coords = build_checkerboard(L, keep)
    n = HX.shape[1]
    if n == 0:
        return None
    css = verify_css(HX, HZ)
    k = compute_k(HX, HZ)
    d = distance_rand(HX, HZ, trials=trials, seed=seed)
    return {
        "L": L, "n": n, "k": k, "css": bool(css), "d": d,
        "eff": k * d * d / n if n else 0.0,
        "hx_rows": int(HX.shape[0]), "hz_rows": int(HZ.shape[0]),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", type=int, nargs="*", default=[8, 12, 16])
    ap.add_argument("--trials", type=int, default=1500)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--output", type=Path, default=ROOT / "research" / "candidates" / "checkerboard-shaping-probe.json")
    args = ap.parse_args()

    results = []
    for L in args.sizes:
        for nc in (0, 1, 2, 4):
            keep = full_grid(L)
            if nc:
                keep = remove_corners(keep, L, nc)
            r = probe(L, keep, trials=args.trials, seed=args.seed)
            if r is None:
                continue
            results.append(r)
            print(f"L={L} corners_removed={nc}: n={r['n']} k={r['k']} css={r['css']} "
                  f"d<={r['d']} eff={r['eff']:.3f}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2) + "\n")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()