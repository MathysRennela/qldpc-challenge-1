#!/usr/bin/env python
"""Overnight: blocked SAT enumeration near the exact d>=3 frontier.

For each L, sweep cardinality A downward from the all-anchor count, enumerate
solutions with blocking (exact CNF: weight-1 coverage + weight-2 pairs), and
record the max exact k and the best config. The CNF is exact (validated at
L=4 exhaustively + 11 annealer cross-checks), so every solution passes
d >= 3; k is still recomputed exactly via GF(2) rank.
"""
import json
import sys
import time

from pysat.card import CardEnc, EncType
from pysat.formula import CNF
from pysat.solvers import Cadical153

sys.path.insert(0, "research/local2d")
from sat_d3 import encode, exact_eval  # noqa: E402

OUT = "research/candidates/overnight-chamfer4"
SAMPLES = 2000


def main():
    L = int(sys.argv[1])
    t0 = time.time()
    n, anchors, var, clauses = encode(L)
    allv = [var[(key, isx)] for key, _, isx in anchors]
    var2key = {vv: kk for (kk, ii), vv in var.items()}
    print(f"L={L}: n={n}, {len(anchors)} anchors", flush=True)
    best = None
    for A in range(len(anchors), max(len(anchors) - 30, 0), -1):
        cnf = CNF()
        cnf.extend(clauses)
        card = CardEnc.atmost(lits=allv, bound=A,
                              top_id=len(var) + len(allv) + n,
                              encoding=EncType.seqcounter)
        cnf.extend(card.clauses)
        s = Cadical153(bootstrap_with=cnf)
        found, kmax = 0, -1
        while s.solve() and found < SAMPLES:
            m = s.get_model()
            active = {var2key[v] for v in m if v > 0 and v in var2key}
            k, clean = exact_eval(active, anchors, n)
            if clean:
                found += 1
                if k > kmax:
                    kmax = k
                if best is None or k > best[0]:
                    best = (k, A, sorted(active, key=str))
                    with open(f"{OUT}/d3-L{L}-enum-best.json", "w") as f:
                        json.dump({"L": L, "n": n, "k": k, "A": A,
                                   "active": best[2],
                                   "verification": "exact CNF + GF2 rank + "
                                                   "d3_clean"},
                                  f, indent=1)
                    print(f"  NEW BEST k={k} at A={A}", flush=True)
            s.add_clause([-v for v in m if v > 0 and v in var2key])
        print(f"A={A}: clean={found}, kmax={kmax} "
              f"({time.time()-t0:.0f}s)", flush=True)
        if found == 0:
            break
    print(f"FINAL L={L}: best k={best[0] if best else '-'}", flush=True)


if __name__ == "__main__":
    main()
