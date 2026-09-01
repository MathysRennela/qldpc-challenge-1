#!/usr/bin/env python
"""Measure pitch_min for the raised-pitch two-band family at d = 11, 13.

Method per notes/367-19-5.md: build (d, rows=2, m=3, pitch) for even pitch,
check CSS commutation + exact k, witness-screen the distance; pitch_min is
the smallest pitch with d_ub >= d. Known: 6 (d=5), 10 (d=7), 12 (d=9).
"""
import sys
import time

import numpy as np

sys.path.insert(0, "research/local2d")
from multiband import build  # noqa: E402
from chamfer4 import gf2_rank  # noqa: E402
from surrogate import distance_rand  # noqa: E402


def main():
    for d in (5, 7, 9, 11, 13):
        print(f"=== d={d} (rows=4, m=3, raised-pitch regime) ===", flush=True)
        for pitch in range(2, 2 * d, 2):
            try:
                HX, HZ, xy = build(d, 4, 3, pitch)
            except Exception as e:
                print(f"  pitch={pitch}: build fail ({e})", flush=True)
                continue
            n = HX.shape[1]
            comm = not (HX @ HZ.T % 2).any()
            k = n - gf2_rank(HX) - gf2_rank(HZ)
            k_exp = 10  # expected_k(4, 3)
            if not comm:
                print(f"  pitch={pitch}: CSS BROKEN (k arithmetic meaningless)",
                      flush=True)
                continue
            if k <= 0:
                print(f"  pitch={pitch}: k=0", flush=True)
                continue
            if k != k_exp:
                print(f"  pitch={pitch}: n={n} k={k} (k_exp={k_exp}) "
                      f"- k not unlocked", flush=True)
                continue
            d_ub = distance_rand(HX, HZ, trials=4000, seed=pitch,
                                 backend="fast", threads=4)
            mark = " <-- pitch_min candidate" if d_ub >= d else ""
            print(f"  pitch={pitch}: n={n} k={k} d_ub={d_ub}{mark}", flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
