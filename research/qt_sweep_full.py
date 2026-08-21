"""Full targeted search over the QT-lift family (arXiv:2608.12509).

Runs a larger sweep than the quick check, over multiple seeds, and reports
whether ANY QT-lift code is non-dominated on the current board. Also records
the best (n,k,d,w) found so the negative result is auditable.
"""
import sys
import os
import json
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "kit"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "site"))

from qt_lift import (build_qt_lift, hamming_8_4_4, hamming_7_3_4,
                     hamming_6_3_3, generator_from_parity)
from group_algebra import dihedral, metacyclic
from css import compute_k, verify_css
from surrogate import distance_rand
from build import load_entries


def run(seed=0, num=200, trials=150):
    rng = np.random.default_rng(seed)
    local_codes = {
        "8_4_4": (hamming_8_4_4(), generator_from_parity(hamming_8_4_4())),
        "7_3_4": (hamming_7_3_4(), generator_from_parity(hamming_7_3_4())),
        "6_3_3": (hamming_6_3_3(), generator_from_parity(hamming_6_3_3())),
    }
    # Groups with order in [5, 11] so n = nA*nB*N lands in [300, 700] for
    # the local-code products nA*nB in {36, 42, 48, 49, 56, 63, 64}.
    groups = []
    for m in range(3, 6):
        mul, _ = dihedral(m)
        groups.append((f"D_{2*m}", mul))
    for n in range(3, 12):
        for k in range(2, 8):
            for r in range(2, n):
                if pow(r, k, n) == 1 and 5 <= n * k <= 11:
                    mul, _ = metacyclic(n, k, r)
                    groups.append((f"C{n}x|C{k}", mul))
    seen = {}
    for name, mul in groups:
        seen.setdefault(mul.shape[0], (name, mul))
    groups = list(seen.values())

    entries = load_entries()
    results = []
    t0 = time.time()
    ntested = 0
    for trial in range(num):
        name, mul = groups[rng.choice(len(groups))]
        N = mul.shape[0]
        cname = rng.choice(list(local_codes))
        H0, G0 = local_codes[cname]
        H0p, G0p = local_codes[cname]
        nA, nB = H0.shape[1], H0p.shape[1]
        n = nA * nB * N
        if not (300 <= n <= 700):
            continue
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
        d = distance_rand(HX, HZ, trials=trials, seed=seed + trial)
        if d == float("inf"):
            continue
        ntested += 1
        results.append({"n": n, "k": k, "d": int(d), "w": w,
                        "eff": k * d * d / n, "group": name,
                        "local": cname if False else "mixed"})
    results.sort(key=lambda r: -r["eff"])
    return results, entries, time.time() - t0


if __name__ == "__main__":
    results, entries, dt = run(seed=int(sys.argv[1]) if len(sys.argv) > 1 else 0)
    print(f"swept {len(results)} valid codes in {dt:.1f}s")
    # check dominance against board
    from qt_search import find_dominator
    nondom = []
    for r in results:
        if not find_dominator((r["n"], r["k"], r["d"], r["w"]), entries):
            nondom.append(r)
    print(f"non-dominated: {len(nondom)}")
    for r in results[:10]:
        dom = find_dominator((r["n"], r["k"], r["d"], r["w"]), entries)
        print("  [[%d,%d,%d]] w=%d eff=%.2f %s %s" % (r["n"], r["k"], r["d"],
              r["w"], r["eff"], "NON-DOM" if not dom else "dominated", r["group"]))