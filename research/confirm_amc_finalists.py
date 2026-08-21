#!/usr/bin/env python3
"""Fresh-seed confirmation of the AMC3 board-advancing finalists.

Rebuilds each candidate from its spec, re-screens distance with a fresh seed
(different from the campaign seed), and re-runs the trusted validator with a
fresh seed.  If a lighter logical is found, it would be preserved and the
claim lowered -- here we confirm the claimed distance holds.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "research" / "kit"), str(ROOT / "verify")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from amc import build_amc  # noqa: E402
from css import compute_k, verify_css  # noqa: E402
from surrogate import distance_rand, lightest_logical  # noqa: E402
from validate_candidate import validate_candidate  # noqa: E402

# (doc path, orders, [A,B,C]) -- specs recovered from the sweep output.
FINALISTS = [
    ("research/candidates/amc3-finalist-2-36-9.json",
     (2, 2, 3),
     [[(0, 0, 0), (0, 0, 1), (1, 0, 1), (1, 1, 0)],
      [(0, 0, 0), (0, 0, 1), (0, 1, 0), (1, 0, 1)],
      [(0, 0, 0), (0, 0, 1), (1, 0, 0), (1, 1, 1)]]),
    ("research/candidates/amc3-finalist-1-54-9.json",
     (2, 3, 3),
     [[(0, 0, 0), (0, 1, 1), (1, 0, 1), (1, 1, 0)],
      [(0, 0, 0), (0, 0, 1), (0, 2, 0), (1, 1, 1)],
      [(0, 0, 0), (0, 2, 0), (0, 2, 1), (1, 2, 1)]]),
]
FRESH_SEED = 424242


def main():
    for path, orders, supports in FINALISTS:
        print(f"=== {path} ===")
        hx, hz = build_amc(orders, supports)
        assert verify_css(hx, hz)
        k = compute_k(hx, hz)
        print(f"  rebuilt: n={hx.shape[1]} k={k}")

        # Fresh-seed distance screen (upper bound).
        d = distance_rand(hx, hz, trials=2000, seed=FRESH_SEED)
        wx, xw = lightest_logical(hx, hz, seed=FRESH_SEED)
        wz, zw = lightest_logical(hz, hx, seed=FRESH_SEED)
        print(f"  fresh-seed screen: d<={d}  X-logical={wx}  Z-logical={wz}")

        # Fresh-seed trusted validator on the packaged doc.
        doc = json.load(open(path))
        verdict = validate_candidate(doc, seed=FRESH_SEED)
        print("  passed:", verdict["passed"])
        print("  board_advancing:",
              verdict["gates"]["novelty"]["board_advancing"])
        print("  refute:", verdict["gates"]["refute"])
        print("  dedup:", verdict["gates"]["dedup"])
        print()


if __name__ == "__main__":
    main()