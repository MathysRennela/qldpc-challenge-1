#!/usr/bin/env python
"""Manifold subtraction for the multi-band dense-packing family.

Enumerates rows x m at pitch = pitch_min(d) (higher pitches only add n at
fixed k, so are dominated), keeps n <= 700, scores g = k*d^2/n, and subtracts
every (n, k, d) already on the board. Output: uncovered points ranked by g.
"""
import sys

import numpy as np

sys.path.insert(0, "research/local2d")
from multiband import build, code_stats, expected_k  # noqa: E402

PITCH_MIN = {3: 4, 5: 6, 7: 10, 9: 12}   # 6/10/12 measured; 4 = board-used at d=3
N_CAP = 700


def board_points():
    import glob
    import json
    pts = set()
    for f in glob.glob("codes/*.json"):
        try:
            j = json.load(open(f))
            pts.add((j["n"], j["k"], j["distance"]["d"]))
        except Exception:
            pass
    return pts


def main():
    board = board_points()
    print(f"board points loaded: {len(board)}")
    for d, pitch in sorted(PITCH_MIN.items()):
        rows_out = []
        for rows in range(2, 40):
            for m in range(2, 40):
                k = expected_k(rows, m)
                if k < 1:
                    continue
                HX, HZ, _ = build(d, rows, m, pitch)
                st = code_stats(HX, HZ)
                if st["n"] > N_CAP:
                    break
                if not (st["css"] and st["k"] == k and st["components"] == 1
                        and st["wmax"] == 4):
                    continue
                g = k * d * d / st["n"]
                covered = (st["n"], k, d) in board
                rows_out.append((g, st["n"], k, rows, m, covered))
            # n grows with m; inner break handles it, but rows loop has no
            # monotone cutoff in general -- rely on the m-range cap
        rows_out.sort(reverse=True)
        unc = [r for r in rows_out if not r[5]]
        best_cov = max((r[0] for r in rows_out if r[5]), default=0)
        best_unc = unc[0] if unc else None
        print(f"\n=== d={d} pitch={pitch}: {len(rows_out)} manifold points "
              f"under cap, {len(unc)} uncovered ===")
        print(f"best covered g={best_cov:.4f}  "
              f"best uncovered g={best_unc[0]:.4f} at [[{best_unc[1]},{best_unc[2]},{d}]]"
              if best_unc else "all covered")
        print("top uncovered (g, n, k, rows, m):")
        for g, n, k, rows, m, _ in unc[:8]:
            print(f"  g={g:.4f}  [[{n},{k},{d}]]  rows={rows} m={m}")


if __name__ == "__main__":
    main()
