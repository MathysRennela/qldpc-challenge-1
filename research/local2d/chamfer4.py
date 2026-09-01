#!/usr/bin/env python
"""Chamfer-d=4 derivation: holey rotated surface code with exact d>=4.

Base: codes/676-110-3.json = rotated surface code on 26x26 vertices
(weight-4 interior plaquettes, alternating weight-2 boundary checks) with 109
single-plaquette holes: k = 110, d = 3. d >= 4 iff no nontrivial logical of
weight <= 3 exists on either side. Weight-<=3 elements of ker(Hopp) are
enumerated EXHAUSTIVELY via syndrome pairing (numpy-vectorized); each
candidate is tested against rowspace(Hself). A non-member is a logical.

Loop: greedily delete holes adjacent to found short logicals until both sides
are clean (exact d >= 4), then greedily re-add holes (keeping cleanliness) to
maximize k. g = k * 16 / 676 at d = 4.
"""
import json
import sys

import numpy as np

sys.path.insert(0, "research/kit")


def rows(chks, n):
    H = np.zeros((len(chks), n), dtype=np.uint8)
    for i, c in enumerate(chks):
        for q in c:
            H[i, q] = 1
    return H


def gf2_rank(A):
    A = (A % 2).copy().astype(np.uint8)
    m_, c = A.shape
    r = 0
    for col in range(c):
        piv = np.nonzero(A[r:, col])[0]
        if len(piv) == 0:
            continue
        piv = piv[0] + r
        A[[r, piv]] = A[[piv, r]]
        for rr in range(m_):
            if rr != r and A[rr, col]:
                A[rr] ^= A[r]
        r += 1
        if r == m_:
            break
    return r


def rref_basis(H):
    A = H.copy() % 2
    m_, n = A.shape
    r = 0
    pivots = []
    for col in range(n):
        piv = np.nonzero(A[r:, col])[0]
        if len(piv) == 0:
            continue
        piv = piv[0] + r
        A[[r, piv]] = A[[piv, r]]
        for rr in range(m_):
            if rr != r and A[rr, col]:
                A[rr] ^= A[r]
        pivots.append(col)
        r += 1
        if r == m_:
            break
    return pivots, A[:r]


def short_logicals(Hself, Hopp, cap=None):
    """All weight<=3 elements of ker(Hopp) not in rowspace(Hself).
    If cap is set, stop early once that many are found (dirty-config speed)."""
    m_, n = Hself.shape
    S = np.ascontiguousarray((Hopp % 2).T)          # n x m_ syndrome matrix
    synd = [S[a].tobytes() for a in range(n)]
    zero = b"\x00" * Hopp.shape[0]   # syndrome length = Hopp rows!
    piv, basis = rref_basis(Hself)
    B = basis
    P = piv

    def is_logical(support):
        w = np.zeros(n, dtype=np.uint8)
        w[list(support)] = 1
        for row, p in zip(B, P):
            if w[p]:
                w ^= row
        return w.any()

    syn_lists = {}
    for a in range(n):
        syn_lists.setdefault(synd[a], []).append(a)

    found = []
    full = cap is None

    def done():
        return not full and len(found) >= cap

    for a in range(n):                                   # weight 1
        if synd[a] == zero and is_logical((a,)):
            found.append((a,))
            if done():
                return found
    for a in range(n):                                   # weight 2
        if done():
            return found
        for b in syn_lists.get(synd[a], ()):
            if b > a and is_logical((a, b)):
                found.append((a, b))
                if done():
                    return found
    pair_syn = {}                                        # weight 3
    Sa = S  # S[a] ^ S[b] via numpy rows
    for a in range(n):
        row_a = Sa[a]
        for b in range(a + 1, n):
            s = (row_a ^ Sa[b]).tobytes()
            pair_syn.setdefault(s, []).append((a, b))
    for s, pairs in pair_syn.items():
        if done():
            return found
        cs = syn_lists.get(s)
        if not cs:
            continue
        for a, b in pairs:
            for c in cs:
                if c > b and is_logical((a, b, c)):
                    found.append((a, b, c))
                    if done():
                        return found
    return found


def main():
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
    HXb = rows(d["checks"]["X"], n)
    HZb = rows(d["checks"]["Z"], n)
    xsets = {frozenset(np.nonzero(r)[0]) for r in HXb}
    zsets = {frozenset(np.nonzero(r)[0]) for r in HZb}
    holes = {pos for pos, fs in faces.items()
             if fs not in xsets and fs not in zsets}
    # fixed boundary weight-2 checks (from the board code)
    bx = [c for c in d["checks"]["X"] if len(c) == 2]
    bz = [c for c in d["checks"]["Z"] if len(c) == 2]
    print(f"base: n={n} L={L} holes={len(holes)} k={d['k']} "
          f"d={d['distance']['d']} boundary w2: X={len(bx)} Z={len(bz)}",
          flush=True)

    def build_H(holeset):
        Xl, Zl = [], []
        for (i, j), fs in faces.items():
            if (i, j) in holeset:
                continue
            (Xl if (i + j) % 2 == 0 else Zl).append(sorted(fs))
        return (rows(Xl + bx, n), rows(Zl + bz, n))

    def evaluate(holeset):
        HX, HZ = build_H(holeset)
        k = n - gf2_rank(HX) - gf2_rank(HZ)
        lx = short_logicals(HX, HZ)
        lz = short_logicals(HZ, HX)
        return HX, HZ, k, lx, lz

    # sanity: reproduce base
    HX, HZ, k, lx, lz = evaluate(holes)
    print(f"base rebuilt: k={k} (expect {d['k']}), shortX={len(lx)} "
          f"shortZ={len(lz)}", flush=True)

    def qubit_to_holes(q, holeset):
        return [p for p in holeset if q in faces[p]]

    holes = set(holes)
    for it in range(300):
        HX, HZ, k, lx, lz = evaluate(holes)
        if not lx and not lz:
            print(f"iter {it}: CLEAN d>=4 exact, k={k}, holes={len(holes)}",
                  flush=True)
            break
        support = (lx or lz)[0]
        cand = set()
        for q in support:
            cand.update(qubit_to_holes(q, holes))
        if not cand:
            q = support[0]
            cq = coords[q]
            cand = {min(holes, key=lambda p: (p[0] + 0.5 - cq[0]) ** 2
                        + (p[1] + 0.5 - cq[1]) ** 2)}
        victim = sorted(cand)[0]
        holes.discard(victim)
        if it % 5 == 0:
            print(f"  iter {it}: k={k} shortX={len(lx)} shortZ={len(lz)} "
                  f"removed {victim}", flush=True)
    else:
        print("deletion did not converge", flush=True)
        return

    # greedy re-add
    print(f"after deletion: k={k} holes={len(holes)}", flush=True)
    improved = True
    while improved:
        improved = False
        for pos in sorted(set(faces) - holes):
            trial = holes | {pos}
            HX, HZ, k2, lx, lz = evaluate(trial)
            if not lx and not lz and k2 > k:
                holes = trial
                k = k2
                improved = True
                print(f"  re-added {pos}: k={k}", flush=True)
                break
    HX, HZ, k, lx, lz = evaluate(holes)
    g = k * 16 / n
    print(f"FINAL: holes={len(holes)} k={k} d>=4 exact g={g:.4f}", flush=True)
    np.savez("/tmp/chamfer4.npz", hx=HX, hz=HZ,
             coords=np.array(coords, dtype=float),
             holes=np.array(sorted(holes)))
    print("saved /tmp/chamfer4.npz", flush=True)


if __name__ == "__main__":
    main()
