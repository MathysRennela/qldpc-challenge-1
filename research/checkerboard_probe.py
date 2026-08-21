#!/usr/bin/env python3
"""Probe the checkerboard plaquette geometry (route 5, boundary shaping).

The board's [[656,114,3]] code is a single-layer weight-4 checkerboard
plaquette code: qubits on an LxL grid, X-checks on 2x2 plaquettes of one
checkerboard color, Z-checks on the other, with boundary shaping (chamfer +
Young diagram) that boosts k.  This script builds a clean, reproducible
checkerboard-plaquette family at several sizes, measures (n,k,d) with the kit's
exact GF(2) core and the surrogate (distance is an UPPER BOUND), and probes
simple boundary-shaping variants.

It is a probe: it does NOT claim a find.  Any candidate that looks promising is
persisted to research/candidates/ for later packaging through the standard kit
+ trusted validator.
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


def build_checkerboard(L, x_offset=0, y_offset=0, keep=None):
    """Clean checkerboard plaquette code on an LxL qubit grid.

    X-checks: 2x2 plaquettes whose top-left corner (i,j) has (i+j) even.
    Z-checks: 2x2 plaquettes whose top-left corner (i,j) has (i+j) odd.
    A plaquette is placed only if all 4 of its qubits are inside the grid and
    in `keep` (a set of (i,j) sites to retain, for boundary shaping).
    Returns (HX, HZ, coords, kept_sites).
    """
    # qubit index = i*L + j
    def idx(i, j):
        return i * L + j

    n = L * L
    xrows, zrows = [], []
    for i in range(L - 1):
        for j in range(L - 1):
            if keep is not None and not all(
                (i + di, j + dj) in keep for di in (0, 1) for dj in (0, 1)
            ):
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
    coords = [[float(i), float(j)] for i in range(L) for j in range(L)]
    return HX, HZ, coords


def gf2_rank(A):
    A = (A % 2).copy()
    m, c = A.shape
    r = 0
    for col in range(c):
        piv = np.nonzero(A[r:, col])[0]
        if len(piv) == 0:
            continue
        piv = piv[0] + r
        A[[r, piv]] = A[[piv, r]]
        for rr in range(m):
            if rr != r and A[rr, col]:
                A[rr] ^= A[r]
        r += 1
        if r == m:
            break
    return r


def probe(L, trials=2000, seed=0):
    HX, HZ, coords = build_checkerboard(L)
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
    ap.add_argument("--sizes", type=int, nargs="*", default=[8, 12, 16, 20, 24])
    ap.add_argument("--trials", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--output", type=Path, default=ROOT / "research" / "candidates" / "checkerboard-probe.json")
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