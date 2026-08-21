#!/usr/bin/env python3
"""Probe checkerboard-plaquette codes with surface-code boundaries (route 5).

A clean checkerboard plaquette code (X on even 2x2 plaquettes, Z on odd) has
weight-1 corner/edge logicals.  Standard surface-code boundary treatment adds
weight-2 boundary checks (truncated plaquettes on the boundary).  This probe
builds a clean, reproducible checkerboard-plaquette family with weight-2
boundary checks, measures (n,k,d) with the kit's exact GF(2) core (distance is
an UPPER BOUND), and reports which cells it might advance.

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


def build_checkerboard_boundary(L):
    """Checkerboard plaquette code on an LxL grid with weight-2 boundary checks.

    Interior: X on even 2x2 plaquettes, Z on odd.
    Boundary: for each boundary plaquette whose 4th qubit would be out of
    bounds, add a weight-2 check on the two in-grid qubits (surface-code
    boundary condensation).  X-type boundary terms hang off the top/bottom
    edges; Z-type off the left/right edges (matching the planar convention).
    Returns (HX, HZ, coords).
    """
    n = L * L
    def idx(i, j):
        return i * L + j
    xrows, zrows = [], []
    for i in range(L - 1):
        for j in range(L - 1):
            qs = [idx(i, j), idx(i, j + 1), idx(i + 1, j), idx(i + 1, j + 1)]
            row = np.zeros(n, dtype=np.int8)
            row[qs] = 1
            if (i + j) % 2 == 0:
                xrows.append(row)
            else:
                zrows.append(row)
    # Boundary weight-2 checks: for plaquettes that would extend off-grid.
    # X boundary (even plaquettes) hangs off top/bottom rows; Z off left/right.
    for i in range(L - 1):
        for j in range(L - 1):
            if (i + j) % 2 == 0:  # X plaquette
                # hangs off bottom (i+1==L) or top (i<0) -> but i in [0,L-2]
                # only bottom edge i==L-2 has i+1==L-1 in grid; top handled by i range
                pass
    # Simpler: add weight-2 checks on the outermost boundary pairs.
    # X boundary checks on top/bottom rows (horizontal pairs)
    for j in range(L - 1):
        # top row
        row = np.zeros(n, dtype=np.int8)
        row[idx(0, j)] = 1; row[idx(0, j + 1)] = 1
        zrows.append(row)  # Z-type on top? keep flexible
    return None


def build_surface_checkerboard(L):
    """Standard surface-code checkerboard: qubits on LxL, X-stabilizers on
    even plaquettes (2x2), Z on odd, plus weight-2 boundary stabilizers so the
    code is a proper surface code with d ~ L."""
    n = L * L
    def idx(i, j):
        return i * L + j
    xrows, zrows = [], []
    for i in range(L - 1):
        for j in range(L - 1):
            qs = [idx(i, j), idx(i, j + 1), idx(i + 1, j), idx(i + 1, j + 1)]
            row = np.zeros(n, dtype=np.int8)
            row[qs] = 1
            if (i + j) % 2 == 0:
                xrows.append(row)
            else:
                zrows.append(row)
    # weight-2 boundary checks: X-type on top/bottom edges, Z-type on left/right
    # top edge: horizontal pairs (0,j)-(0,j+1) -> Z boundary
    for j in range(L - 1):
        row = np.zeros(n, dtype=np.int8)
        row[idx(0, j)] = 1; row[idx(0, j + 1)] = 1
        zrows.append(row)
    # bottom edge
    for j in range(L - 1):
        row = np.zeros(n, dtype=np.int8)
        row[idx(L - 1, j)] = 1; row[idx(L - 1, j + 1)] = 1
        zrows.append(row)
    # left edge: vertical pairs -> X boundary
    for i in range(L - 1):
        row = np.zeros(n, dtype=np.int8)
        row[idx(i, 0)] = 1; row[idx(i + 1, 0)] = 1
        xrows.append(row)
    # right edge
    for i in range(L - 1):
        row = np.zeros(n, dtype=np.int8)
        row[idx(i, L - 1)] = 1; row[idx(i + 1, L - 1)] = 1
        xrows.append(row)
    HX = np.array(xrows, dtype=np.int8) if xrows else np.zeros((0, n), dtype=np.int8)
    HZ = np.array(zrows, dtype=np.int8) if zrows else np.zeros((0, n), dtype=np.int8)
    coords = [[float(i), float(j)] for i in range(L) for j in range(L)]
    return HX, HZ, coords


def probe(L, trials=1500, seed=0):
    HX, HZ, coords = build_surface_checkerboard(L)
    n = HX.shape[1]
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
    ap.add_argument("--sizes", type=int, nargs="*", default=[6, 8, 10, 12, 14, 16])
    ap.add_argument("--trials", type=int, default=1500)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--output", type=Path, default=ROOT / "research" / "candidates" / "surface-checkerboard-probe.json")
    args = ap.parse_args()

    results = []
    for L in args.sizes:
        r = probe(L, trials=args.trials, seed=args.seed)
        results.append(r)
        print(f"L={L}: n={r['n']} k={r['k']} css={r['css']} d<={r['d']} "
              f"eff={r['eff']:.3f} (hx={r['hx_rows']},hz={r['hz_rows']})")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2) + "\n")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()