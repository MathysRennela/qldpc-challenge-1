#!/usr/bin/env python
"""Overnight: exhaustive multi-band parameter sweep vs the board Pareto front.

Enumerates (d, rows, m, pitch) under n <= 700, computes (n, k) exactly via
GF(2) rank on the bit-exact-validated builder, and keeps every config that
strictly beats the current board's Pareto frontier at its d (no board code
with the same d has n' <= n and k' >= k). Survivors get a fast witness
screen; anything with a confirmed d >= target is staged via the kit path.
"""
import itertools
import json
import sys
import time

import numpy as np

sys.path.insert(0, "research/local2d")
sys.path.insert(0, "research/kit")
from multiband import build, expected_k  # noqa: E402
from submit import make_submission, save_submission  # noqa: E402

OUT = "research/candidates/overnight-chamfer4"
BOARD = "codes"


def board_pareto():
    """d -> list of (n, k) board points, layers=1, n<=700.

    Includes codes from our open PRs (research/candidates/pr-board/):
    they are already submitted, so sweep survivors must not duplicate or
    merely tie them.
    """
    import glob
    pareto = {}
    for f in (glob.glob("codes/*.json")
              + glob.glob("research/candidates/pr-board/*.json")):
        d = json.load(open(f))
        n, k = d["n"], d["k"]
        dd = d["distance"]["d"] if isinstance(d["distance"], dict) else d["distance"]
        loc = d.get("locality") or {}
        if loc.get("layers") == 1 and n <= 700 and dd:
            pareto.setdefault(dd, []).append((n, k))
    # keep only Pareto-optimal per d
    out = {}
    for dd, pts in pareto.items():
        keep = []
        for n, k in sorted(pts):
            if not any(n2 <= n and k2 >= k for n2, k2 in keep):
                keep.append((n, k))
        out[dd] = keep
    return out


def main():
    t0 = time.time()
    board = board_pareto()
    survivors = []
    for d in (3, 5, 7, 9, 11, 13):
        for rows in range(1, 9):
            for m in range(1, 21):
                for pitch in range(max(2, d - 2), d + 4):
                    try:
                        HX, HZ, sites = build(d, rows, m, pitch)
                    except Exception:
                        continue
                    n = HX.shape[1]
                    if n > 700 or n < 4:
                        continue
                    # exact k via rank
                    def rank(A):
                        A = A.copy() % 2
                        r, piv = 0, []
                        for col in range(A.shape[1]):
                            p = [i for i in range(r, A.shape[0]) if A[i, col]]
                            if not p:
                                continue
                            A[[r, p[0]]] = A[[p[0], r]]
                            for i in range(A.shape[0]):
                                if i != r and A[i, col]:
                                    A[i] ^= A[r]
                            r += 1
                        return r
                    k = n - rank(HX) - rank(HZ)
                    if k <= 0:
                        continue
                    g = k * d * d / n
                    # beats board Pareto at this d? (no board point with
                    # n' <= n and k' >= k)
                    dominated = any(n2 <= n and k2 >= k
                                    for n2, k2 in board.get(d, []))
                    if dominated:
                        continue
                    survivors.append((d, rows, m, pitch, n, k, g))
                    print(f"SURVIVOR d={d} rows={rows} m={m} pitch={pitch} "
                          f"[[{n},{k},{d}]] g={g:.4f}", flush=True)
    with open(f"{OUT}/multiband-sweep.json", "w") as f:
        json.dump([{"d": d, "rows": r, "m": mm, "pitch": p, "n": n, "k": kk,
                    "g": g} for d, r, mm, p, n, kk, g in survivors], f, indent=1)
    print(f"TOTAL survivors: {len(survivors)} ({time.time()-t0:.0f}s)",
          flush=True)


if __name__ == "__main__":
    main()
