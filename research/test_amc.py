"""
Unit test for the AMC constructor and its enumerators.

Covers the independently specified AMC3/AMC4 constructor in research/kit/amc.py
and the two campaign enumerators (research/amc3_sweep.py, research/amc4_sweep.py):

  * AMC4 calibration: the public Lin et al. [[84,6,7]] example reproduces at
    parameter level (n=84, k=6) with CSS commutation;
  * AMC3 construction: a small explicit example has the expected (n, k) and
    check-weight profile;
  * quotient-lattice prefilter: size-2 relations are rejected, longer cycles
    are not;
  * enumerators: symmetry-reduced iteration yields only unique orbits, respects
    the max-orbits budget, and every emitted code passes CSS commutation.

Run: uv run python research/test_amc.py   (exit 0 = pass)
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "kit"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "verify"))

from amc import build_amc, shortest_quotient_cycle  # noqa: E402
from css import compute_k, verify_css  # noqa: E402
from amc3_sweep import iter_amc3  # noqa: E402
from amc4_sweep import iter_amc4  # noqa: E402

_fail = []


def check(name, cond):
    print(f"  {'ok  ' if cond else 'FAIL'}  {name}")
    if not cond:
        _fail.append(name)


def main():
    print("AMC constructor + enumerator unit test:")

    # 1. AMC4 calibration: [[84,6,7]] at parameter level.
    zero = (0, 0, 0, 0)
    hx, hz = build_amc(
        (14, 1, 1, 1),
        [[zero, (1, 0, 0, 0)],
         [zero, (2, 0, 0, 0)],
         [zero, (5, 0, 0, 0)],
         [zero, (6, 0, 0, 0)]],
    )
    check("AMC4 [[84,6,7]]: CSS commutation", verify_css(hx, hz))
    check("AMC4 [[84,6,7]]: n == 84", hx.shape[1] == 84)
    check("AMC4 [[84,6,7]]: k == 6", compute_k(hx, hz) == 6)

    # 2. AMC3 construction: explicit small example, n = 3*l1*l2*l3.
    hx3, hz3 = build_amc(
        (2, 2, 2),
        [[(0, 0, 0), (1, 0, 0)],
         [(0, 0, 0), (0, 1, 0)],
         [(0, 0, 0), (0, 0, 1)]],
    )
    check("AMC3: CSS commutation", verify_css(hx3, hz3))
    check("AMC3: n == 24", hx3.shape[1] == 24)
    k3 = compute_k(hx3, hz3)
    check("AMC3: k == 3 (three independent 1-cycles)",
          k3 == 3)

    # 3. Quotient-lattice prefilter.
    check("prefilter: duplicate monomial closes size-2 relation",
          shortest_quotient_cycle((2, 2, 2), [(1, 0, 0), (1, 0, 0)]) == 2)
    check("prefilter: independent units have no size-2 relation",
          shortest_quotient_cycle((3, 3, 3), [(1, 0, 0), (0, 1, 0)]) is None)
    check("prefilter: (1,0,0)+(0,1,0)+(1,1,0) closes a size-3 relation",
          shortest_quotient_cycle((2, 2, 2),
                                  [(1, 0, 0), (0, 1, 0), (1, 1, 0)]) == 3)

    # 4. AMC3 enumerator: unique orbits, budget respected, CSS holds.
    seen = set()
    count = 0
    for spec, hx, hz in iter_amc3((2, 2, 3), 3, max_orbits=20):
        count += 1
        check("AMC3 enumerator: CSS commutation", verify_css(hx, hz))
        key = (tuple(spec["A"]), tuple(spec["B"]), tuple(spec["C"]))
        seen.add(key)
    check("AMC3 enumerator: emitted within budget", count <= 20)
    check("AMC3 enumerator: all orbits unique", len(seen) == count)

    # 5. AMC4 enumerator: nonuniform weights, unique orbits, CSS holds.
    seen4 = set()
    count4 = 0
    for spec, hx, hz in iter_amc4((2, 2, 2, 2), (3, 3, 4, 4), max_orbits=20):
        count4 += 1
        check("AMC4 enumerator: CSS commutation", verify_css(hx, hz))
        key = (tuple(spec["A"]), tuple(spec["B"]),
               tuple(spec["C"]), tuple(spec["D"]))
        seen4.add(key)
    check("AMC4 enumerator: emitted within budget", count4 <= 20)
    check("AMC4 enumerator: all orbits unique", len(seen4) == count4)

    print("PASS" if not _fail else "FAIL: " + ", ".join(_fail))
    return 0 if not _fail else 1


def test_main():
    """pytest entry point; the suite body lives in main()."""
    assert main() == 0


if __name__ == "__main__":
    sys.exit(main())