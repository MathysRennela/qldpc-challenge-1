"""Regression tests for research/kit/spectral.py.

Checks (2) and (3) from the spectral selftest, wired into the CI suite
per vprusso's review of PR #1328.  Check (2) is a soundness test for
spectral_k (exact k via matrix rank on random odd grids); check (3) is a
soundness test for the distance floor (floor must not exceed a witnessed
upper bound, since an unsound floor silently discards good codes).

Run: uv run pytest research/test_spectral.py
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, "kit"))

import numpy as np
from bb import build_bb
from css import compute_k
from spectral import colon_lower_bound, spectral_k
from surrogate import distance_rand


def test_spectral_k_matches_matrix_rank():
    """Check (2): spectral_k must agree with matrix rank on random odd grids."""
    rng = np.random.default_rng(7)
    bad = 0
    for _ in range(60):
        l, m = (int(a) for a in rng.choice([3, 5, 7, 9, 15], size=2))  # noqa: E741
        A = [tuple(int(v) for v in rng.integers(0, (l, m))) for _ in range(3)]
        A = list(dict.fromkeys(A)) or [(0, 0)]
        B = [tuple(int(v) for v in rng.integers(0, (l, m))) for _ in range(3)]
        B = list(dict.fromkeys(B)) or [(0, 1)]
        ks = spectral_k(l, m, A, B)
        km = compute_k(*build_bb(l, m, A, B))
        if ks != km:
            bad += 1
    assert bad == 0, f"spectral_k vs matrix rank: {bad}/60 mismatches on seeded grids (rng=7)"


def test_floor_not_above_witnessed_upper_bound():
    """Soundness check: the distance floor must not exceed a witnessed upper bound.

    An unsound floor discards good codes silently, with no failing test and
    nothing on the board to notice.  This is the check the campaign uses to
    declare candidates dead.
    """
    rng = np.random.default_rng(11)
    viol = 0
    for t in range(20):
        l, m = (int(a) for a in rng.choice([3, 5, 7, 9], size=2))  # noqa: E741
        A = [tuple(int(v) for v in rng.integers(0, (l, m))) for _ in range(3)]
        B = [tuple(int(v) for v in rng.integers(0, (l, m))) for _ in range(3)]
        lb = colon_lower_bound(l, m, A, B)
        du = distance_rand(*build_bb(l, m, A, B), trials=300, seed=t)
        if lb["d_lower"] > du:
            viol += 1
    assert viol == 0, f"distance floor exceeded a witnessed upper bound in {viol}/20 random cases (rng=11)"
