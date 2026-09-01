#!/usr/bin/env python
"""d=3 SAT campaign, milestone 2: exact CNF encoder + cardinality sweep.

Variables: one boolean per anchor (faces + boundary w2 checks), True = check
present. CSS commutation is automatic (checkerboard types). d >= 3 is encoded
EXACTLY and polynomially:

  weight-1 X-logical at q  <=>  all Z-anchors containing q inactive
     (weight-1 vectors are never in rowspace(HX): no weight-1 checks exist
      and w2 products have weight >= 4)
  weight-2 X-logical {p,q} <=>  all Z-anchors meeting exactly one of {p,q}
     inactive, AND {p,q} not in rowspace(HX)
     (weight-2 rowspace elements are exactly single active X-w2 checks)

So per vertex: clause = OR(Z-anchors containing q).
Per pair {p,q}: if {p,q} is an X-w2 support: clause = (that w2) OR (OR D);
otherwise clause = OR(D), where D = Z-anchors meeting exactly one of {p,q}.
Symmetrically for Z-logicals with X-anchors. Symmetric clauses are
tautologies when D is empty and are skipped.

k is NOT encoded; solutions are post-verified exactly (GF2 rank + the same
d>=3 test) and k recorded. Cardinality constraint: at most A active anchors;
A is swept downward to map the frontier. Validated against the exhaustive
L=4 map ({1:15, 2:14, 3:13}).
"""
import json
import sys
import time

import numpy as np
from pysat.formula import IDPool
from pysat.solvers import Cadical153

sys.path.insert(0, "research/local2d")
from chamfer4 import gf2_rank, rows  # noqa: E402
from sat_map_ortho import build_grid, d3_clean  # noqa: E402


def encode(L):
    n, faces, w2 = build_grid(L)
    pool = IDPool()
    var = {}

    def v(key, isx):
        return var.setdefault((key, isx), pool.id((key, isx)))

    anchors = []  # (key, support, isx)
    for p, fs in sorted(faces.items()):
        anchors.append((p, sorted(fs), (p[0] + p[1]) % 2 == 0))
    for i, (s, isx) in enumerate(w2):
        anchors.append((f"w{i}", s, isx))

    for key, sup, isx in anchors:
        v(key, isx)

    clauses = []

    def add_x_anchors():
        return [a for a in anchors if a[2]]

    def add_z_anchors():
        return [a for a in anchors if not a[2]]

    XA, ZA = add_x_anchors(), add_z_anchors()

    # weight-1: EXACT by the even-weight argument — all anchors have even
    # weight (faces 4, w2 2), so rowspace(H) contains no weight-1 vector;
    # a weight-1 logical at q exists iff no active opposite-type anchor
    # covers q. Verified equivalent to the exact rank test over all 2^15
    # L=4 configs (d3_design_check2.py, T1: 0 violations).
    cover = {q: ([], []) for q in range(n)}   # q -> (x_anchors, z_anchors)
    for key, sup_, isx_ in anchors:
        for q in sup_:
            cover[q][0 if isx_ else 1].append((key, isx_))
    for q, (xa, za) in cover.items():
        if xa:
            clauses.append([v(k, b) for k, b in xa])
        else:
            clauses.append([])   # uncovered vertex: unconditional logical
        if za:
            clauses.append([v(k, b) for k, b in za])
        else:
            clauses.append([])

    # weight-2
    xw2_supports = {frozenset(sup): key for key, sup, isx in anchors
                    if isx and len(sup) == 2}
    zw2_supports = {frozenset(sup): key for key, sup, isx in anchors
                    if not isx and len(sup) == 2}

    def pair_clauses(p, q, opp, own_w2):
        """Forbid weight-2 logical {p,q} on the side checked by `opp`
        anchors (opp = Z-anchors when forbidding X-logicals)."""
        D = [key for key, sup, isx in opp
             if len(frozenset(sup) & {p, q}) == 1]
        w2key = own_w2.get(frozenset((p, q)))
        if w2key is not None:
            # {p,q} is a stabilizer iff this w2 is active; otherwise every
            # Z-anchor meeting exactly one must be active
            clauses.append([v(w2key, True)] + [v(k, False) for k in D])
        elif D:
            clauses.append([v(k, False) for k in D])
        else:
            clauses.append([])   # unconditionally a logical: UNSAT

    for p, q in itertools_pairs(n):
        pair_clauses(p, q, ZA, xw2_supports)
        pair_clauses(p, q, XA, zw2_supports)
    return n, anchors, var, clauses


def itertools_pairs(n):
    for p in range(n):
        for q in range(p + 1, n):
            yield p, q


def exact_eval(active_keys, anchors, n):
    sup = {key: s for key, s, _ in anchors}
    isx = {key: b for key, _, b in anchors}
    HX = rows([sup[k] for k in active_keys if isx[k]], n)
    HZ = rows([sup[k] for k in active_keys if not isx[k]], n)
    k = n - gf2_rank(HX) - gf2_rank(HZ)
    return k, d3_clean(HX, HZ)


def main():
    L = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    n, anchors, var, clauses = encode(L)
    print(f"L={L}: n={n}, {len(anchors)} anchors, {len(clauses)} clauses",
          flush=True)
    allv = [var[(key, isx)] for key, _, isx in anchors]
    key_of = {var[(key, isx)]: key for key, _, isx in anchors}
    best = {}
    t0 = time.time()
    for A in range(len(anchors), 0, -1):
        # at most A active: sequential counter (simple pairwise for small A
        # ranges is expensive; use pysat CardEnc)
        from pysat.card import CardEnc, EncType
        from pysat.formula import CNF
        cnf_obj = CNF()
        cnf_obj.extend(clauses)
        card = CardEnc.atmost(lits=allv, bound=A, top_id=len(var) + len(allv) + n,
                              encoding=EncType.seqcounter)
        cnf_obj.extend(card.clauses)
        cnf = cnf_obj.clauses
        s = Cadical153(bootstrap_with=cnf)
        sat_count = 0
        best_kA = 0
        while s.solve() and sat_count < 30 and time.time() - t0 < 3600:
            model = s.get_model()
            act = [key_of[l] for l in model if l > 0 and l in key_of]
            k, clean = exact_eval(act, anchors, n)
            sat_count += 1
            if clean and k > best_kA:
                best_kA = k
            if clean and (k not in best or A < best[k]):
                best[k] = A
                print(f"  k={k} with {A} anchors (A={A})", flush=True)
            # block this model
            s.add_clause([-l for l in model if l > 0 and l in key_of])
        print(f"A={A}: {'SAT' if sat_count else 'UNSAT'} "
              f"({sat_count} samples, best k={best_kA}) "
              f"{time.time()-t0:.0f}s", flush=True)
        if not sat_count:
            print(f"UNSAT at A={A} -> frontier mapped; best={best}", flush=True)
            break
    print(f"FRONTIER L={L}: {dict(sorted(best.items()))}", flush=True)
    with open(f"/tmp/sat_frontier_L{L}.json", "w") as f:
        json.dump({"L": L, "n": n, "frontier_k_to_min_anchors": best}, f)


if __name__ == "__main__":
    main()
