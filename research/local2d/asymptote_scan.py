#!/usr/bin/env python
"""Valid-regime asymptotic scan of the multi-band family (exact rank).

Collapse boundary established: expected_k is valid iff pitch >= d+1.
Below that, overlapping bands annihilate checks and k collapses.
This scan computes exact g in the valid regime to find the family's
asymptotic constant.
"""
import sys
import time

sys.path.insert(0, "research/local2d")
from multiband import build  # noqa: E402
from chamfer4 import gf2_rank  # noqa: E402


def exact_g(d, rows, m, pitch):
    HX, HZ, xy = build(d, rows, m, pitch)
    n = HX.shape[1]
    k = n - gf2_rank(HX) - gf2_rank(HZ)
    return n, k, k * d * d / n


def main():
    t0 = time.time()
    print("valid-regime asymptotic scan (exact rank):", flush=True)
    for d, pitch in ((5, 6), (5, 7), (7, 8), (7, 9), (9, 10), (11, 12),
                     (13, 14)):
        for rows, m in ((16, 16), (24, 32)):
            try:
                n, k, g = exact_g(d, rows, m, pitch)
            except Exception as e:
                print(f"  (d={d},p={pitch},r={rows},m={m}): fail {e}",
                      flush=True)
                continue
            print(f"  d={d} pitch={pitch} rows={rows} m={m}: n={n} k={k} "
                  f"g={g:.4f} ({time.time()-t0:.0f}s)", flush=True)
    for rows, m in ((32, 48), (48, 64)):
        try:
            n, k, g = exact_g(5, rows, m, 6)
            print(f"  d=5 pitch=6 rows={rows} m={m}: n={n} k={k} g={g:.4f} "
                  f"({time.time()-t0:.0f}s)", flush=True)
        except Exception as e:
            print(f"  fail: {e}", flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
