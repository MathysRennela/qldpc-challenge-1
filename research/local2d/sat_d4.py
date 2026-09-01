#!/usr/bin/env python
"""Exact d>=4 SAT encoder for the orthogonal anchor grid, with lazy triple
clauses (CEGIS). Target question: does a clean d>=4 config with k>=52 exist
on the 26x26 board grid (the chamfer k=51 wall)?

Exactness: weight-1 coverage + weight-2 pair clauses (as sat_d3, exact) +
weight-3 triple clauses. Any odd-weight vector is never in rowspace (all
anchors have even weight), so a triple is a logical iff its opposite-
syndrome is zero; the clause "some opposite anchor meets T oddly and is
active" is therefore exact (sound + complete). Lazy CEGIS: enumerate
zero-syndrome triples via syndrome-group XOR (exhaustive, early-exit only
after >=1 found so the clean verdict stays exact), add clauses, re-solve.
"""
import json
import sys
import time

import numpy as np
from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool
from pysat.solvers import Cadical153

sys.path.insert(0, "research/local2d")
from chamfer4 import gf2_rank, rows  # noqa: E402

TRIPLE_CAP = 400


def build_anchors():
    d = json.load(open("codes/676-110-3.json"))
    n = d["n"]
    coords = [tuple(c) for c in d["locality"]["coordinates"]]
    c2i = {c: i for i, c in enumerate(coords)}
    L = int(max(max(c) for c in coords)) + 1
    faces = {}
    for i in range(L - 1):
        for j in range(L - 1):
            faces[(i, j)] = frozenset((c2i[(i, j)], c2i[(i + 1, j)],
                                       c2i[(i, j + 1)], c2i[(i + 1, j + 1)]))
    bx = [c for c in d["checks"]["X"] if len(c) == 2]
    bz = [c for c in d["checks"]["Z"] if len(c) == 2]
    anchors = []
    for p, fs in sorted(faces.items()):
        anchors.append((p, fs, (p[0] + p[1]) % 2 == 0))
    for i, s in enumerate(bx):
        anchors.append((f"bx{i}", frozenset(s), True))
    for i, s in enumerate(bz):
        anchors.append((f"bz{i}", frozenset(s), False))
    return n, anchors


def encode_base(n, anchors):
    pool = IDPool()
    var = {}
    for key, sup, isx in anchors:
        var[(key, isx)] = pool.id((key, isx))
    XA = [a for a in anchors if a[2]]
    ZA = [a for a in anchors if not a[2]]
    clauses = []
    cover = {q: ([], []) for q in range(n)}
    for key, sup, isx in anchors:
        for q in sup:
            cover[q][0 if isx else 1].append((key, isx))
    for q in range(n):
        for lst in cover[q]:
            clauses.append([var[(k, b)] for k, b in lst] if lst else [])
    xw2 = {frozenset(sup): var[(key, True)] for key, sup, isx in anchors
           if isx and len(sup) == 2}
    zw2 = {frozenset(sup): var[(key, False)] for key, sup, isx in anchors
           if not isx and len(sup) == 2}

    def pair_clause(p, q, opp, own_w2):
        D = [var[(key, isx)] for key, sup, isx in opp
             if len(sup & {p, q}) == 1]
        w2v = own_w2.get(frozenset((p, q)))
        if w2v is not None:
            clauses.append([w2v] + [v for v in D])
        elif D:
            clauses.append([v for v in D])
        else:
            clauses.append([])

    for p in range(n):
        for q in range(p + 1, n):
            pair_clause(p, q, ZA, xw2)
            pair_clause(p, q, XA, zw2)
    return pool, var, clauses


def syndromes(active, anchors, n, side_isx):
    """Syndrome of each qubit under active opposite-type anchors, packed
    as ints. Returns (synd_int list, active opposite anchor count)."""
    sup = {key: s for key, s, _ in anchors}
    opp = [(key, sup[key]) for key, s, b in anchors
           if b != side_isx and key in active]
    m = len(opp)
    S = np.zeros((n, m), dtype=np.uint8)
    for j, (key, s) in enumerate(opp):
        for q in s:
            S[q, j] = 1
    packed = np.packbits(S, axis=1)
    ints = [int.from_bytes(row.tobytes(), "big") for row in packed]
    return ints, m


def find_zero_syndrome_triples(ints, cap):
    """Exhaustive up to cap: triples a<b<c with ints[a]^ints[b]^ints[c]==0.
    Early exit AFTER cap found (0 found is exact)."""
    groups = {}
    for q, s in enumerate(ints):
        groups.setdefault(s, []).append(q)
    gkeys = sorted(groups)
    found = []
    for i, ga in enumerate(gkeys):
        for gb in gkeys[i:]:
            gc = ga ^ gb
            if gc not in groups:
                continue
            gl_a, gl_b, gl_c = groups[ga], groups[gb], groups[gc]
            if ga == gb:
                for x in range(len(gl_a)):
                    a = gl_a[x]
                    for y in range(x + 1, len(gl_a)):
                        b = gl_a[y]
                        for c in gl_c:
                            if c > b:
                                found.append((a, b, c))
                                if len(found) >= cap:
                                    return found
            else:
                for a in gl_a:
                    for b in gl_b:
                        lo, hi = (a, b) if a < b else (b, a)
                        for c in gl_c:
                            if c > hi:
                                found.append((lo, hi, c))
                                if len(found) >= cap:
                                    return found
    return found


def triple_lits(T, anchors, var, side_isx):
    T = set(T)
    return [var[(key, isx)] for key, sup, isx in anchors
            if isx == side_isx and len(sup & T) % 2 == 1]


def main():
    t0 = time.time()
    n, anchors = build_anchors()
    N = len(anchors)
    # warm-start cardinality: the k=51 config's anchor count
    doc = json.load(open("research/candidates/676-51-4-chamfer.json"))
    coords = [tuple(c) for c in doc["locality"]["coordinates"]]
    c2i = {c: i for i, c in enumerate(coords)}
    L = int(max(max(c) for c in coords)) + 1
    faces = {}
    for i in range(L - 1):
        for j in range(L - 1):
            faces[(i, j)] = frozenset((c2i[(i, j)], c2i[(i + 1, j)],
                                       c2i[(i, j + 1)], c2i[(i + 1, j + 1)]))
    xs = {frozenset(np.nonzero(r)[0])
          for r in rows(doc["checks"]["X"], doc["n"])}
    zs = {frozenset(np.nonzero(r)[0])
          for r in rows(doc["checks"]["Z"], doc["n"])}
    holes51 = {p for p, fs in faces.items() if fs not in xs and fs not in zs}
    A0 = N - len(holes51)
    hole_vars51 = []
    print(f"n={n}, {N} anchors; k=51 config: {len(holes51)} holes -> "
          f"A0={A0}", flush=True)

    pool, var, base_clauses = encode_base(n, anchors)
    var2key = {v: k for k, v in var.items()}
    allv = list(var.values())
    hole_vars51 = [(p, (p[0] + p[1]) % 2 == 0) for p in holes51
                   if ((p, (p[0] + p[1]) % 2 == 0)) in var]
    print(f"base clauses: {len(base_clauses)}; warm-start holes: "
          f"{len(hole_vars51)}", flush=True)

    summary = []
    for card in range(A0, A0 - 9, -1):
        cnf = CNF()
        cnf.extend(base_clauses)
        cnf.extend(CardEnc.atmost(lits=allv, bound=card,
                                  top_id=pool.top + n + 10,
                                  encoding=EncType.seqcounter).clauses)
        best_k = -1
        it = 0
        dead = False
        solver = Cadical153(bootstrap_with=cnf)
        # warm start: assume the known k=51 config's holes inactive on the
        # first solve — guaranteed clean find, seeds CaDiCaL's learning
        warm = [-var[(key, isx)] for key, isx in hole_vars51]
        while time.time() < t0 + 3600 * 5:
            it += 1
            if not solver.solve(assumptions=warm if it == 1 else []):
                print(f"  A={card}: exhausted ({it-1} models blocked, "
                      f"{time.time()-t0:.0f}s)", flush=True)
                break
            m = solver.get_model()
            active = {var2key[v][0] for v in m if v > 0 and v in var2key}
            sup = {key: s_ for key, s_, _ in anchors}
            isx = {key: b for key, _, b in anchors}
            HX = rows([sup[k] for k in active if isx[k]], n)
            HZ = rows([sup[k] for k in active if not isx[k]], n)
            k = n - gf2_rank(HX) - gf2_rank(HZ)
            block = [-v for v in m if v > 0 and v in var2key]
            clause_pool = []
            unconditional = False
            clean = True
            for side_isx in (True, False):
                ints, _ = syndromes(active, anchors, n, side_isx)
                found = find_zero_syndrome_triples(ints, TRIPLE_CAP)
                if found:
                    clean = False
                for T in found:
                    lits = triple_lits(T, anchors, var, side_isx)
                    if lits:
                        clause_pool.append(lits)
                    else:
                        # no anchor structurally meets T oddly: T is a
                        # weight-3 logical in EVERY config of this grid
                        unconditional = True
                        break
                if unconditional:
                    break
            if clean:
                print(f"  A={card}: CLEAN d>=4 config k={k} (iter {it}, "
                      f"{time.time()-t0:.0f}s)", flush=True)
                if k > best_k:
                    best_k = k
                solver.add_clause(block)
                continue
            if unconditional:
                print(f"  A={card}: unconditional weight-3 logical found "
                      f"-> branch dead ({time.time()-t0:.0f}s)", flush=True)
                dead = True
                break
            added = 0
            for lits in clause_pool:
                solver.add_clause(lits)
                added += 1
                if added >= TRIPLE_CAP:
                    break
            if it % 10 == 0:
                print(f"  A={card}: iter {it}, k={k}, "
                      f"{len(clause_pool)} triple clauses this round "
                      f"({time.time()-t0:.0f}s)", flush=True)
        if best_k >= 0:
            summary.append((card, best_k))
        if dead:
            break
        if time.time() >= t0 + 3600 * 5:
            print("TIME BUDGET HIT", flush=True)
            break
    print("SUMMARY:", summary, flush=True)


if __name__ == "__main__":
    main()
