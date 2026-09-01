#!/usr/bin/env python
"""L=4 decisive tests, all 2^15 configs:

T1: weight-1 exactness — "no weight-1 logical (exact rank test)" equals
    "every vertex covered by >=1 active opposite-type anchor"?
    (even-weight argument predicts yes, exactly)
T2: does the chain mechanism fire? i.e. exists config with a pair {p,q}
    having zero opposite-syndrome, {p,q} in rowspace(Hself) via chains
    (no own active w2), which the pair clause would forbid.
    (predicts the pair clauses are spurious -> UNSAT lines unsound)
"""
import sys

import numpy as np

sys.path.insert(0, "research/local2d")
from chamfer4 import gf2_rank, rows  # noqa: E402
from sat_d3 import encode  # noqa: E402

L = 4
n, anchors, var, clauses = encode(L)
N = len(anchors)
sup = {key: s for key, s, _ in anchors}
isx = {key: b for key, _, b in anchors}
xw2 = {frozenset(sup[k]): k for k, s, b in anchors if b and len(s) == 2}
zw2 = {frozenset(sup[k]): k for k, s, b in anchors if not b and len(s) == 2}

t1_bad = 0
t1_rank_fail = 0
t2_hits = 0
t2_examples = []
for mask in range(2**N):
    act = [anchors[i] for i in range(N) if mask >> i & 1]
    active = {a[0] for a in act}
    HX = rows([sup[k] for k, _, b in act if b], n)
    HZ = rows([sup[k] for k, _, b in act if not b], n)

    # T1 per side
    for Hself, Hopp, opp_isx in ((HX, HZ, False), (HZ, HX, True)):
        S = (Hopp % 2).T
        zero = b"\x00" * Hopp.shape[0]
        r_self = gf2_rank(Hself)
        for q in range(n):
            e = np.zeros((1, n), dtype=int)
            e[0, q] = 1
            in_rows = gf2_rank(np.vstack([Hself, e])) == r_self
            if not in_rows:
                t1_rank_fail += 1
            zero_synd = S[q].tobytes() == zero
            logical = zero_synd and not in_rows
            covered = any(k in active for k, s, b in act
                          if b == opp_isx and q in sup[k])
            if logical == (not covered):
                pass
            else:
                t1_bad += 1

    # T2: pair {p,q}, zero Z-syndrome, in rowspace(HX), no own active X-w2
    SZ = (HZ % 2).T
    zeroZ = b"\x00" * HZ.shape[0]
    rX = gf2_rank(HX)
    for p in range(n):
        for q in range(p + 1, n):
            if SZ[p].tobytes() != zeroZ or SZ[q].tobytes() != zeroZ:
                continue
            e = np.zeros((1, n), dtype=int)
            e[0, p] = e[0, q] = 1
            if gf2_rank(np.vstack([HX, e])) != rX:
                continue  # in rowspace -> stabilizer, clause irrelevant?
            continue
            # (unreachable; kept for clarity)
    # proper T2: zero syndrome on BOTH single qubits is not required;
    # the pair has zero syndrome iff no Z-anchor meets exactly one.
    for p in range(n):
        for q in range(p + 1, n):
            D = [k for k, s, b in act if not b
                 and len(frozenset(sup[k]) & {p, q}) == 1]
            if D:
                continue
            e = np.zeros((1, n), dtype=int)
            e[0, p] = e[0, q] = 1
            if gf2_rank(np.vstack([HX, e])) == rX:
                own = xw2.get(frozenset((p, q)))
                if own is None or own not in active:
                    t2_hits += 1
                    if len(t2_examples) < 3:
                        t2_examples.append((mask, p, q, sorted(active)))

print(f"T1: equivalence violations={t1_bad}, "
      f"weight-1-in-rowspace occurrences={t1_rank_fail}")
print(f"T2: chain-stabilized zero-syndrome pairs forbidden by "
      f"pair clauses: {t2_hits}")
for ex in t2_examples:
    print("  example mask/p/q:", ex[0], ex[1], ex[2])
