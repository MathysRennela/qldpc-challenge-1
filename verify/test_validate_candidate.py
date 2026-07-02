"""Regression tests for validate_candidate -- the trusted autoresearch gate.

Each case isolates one gate so a failure points at the right place:

  1. a genuinely-new valid code PASSES (verifies, not refuted, not a dup);
  2. an OVER-CLAIM (same checks, witnesses inflated) is caught by the refutation,
     and is *not* a duplicate -- so the failure is unambiguously the distance gate;
  3. an exact BOARD DUPLICATE verifies but does not pass (the dedup gate);
  4. a SCHEMA-BROKEN candidate fails at verify and short-circuits;
  5. every verdict carries the validator's source-hash provenance stamp.

Fixtures are built from research/ (bb, submit) -- that is fine: the code UNDER TEST
(validate_candidate) imports only verify/, never research/. An explicit seed and a small,
off-board fixture keep the run deterministic and fast.

Run: uv run python verify/test_validate_candidate.py  (or pytest)
"""
import copy
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))          # verify/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(       # research/kit (fixtures only)
    os.path.abspath(__file__))), "research", "kit"))

import numpy as np
import gf2
from bb import build_bb
from submit import make_submission
import validate_candidate as V

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = 0
# a small, fast, off-board BB code: [[36,4,6]] on Z_6 x Z_3 (not on the board)
FRESH = (6, 3, [(0, 1), (0, 2), (5, 0)], [(4, 2), (3, 1), (0, 0)])

_fail = []


def check(name, cond):
    print(f"  {'ok  ' if cond else 'FAIL'}  {name}")
    if not cond:
        _fail.append(name)


def heavy_witness(own_H, opp_H, n, target, seed):
    """A genuine nontrivial logical (in ker(opp)\\rowspace(own)) padded with
    stabilizer rows until its weight reaches `target` -- same class, inflated weight."""
    rng = np.random.default_rng(seed)
    v = next(r.copy() % 2 for r in gf2.kernel_basis(opp_H) if not gf2.in_rowspace(r, own_H))
    stab = own_H % 2
    while int(v.sum()) < target:
        v = (v + stab[rng.integers(len(stab))]) % 2
    return v


def main():
    HX, HZ = build_bb(*FRESH)
    n = HX.shape[1]
    good = make_submission(HX, HZ, name="fresh BB", construction="test fixture",
                           authors=["t"], family="bivariate-bicycle", trials=4000)

    print("1. a genuinely-new valid code PASSES:")
    vg = V.validate_candidate(good, seed=SEED)
    check("passes", vg["passed"])
    check("verifies", vg["gates"]["verify"]["ok"])
    check("not refuted", not vg["gates"]["refute"]["refuted"])
    check("not a board duplicate", vg["gates"]["dedup"]["exact_duplicate_of"] is None)
    check("computed cell is weight-6 x unrestricted",
          vg["gates"]["novelty"]["cell"] == ["weight-6", "unrestricted"])

    print("2. an OVER-CLAIM (same checks, inflated witnesses) is rejected:")
    vx = heavy_witness(HX, HZ, n, 20, 1)
    vz = heavy_witness(HZ, HX, n, 20, 2)
    sup = lambda v: sorted(int(j) for j in np.nonzero(v)[0])
    over = copy.deepcopy(good)
    over["distance"] = {
        "d": min(int(vx.sum()), int(vz.sum())),
        "X": {"value": int(vx.sum()), "confidence": "upper_bound", "witness": sup(vx)},
        "Z": {"value": int(vz.sum()), "confidence": "upper_bound", "witness": sup(vz)},
    }
    vo = V.validate_candidate(over, seed=SEED)
    check("does not pass", not vo["passed"])
    check("caught by refute", vo["gates"]["refute"]["refuted"])
    check("verifier still accepts the structure (isolates the distance gate)",
          vo["gates"]["verify"]["ok"])
    check("NOT flagged a duplicate (isolates the distance gate)",
          vo["gates"]["dedup"]["exact_duplicate_of"] is None)

    print("3. an exact BOARD DUPLICATE verifies but does not pass:")
    dup = json.load(open(os.path.join(ROOT, "codes", "16-2-4.json")))
    vd = V.validate_candidate(dup, seed=SEED)
    check("verifies", vd["gates"]["verify"]["ok"])
    check("flagged exact duplicate of 16-2-4.json",
          vd["gates"]["dedup"]["exact_duplicate_of"] == "16-2-4.json")
    check("does not pass", not vd["passed"])

    print("4. a SCHEMA-BROKEN candidate fails at verify and short-circuits:")
    broken = copy.deepcopy(dup)
    broken["k"] = 999                                  # k will not match the recomputed value
    vb = V.validate_candidate(broken, seed=SEED)
    check("fails the verify gate", not vb["gates"]["verify"]["ok"])
    check("does not pass", not vb["passed"])

    print("5. provenance stamp:")
    check("verdict stamps this validator's source hash",
          vg["validator"]["source_sha256"] == V.source_sha256())
    check("source hash is 64 hex chars", len(vg["validator"]["source_sha256"]) == 64)

    print(f"\n{'ALL PASS' if not _fail else 'FAILURES: ' + ', '.join(_fail)}")
    return 1 if _fail else 0


def test_validate_candidate():
    assert main() == 0


if __name__ == "__main__":
    sys.exit(main())
