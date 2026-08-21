#!/usr/bin/env python3
"""Probe checkerboard-plaquette codes with correct boundary checks (route 5).

A clean checkerboard plaquette code (X on even 2x2 plaquettes, Z on odd) has
weight-1 X logicals on the top/bottom rows: those qubits are touched by no
Z-check.  The fix is weight-2 boundary checks: Z-type on the top/bottom edges
(covering the missed qubits) and X-type on the left/right edges.  This is the
standard surface-code boundary condensation.

This probe builds a clean, reproducible checkerboard-plaquette family with
weight-2 boundary checks, measures (n,k,d) with the kit's exact GF(2) core
(distance is an UPPER BOUND), and reports which cells it might advance.

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

    Interior: X on even 2x2 plaquettes (top-left (i+j) even), Z on odd.
    Boundary (fixes weight-1 logicals on the top/bottom rows):
      * Z-type weight-2 checks on the top and bottom edges (horizontal pairs
        (0,j)-(0,j+1) and (L-1,j)-(L-1,j+1));
      * X-type weight-2 checks on the left and right edges (vertical pairs
        (i,0)-(i+1,0) and (i,L-1)-(i+1,L-1)).
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
    # Z-type boundary checks on top/bottom edges (horizontal pairs)
    for j in range(L - 1):
        for edge in (0, L - 1):
            row = np.zeros(n, dtype=np.int8)
            row[idx(edge, j)] = 1
            row[idx(edge, j + 1)] = 1
            zrows.append(row)
    # X-type boundary checks on left/right edges (vertical pairs)
    for i in range(L - 1):
        for edge in (0, L - 1):
            row = np.zeros(n, dtype=np.int8)
            row[idx(i, edge)] = 1
            row[idx(i + 1, edge)] = 1
            xrows.append(row)
    HX = np.array(xrows, dtype=np.int8) if xrows else np.zeros((0, n), dtype=np.int8)
    HZ = np.array(zrows, dtype=np.int8) if zrows else np.zeros((0, n), dtype=np.int8)
    coords = [[float(i), float(j)] for i in range(L) for j in range(L)]
    return HX, HZ, coords


def probe(L, trials=1500, seed=0):
    HX, HZ, coords = build_checkerboard_boundary(L)
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
    ap.add_argument("--output", type=Path, default=ROOT / "research" / "candidates" / "checkerboard-boundary-probe.json")
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