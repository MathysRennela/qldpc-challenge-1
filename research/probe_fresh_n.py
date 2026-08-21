"""Cheap feasibility probe: does a divisor g of x^N+1 have ANY low-weight
multiple? Instead of full combinatorial enumeration (which explodes), sample a
bounded number of multiplier positions and check the resulting product weight.
This is a feasibility signal only -- not a search.
"""
import sys
import warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "kit")

import numpy as np
from designed_divisor_search import factor_polynomial

CANDIDATES = {
    339: [28],        # k=56
    343: [3, 21],     # k=6, 42
    345: [11, 22, 44],# k=22, 44, 88
    351: [12, 18, 36],# k=24, 36, 72
    357: [8, 24],     # k=16, 48
    331: [30],        # k=60 (prime)
    353: [88],        # k=176
    397: [44],        # k=88
}


def poly_mul_mod2(a, b):
    out = np.zeros(len(a) + len(b) - 1, dtype=np.int8)
    for i, ai in enumerate(a):
        if ai:
            out[i:i + len(b)] ^= b
    return out


def sample_multiple_weight(g, N, mw, n_samples=20000, seed=0):
    """Return the minimum product weight found over sampled multiplier positions
    of weight mw. g is descending-coeff; product degree < N so no wrap."""
    rng = np.random.default_rng(seed)
    ga = g[::-1]  # ascending for multiplication
    max_q_degree = N - len(g)
    best = None
    for _ in range(n_samples):
        pos = tuple(sorted(rng.choice(max_q_degree + 1, size=mw, replace=False)))
        q = np.zeros(max_q_degree + 1, dtype=np.int8)
        q[list(pos)] = 1
        prod = poly_mul_mod2(ga, q)
        w = int(prod.sum())
        if best is None or w < best:
            best = w
        if best <= 8:
            break
    return best


for N, degs in CANDIDATES.items():
    factors = factor_polynomial(N)
    avail = sorted(set(len(g) - 1 for g in factors))
    print(f"N={N}: n={2*N}, available factor degrees={avail}")
    for deg in degs:
        g = None
        for fac in factors:
            if len(fac) - 1 == deg:
                g = fac
                break
        if g is None:
            print(f"   deg {deg} (k={2*deg}): NOT AVAILABLE")
            continue
        # sample multiplier weight 2 and 3
        best2 = sample_multiple_weight(g, N, 2, n_samples=20000, seed=deg)
        best3 = sample_multiple_weight(g, N, 3, n_samples=20000, seed=deg + 100)
        print(f"   deg {deg} (k={2*deg}): min product weight mw=2 -> {best2}, mw=3 -> {best3}")
