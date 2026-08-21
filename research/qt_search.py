"""Targeted search: can the QT-lift construction (arXiv:2608.12509) advance
the board's frontier?

Strategy:
  1. Reconstruct the paper's own instances (Table 1/3) and check whether any
     is non-dominated on the current board.
  2. Sweep the QT-lift family over groups / local-code combos / supports,
     screening cheaply, and check whether anything beats the frontier.
  3. Validate any survivor with the trusted gate.

The QT codes land in the `unrestricted / any weight` cell (no layout, w > 8).
The frontier there is dominated by high-k generalized-bicycle and
lifted-product codes, so the paper's low-k QT instances are expected to be
dominated. This script confirms that and looks for any non-dominated point.
"""
import sys
import os
import json

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "kit"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "site"))

from qt_lift import (build_qt_lift, hamming_8_4_4, hamming_7_3_4,
                     hamming_6_3_3, generator_from_parity)
from group_algebra import (cyclic_product, dihedral, metacyclic, sym,
                           perm_group, direct_product)
from css import compute_k, verify_css
from surrogate import distance_rand

from build import load_entries, pareto, cells, LOCALITY_LABEL, WEIGHT_LABEL


def board_entries():
    """The board as the site sees it: list of dicts with n,k,d,w."""
    return load_entries()


def is_dominated(cand, entries):
    """True if some board entry dominates cand on (n,k,d,w)."""
    n, k, d, w = cand
    for e in entries:
        if (e["n"] <= n and e["k"] >= k and e["d"] >= d and e["w"] <= w
                and (e["n"] < n or e["k"] > k or e["d"] > d or e["w"] < w)):
            return True
    return False


def find_dominator(cand, entries):
    """Return the board entry that dominates cand, or None."""
    n, k, d, w = cand
    for e in entries:
        if (e["n"] <= n and e["k"] >= k and e["d"] >= d and e["w"] <= w
                and (e["n"] < n or e["k"] > k or e["d"] > d or e["w"] < w)):
            return e
    return None


def check_paper_instances():
    """Reconstruct the paper's Table 3 instances and check dominance."""
    print("=== Paper instances (Table 3) vs board frontier ===")
    entries = board_entries()
    # (name, group_builder, nA, nB, H0, H0p, A, B)
    # We use the paper's reported (n,k,d,w) directly for the dominance check,
    # since we cannot reproduce the exact multisets without the full tables.
    paper = [
        # (name, n, k, d, w)
        ("[[480,8,(<=21,<=21)]]", 480, 8, 21, 12),
        ("[[504,4,(<=36,<=27)]]", 504, 4, 27, 16),
        ("[[672,4,(<=48,<=28)]]", 672, 4, 28, 16),
        ("[[720,6,(<=30,<=30)]]", 720, 6, 30, 9),
        ("[[864,8,(<=39,<=31)]]", 864, 8, 31, 12),
        ("[[864,16,(<=36,<=32)]]", 864, 16, 32, 12),
        ("[[864,8,(<=42,<=40)]]", 864, 8, 40, 12),
        ("[[1120,4,(<=80,<=35)]]", 1120, 4, 35, 16),
    ]
    for name, n, k, d, w in paper:
        dom = find_dominator((n, k, d, w), entries)
        status = "DOMINATED by [[%d,%d,%d]] w=%d" % (dom["n"], dom["k"], dom["d"], dom["w"]) if dom else "NON-DOMINATED"
        print(f"  {name:28s} w={w:2d} eff={k*d*d/n:6.2f}  {status}")


def sweep_qt(seed=0, num=200, trials=300):
    """Sweep the QT-lift family over groups and local-code combos.

    Returns a list of candidate records (n,k,d,w,eff,spec) that are
    non-dominated within the sweep, for later board comparison.
    """
    rng = np.random.default_rng(seed)
    local_codes = {
        "8_4_4": (hamming_8_4_4(), generator_from_parity(hamming_8_4_4())),
        "7_3_4": (hamming_7_3_4(), generator_from_parity(hamming_7_3_4())),
        "6_3_3": (hamming_6_3_3(), generator_from_parity(hamming_6_3_3())),
    }
    # Groups: (name, mul) with order N; n = nA*nB*N must be in [300, 700]
    groups = []
    for m in range(3, 20):
        mul, _ = dihedral(m)          # D_m, order 2m
        groups.append((f"D_{2*m}", mul))
    for n in range(5, 30):
        for k in range(2, 12):
            for r in range(2, n):
                if pow(r, k, n) == 1 and 20 <= n * k <= 60:
                    mul, _ = metacyclic(n, k, r)
                    groups.append((f"C{n}x|C{k}", mul))
    # dedup groups by order
    seen = set()
    uniq = []
    for name, mul in groups:
        if mul.shape[0] not in seen:
            seen.add(mul.shape[0])
            uniq.append((name, mul))
    groups = uniq

    results = []
    for _ in range(num):
        name, mul = groups[rng.choice(len(groups))]
        N = mul.shape[0]
        # pick local codes
        cname = rng.choice(list(local_codes))
        H0, G0 = local_codes[cname]
        H0p, G0p = local_codes[cname]
        nA, nB = H0.shape[1], H0p.shape[1]
        n = nA * nB * N
        if not (300 <= n <= 700):
            continue
        # random supports (with repetition allowed, per Appendix D)
        A = [int(x) for x in rng.choice(N, size=nA, replace=True)]
        B = [int(x) for x in rng.choice(N, size=nB, replace=True)]
        try:
            HX, HZ = build_qt_lift(mul, A, B, H0, G0, H0p, G0p)
        except AssertionError:
            continue
        k = compute_k(HX, HZ)
        if k < 1:
            continue
        w = int(max(max((int(r.sum()) for r in HX), default=0),
                    max((int(r.sum()) for r in HZ), default=0)))
        d = distance_rand(HX, HZ, trials=trials, seed=seed + _)
        if d == float("inf"):
            continue
        results.append({"n": n, "k": k, "d": int(d), "w": w,
                        "eff": k * d * d / n, "spec": {"group": name,
                        "local": cname, "A": A, "B": B}})
    return results


if __name__ == "__main__":
    check_paper_instances()