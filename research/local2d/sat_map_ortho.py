#!/usr/bin/env python
"""d=3 SAT campaign, milestone 1 (corrected lattice): exhaustive maps on the
orthogonal (face-plaquette) convention.

Lattice: data qubits at ALL L x L vertices (n = L^2); face anchors (L-1)^2,
checkerboard X/Z by face parity; boundary weight-2 checks alternating along
the edges (the board's convention, e.g. codes/676-110-3.json). Boundary w2
anchors are optional variables like the faces.

d >= 3 is EXACT: no weight-1 or weight-2 nontrivial logical on either side.
Weight-2 rowspace elements are exactly single active w2 checks (products of
>= 2 w2 checks have weight >= 3), so the check is polynomial and exact.

Exhaustive: L=4 -> 2^15, L=5 -> 2^24 configs. L>=6 needs the SAT encoder
(next milestone). Output: the complete (k, d>=3) map per L.
"""
import itertools
import json
import sys
import time

import numpy as np

sys.path.insert(0, "research/local2d")
from chamfer4 import gf2_rank, rows  # noqa: E402


def build_grid(L):
    """Returns n, faces {(i,j): frozenset(qubits)}, face_type, w2 list."""
    c2i = {(x, y): y * L + x for y in range(L) for x in range(L)}
    faces = {}
    for i in range(L - 1):
        for j in range(L - 1):
            faces[(i, j)] = frozenset((c2i[(i, j)], c2i[(i + 1, j)],
                                       c2i[(i, j + 1)], c2i[(i + 1, j + 1)]))
    # boundary w2 checks: horizontal edges on top/bottom, vertical on
    # left/right, alternating so that face parity and edge phase stay
    # consistent with the board convention (even faces X, odd faces Z;
    # w2 checks on the edge a face would extend into).
    # Board convention (codes/676-110-3.json): X-w2s on horizontal edges
    # at odd x, Z-w2s on vertical edges at even y. Closes all corners iff
    # L is even.
    w2 = []
    for y in (0, L - 1):
        for x in range(1, L - 1, 2):
            w2.append((sorted((c2i[(x, y)], c2i[(x + 1, y)])), True))
    for x in (0, L - 1):
        for y in range(0, L - 1, 2):
            w2.append((sorted((c2i[(x, y)], c2i[(x, y + 1)])), False))
    return L * L, faces, w2


def d3_clean(HX, HZ):
    """Exact d>=3: no weight-<=2 element of ker(H_opp)\rowspace(H_self)."""
    def side(Hself, Hopp):
        m_, n = Hself.shape
        S = np.ascontiguousarray((Hopp % 2).T)
        synd = [S[a].tobytes() for a in range(n)]
        zero = b"\x00" * Hopp.shape[0]   # syndrome length = Hopp rows!
        A = Hself.copy() % 2
        r = 0
        piv = []
        rr_ = A.shape[0]
        for col in range(n):
            p = np.nonzero(A[r:, col])[0]
            if len(p) == 0:
                continue
            p = p[0] + r
            A[[r, p]] = A[[p, r]]
            for q in range(rr_):
                if q != r and A[q, col]:
                    A[q] ^= A[r]
            piv.append(col)
            r += 1
            if r == rr_:
                break
        B = A[:r]

        def in_rs(support):
            w = np.zeros(n, dtype=np.uint8)
            w[list(support)] = 1
            for row, p in zip(B, piv):
                if w[p]:
                    w ^= row
            return not w.any()

        syn_lists = {}
        for a in range(n):
            syn_lists.setdefault(synd[a], []).append(a)
        for a in range(n):                       # weight 1
            if synd[a] == zero and not in_rs((a,)):
                return False
        for a in range(n):                       # weight 2
            for b in syn_lists.get(synd[a], ()):
                if b > a and not in_rs((a, b)):
                    return False
        return True

    return side(HX, HZ) and side(HZ, HX)


def sweep(L, deadline=None):
    n, faces, w2 = build_grid(L)
    items = ([(p, faces[p], (p[0] + p[1]) % 2 == 0) for p in sorted(faces)]
             + [(f"w{i}", frozenset(s), isx) for i, (s, isx) in enumerate(w2)])
    N = len(items)
    print(f"L={L}: n={n}, {N} anchors -> {2**N} configs", flush=True)
    best = {}
    total = 0
    t0 = time.time()
    for bits in range(2 ** N):
        if deadline and time.time() > deadline:
            print(f"TIME LIMIT at {total}", flush=True)
            break
        active = [items[i] for i in range(N) if bits >> i & 1]
        HX = rows([s for _, s, isx in active if isx], n)
        HZ = rows([s for _, s, isx in active if not isx], n)
        k = n - gf2_rank(HX) - gf2_rank(HZ)
        total += 1
        if k >= 1 and d3_clean(HX, HZ):
            if k not in best or len(active) < best[k]:
                best[k] = len(active)
                print(f"  k={k} with {len(active)} anchors", flush=True)
        if total % 500000 == 0:
            print(f"  {total}/{2**N} {time.time()-t0:.0f}s best={best}",
                  flush=True)
    print(f"DONE L={L}: {total} configs in {time.time()-t0:.0f}s", flush=True)
    print(f"complete d>=3 map: {dict(sorted(best.items()))}", flush=True)
    with open(f"/tmp/sat_map_L{L}.json", "w") as f:
        json.dump({"L": L, "n": n, "map_k_to_min_anchors": best}, f)
    return best


if __name__ == "__main__":
    sweep(int(sys.argv[1]) if len(sys.argv) > 1 else 4)
