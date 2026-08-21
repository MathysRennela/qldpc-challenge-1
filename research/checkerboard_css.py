#!/usr/bin/env python3
"""Build a clean checkerboard-plaquette code with CSS-preserving boundaries.

A clean checkerboard (X on even 2x2 plaquettes, Z on odd) has weight-1 X
logicals on the top/bottom rows (qubits touched by no Z-check).  The fix is to
add weight-2 boundary checks that (a) cover those qubits and (b) commute with
every opposite-type plaquette.

This module builds the code and verifies CSS, k, and that no weight-1 logical
remains.  It is a building block for the route-5 boundary-shaping probe.
"""
from __future__ import annotations

import numpy as np

from css import compute_k, verify_css, in_rowspace  # noqa: E402


def build_checkerboard_css(L):
    """Checkerboard plaquette code with CSS-preserving weight-2 boundaries.

    Interior: X on even 2x2 plaquettes (top-left (i+j) even), Z on odd.
    Boundary: add weight-2 checks on the outer edges so every boundary qubit
    is covered by both an X and a Z check, and so CSS commutation holds.

    The rule (derived from the board's [[656,114,3]] code): on the top and
    bottom rows, the qubits are covered by X-plaquettes but not Z-plaquettes;
    add weight-2 Z-checks there.  On the left and right columns, qubits are
    covered by Z-plaquettes but not X-plaquettes; add weight-2 X-checks there.
    A weight-2 check on an edge is placed so it shares an even number of
    qubits with every opposite-type plaquette (so it commutes).
    """
    n = L * L
    def idx(i, j):
        return i * L + j
    xrows, zrows = [], []
    # interior plaquettes
    for i in range(L - 1):
        for j in range(L - 1):
            qs = [idx(i, j), idx(i, j + 1), idx(i + 1, j), idx(i + 1, j + 1)]
            row = np.zeros(n, dtype=np.int8)
            row[qs] = 1
            if (i + j) % 2 == 0:
                xrows.append(row)
            else:
                zrows.append(row)
    # boundary weight-2 checks
    # top row (i=0): add Z-checks on horizontal pairs (0,j)-(0,j+1) for
    #   j where the pair is NOT already inside a Z-plaquette's top edge.
    #   A Z-plaquette with top-left (0,j) covers (0,j),(0,j+1) on its top edge
    #   only if (0+j) odd -> j odd.  So pairs at even j are uncovered -> add.
    for j in range(0, L - 1, 2):
        row = np.zeros(n, dtype=np.int8)
        row[idx(0, j)] = 1; row[idx(0, j + 1)] = 1
        zrows.append(row)
    # bottom row (i=L-1): same, pairs at even j
    for j in range(0, L - 1, 2):
        row = np.zeros(n, dtype=np.int8)
        row[idx(L - 1, j)] = 1; row[idx(L - 1, j + 1)] = 1
        zrows.append(row)
    # left column (j=0): add X-checks on vertical pairs (i,0)-(i+1,0) for
    #   i where the pair is not inside an X-plaquette's left edge.
    #   X-plaquette with top-left (i,0) covers (i,0),(i+1,0) if (i+0) even.
    for i in range(0, L - 1, 2):
        row = np.zeros(n, dtype=np.int8)
        row[idx(i, 0)] = 1; row[idx(i + 1, 0)] = 1
        xrows.append(row)
    # right column (j=L-1): same
    for i in range(0, L - 1, 2):
        row = np.zeros(n, dtype=np.int8)
        row[idx(i, L - 1)] = 1; row[idx(i + 1, L - 1)] = 1
        xrows.append(row)
    HX = np.array(xrows, dtype=np.int8) if xrows else np.zeros((0, n), dtype=np.int8)
    HZ = np.array(zrows, dtype=np.int8) if zrows else np.zeros((0, n), dtype=np.int8)
    coords = [[float(i), float(j)] for i in range(L) for j in range(L)]
    return HX, HZ, coords


def check(L):
    HX, HZ, coords = build_checkerboard_css(L)
    n = HX.shape[1]
    css = verify_css(HX, HZ)
    k = compute_k(HX, HZ)
    # weight-1 logicals
    w1 = []
    for q in range(n):
        v = np.zeros(n, dtype=np.int8); v[q] = 1
        if (HZ @ v % 2).max() == 0 and not in_rowspace(v, HX):
            w1.append(('X', coords[q]))
        if (HX @ v % 2).max() == 0 and not in_rowspace(v, HZ):
            w1.append(('Z', coords[q]))
    return {"L": L, "n": n, "k": k, "css": bool(css), "w1": w1,
            "hx": HX.shape[0], "hz": HZ.shape[0]}


if __name__ == "__main__":
    for L in (6, 8, 10, 12):
        r = check(L)
        print(f"L={L}: n={r['n']} k={r['k']} css={r['css']} "
              f"w1_logicals={len(r['w1'])} (hx={r['hx']},hz={r['hz']})")
        if r['w1']:
            print("   w1:", r['w1'][:5])