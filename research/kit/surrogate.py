"""Cheap distance surrogates for screening codes -- and, as a free byproduct,
the explicit logical-operator *witnesses* a submission needs.

Two tools:

* ``mixed_volume(S_f, S_g)`` -- a matrix-free upper bound on k for a bivariate
  two-monomial-set construction (the Bernstein-Kushnirenko / mixed-volume
  bound; tight on the BB trinomial families). Use it to filter millions of
  candidate exponent sets before building any matrix.

* ``distance_rand`` / ``lightest_logical`` -- a randomized GF(2) coset-leader
  search for a low-weight nontrivial logical operator. This is the cheap stand
  in for an exact distance solver.

HONEST SEMANTICS. ``distance_rand`` returns an **upper bound** on the true
distance: it found *a* logical of that weight, so d <= that. It is Monte Carlo,
not a proof. In practice, for small d, raise ``trials`` until the value stops
dropping (e.g. ``distance_rand(.., trials=t)`` == ``distance_rand(.., trials=2*t)``)
and treat that as a confident upper bound. The matching ``confidence`` for a
submission built this way is ``"upper_bound"``; an ``"exact"`` claim is a
separate, server-certified tier (see ``verify/certify.py``). The witness this
search returns is exactly what the verifier checks to certify the upper bound.

Pure numpy; no exact-solver or decoder dependency (those are a later phase).
"""
import numpy as np

from css import kernel_basis, logical_basis


# =====================================================================
#  Part 1: mixed-volume proxy for k  (matrix-free)
# =====================================================================
def _cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def convex_hull_2d(points):
    pts = sorted(set(points))
    if len(pts) <= 1:
        return list(pts)
    lower = []
    for p in pts:
        while len(lower) >= 2 and _cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and _cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _polygon_area(v):
    n = len(v)
    if n < 3:
        return 0.0
    return abs(sum(v[i][0] * v[(i + 1) % n][1] - v[(i + 1) % n][0] * v[i][1]
                   for i in range(n))) / 2.0


def _minkowski(P, Q):
    """Minkowski sum of two convex hulls via pairwise sums + re-hull (hulls here
    have <= 4 vertices, so the brute force is correct and free)."""
    if not P or not Q:
        return []
    return convex_hull_2d([(p[0] + q[0], p[1] + q[1]) for p in P for q in Q])


def mixed_volume(S_f, S_g):
    """k upper bound = Area(N(f)+N(g)) - Area(N(f)) - Area(N(g)) for the Newton
    polygons of two bivariate monomial sets ``S_f``, ``S_g`` (lists of (i, j)
    exponent pairs)."""
    hf, hg = convex_hull_2d(S_f), convex_hull_2d(S_g)
    af, ag = _polygon_area(hf), _polygon_area(hg)
    a_sum = _polygon_area(convex_hull_2d(_minkowski(hf, hg)))
    return int(round(a_sum - af - ag))


# =====================================================================
#  Part 2: randomized min-weight-logical search (distance + witness)
# =====================================================================
def _rref_perm(M, perm):
    """RREF over GF(2) visiting columns in the order ``perm``; returns the
    nonzero reduced rows."""
    M = M.copy() % 2
    rows = M.shape[0]
    r = 0
    for col in perm:
        piv = next((i for i in range(r, rows) if M[i, col]), None)
        if piv is None:
            continue
        M[[r, piv]] = M[[piv, r]]
        for i in range(rows):
            if i != r and M[i, col]:
                M[i] ^= M[r]
        r += 1
        if r == rows:
            break
    return M[:r]


def _search_lightest(Hself, Hopp, trials, seed, pair_depth=10):
    """Randomized upper-bound search for the lightest nontrivial logical of one
    type: a vector v with v in ker(Hopp) (commutes with the opposite checks) but
    v not in rowspace(Hself) (not a stabilizer product). Returns
    ``(weight, support)``, or ``(inf, [])`` if the code has no logical of this
    type.

    Per trial it takes the rows of a randomly column-permuted RREF of ker(Hopp),
    plus pairwise sums of the lightest such rows (this closes most of the gap to
    minima realized only as short combinations). Still an upper bound.
    """
    Hself = np.asarray(Hself, dtype=np.int8) % 2
    Hopp = np.asarray(Hopp, dtype=np.int8) % 2
    n = Hself.shape[1]
    K = kernel_basis(Hopp)            # operators commuting with the opposite checks
    LO = logical_basis(Hself, Hopp)   # opposite-type logicals -> nontriviality test
    if K.size == 0 or LO.size == 0:
        return float("inf"), []
    rng = np.random.default_rng(seed)
    best_w, best_v = n + 1, None
    for _ in range(trials):
        red = _rref_perm(K, rng.permutation(n))
        w = red.sum(axis=1)
        nz = ((red @ LO.T) % 2).any(axis=1)
        for i in np.where(nz & (w > 0))[0]:
            if int(w[i]) < best_w:
                best_w, best_v = int(w[i]), red[i].copy() % 2
        if pair_depth > 1 and red.shape[0] >= 2:
            light = np.argsort(w)[:min(pair_depth, red.shape[0])]
            sub = red[light]
            for i in range(len(light)):
                pr = (sub[i] + sub[i + 1:]) % 2
                if pr.size == 0:
                    continue
                pw = pr.sum(axis=1)
                pnz = ((pr @ LO.T) % 2).any(axis=1) & (pw > 0)
                for j in np.where(pnz)[0]:
                    if int(pw[j]) < best_w:
                        best_w, best_v = int(pw[j]), pr[j].copy()
    if best_v is None:
        return float("inf"), []
    return best_w, sorted(int(j) for j in np.where(best_v)[0])


def lightest_logical(Hself, Hopp, trials=8000, seed=0):
    """Lightest nontrivial logical of one type, as ``(weight, support)``.

    For the X side pass ``(HX, HZ)``; for the Z side pass ``(HZ, HX)``. The
    returned support is a valid distance witness for that side (the verifier
    checks: in ker(opposite), outside rowspace(own), weight == value).
    """
    return _search_lightest(Hself, Hopp, trials, seed)


def distance_rand(HX, HZ, trials=2000, seed=0):
    """Upper bound on the code distance d = min(d_X, d_Z), as an int. Cheap
    screening number; for the witnesses, call ``lightest_logical`` per side."""
    wx, _ = _search_lightest(HX, HZ, trials, seed)
    wz, _ = _search_lightest(HZ, HX, trials, seed)
    return min(wx, wz)


if __name__ == "__main__":
    # k-proxy calibration against the BB trinomial families (true k known).
    print("mixed_volume (k upper bound) vs known k:")
    cases = {6: (-1, -2, 1, -1), 7: (-1, 1, 1, 3), 8: (-1, 2, 1, 3),
             11: (-1, -3, 1, -3), 12: (-1, 2, 1, 5), 13: (5, 1, 3, -1)}
    for k, (a, b, c, d) in cases.items():
        mv = mixed_volume([(0, 0), (1, 0), (a, b)], [(0, 0), (0, 1), (c, d)])
        print(f"  true k={k:2d}  MV={mv:2d}  {'ok' if mv == k else 'MISMATCH'}")
