#!/usr/bin/env python
"""Exact d>=4 maps at small L: full triple-clause materialization.

At L <= 12 the triple set C(n,3) is small enough to materialize the ENTIRE
exact d>=4 CNF upfront (no laziness): weight-1 coverage + weight-2 pairs +
all weight-3 triple clauses + cardinality. UNSAT is then fully authoritative.
Sweeps cardinality downward, recording max exact k among clean configs.
"""
import sys
import time

from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool
from pysat.solvers import Cadical153

sys.path.insert(0, "research/local2d")
from sat_map_ortho import build_grid  # noqa: E402
from chamfer4 import gf2_rank, rows  # noqa: E402


def main():
    t0 = time.time()
    for L in (6, 8, 10, 12):
        n, faces, w2 = build_grid(L)
        anchors = []
        for p, fs in sorted(faces.items()):
            anchors.append((p, frozenset(fs), (p[0] + p[1]) % 2 == 0))
        for i, (s, isx) in enumerate(w2):
            anchors.append((f"w{i}", frozenset(s), isx))
        pool = IDPool()
        var = {}
        for key, sup, isx in anchors:
            var[(key, isx)] = pool.id((key, isx))
        XA = [a for a in anchors if a[2]]
        ZA = [a for a in anchors if not a[2]]
        clauses = []

        # weight-1 coverage
        cover = {q: ([], []) for q in range(n)}
        for key, sup, isx in anchors:
            for q in sup:
                cover[q][0 if isx else 1].append((key, isx))
        for q in range(n):
            for lst in cover[q]:
                clauses.append([var[(k, b)] for k, b in lst] if lst else [])

        # weight-2 pairs
        xw2 = {frozenset(sup): var[(key, True)] for key, sup, isx in anchors
               if isx and len(sup) == 2}
        zw2 = {frozenset(sup): var[(key, False)] for key, sup, isx in anchors
               if not isx and len(sup) == 2}
        for p in range(n):
            for q in range(p + 1, n):
                for opp, own in ((ZA, xw2), (XA, zw2)):
                    D = [var[(key, isx)] for key, sup, isx in opp
                         if len(sup & {p, q}) == 1]
                    w2v = own.get(frozenset((p, q)))
                    if w2v is not None:
                        clauses.append([w2v] + [v for v in D])
                    elif D:
                        clauses.append([v for v in D])
                    else:
                        clauses.append([])

        # weight-3 triples: every triple needs an odd-meeting opposite anchor
        n_triples = 0
        dead = False
        for p in range(n):
            for q in range(p + 1, n):
                for r in range(q + 1, n):
                    T = {p, q, r}
                    for opp in (ZA, XA):
                        lits = [var[(key, isx)] for key, sup, isx in opp
                                if len(sup & T) % 2 == 1]
                        if lits:
                            clauses.append(lits)
                            n_triples += 1
                        else:
                            dead = True  # unconditional weight-3 logical
                if dead:
                    break
            if dead:
                break
        if dead:
            print(f"L={L}: unconditional weight-3 logical -> no d>=4 code "
                  f"exists on this grid", flush=True)
            continue

        var2key = {v: k for k, v in var.items()}
        allv = list(var.values())
        sup = {key: s for key, s, _ in anchors}
        isx = {key: b for key, _, b in anchors}
        print(f"L={L}: n={n}, {len(anchors)} anchors, {len(clauses)} clauses "
              f"({n_triples} triple clauses) [{time.time()-t0:.0f}s]",
              flush=True)
        best = (-1, None)
        for card in range(len(anchors), 0, -1):
            cnf = CNF()
            cnf.extend(clauses)
            cnf.extend(CardEnc.atmost(lits=allv, bound=card,
                                      top_id=pool.top + n + 10,
                                      encoding=EncType.seqcounter).clauses)
            s = Cadical153(bootstrap_with=cnf)
            if not s.solve():
                print(f"  L={L}: UNSAT at A<={card} -> frontier closed "
                      f"({time.time()-t0:.0f}s)", flush=True)
                break
            m = s.get_model()
            active = {var2key[v][0] for v in m if v > 0 and v in var2key}
            HX = rows([sup[k] for k in active if isx[k]], n)
            HZ = rows([sup[k] for k in active if not isx[k]], n)
            k = n - gf2_rank(HX) - gf2_rank(HZ)
            if k > best[0]:
                best = (k, sorted(active, key=str))
                print(f"  A<={card}: clean d>=4 k={k} "
                      f"({time.time()-t0:.0f}s)", flush=True)
        if best[0] >= 0:
            g = best[0] * 9 / n
            print(f"  L={L} FINAL: max k={best[0]}, g(d>=4)={g:.4f}",
                  flush=True)
    print("ALL DONE", flush=True)


if __name__ == "__main__":
    main()
