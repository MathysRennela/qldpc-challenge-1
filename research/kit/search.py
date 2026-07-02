"""A generic search funnel for *discovering* codes (the heart of autoresearch).

The constructors in this kit build one code at a time; this module sweeps a
*family* of them, screens each cheaply, and surfaces the best. The funnel is the
standard three stages:

    1. generate   candidate (HX, HZ) from a family (a sampler/enumerator)
    2. screen     skip k < min_k; estimate d with the surrogate; score by k*d^2/n
    3. rank       sort by efficiency and/or extract the Pareto frontier

All pure numpy. The screening distance is ``surrogate.distance_rand`` -- an
UPPER bound -- so ``screen`` gives you ranked *candidates*, not certified codes.
Confirm the finalists' distance (``research/kit/distance.py``: exact MILP or decoder
corroboration) before claiming anything, then package the winner with
``submit.make_submission``.

``screen`` consumes any iterable of ``(label, HX, HZ)`` triples, so you can point
it at your own generator. ``sample_bb`` is a ready-made one for the BB family;
writing a 2BGA / coset sampler on top of ``group_algebra`` / ``coset`` is the
same shape.
"""
import hashlib
import json
import os

import numpy as np

from css import compute_k, verify_css, rref
from surrogate import distance_rand
from bb import build_bb


def efficiency(n, k, d):
    """The board's headline encoding-efficiency figure, k*d^2 / n."""
    return (k * d * d / n) if n else 0.0


def fingerprint(HX, HZ):
    """Exact-duplicate key: the reduced row echelon forms pin the stabilizer
    group. Equal fingerprint => identical code (same convention as the
    verifier's duplicate check). Used to dedup a sweep."""
    HX = np.asarray(HX, dtype=np.int8) % 2
    HZ = np.asarray(HZ, dtype=np.int8) % 2
    b = rref(HX)[0].tobytes() + b"|" + rref(HZ)[0].tobytes()
    return hashlib.sha256(b).hexdigest()[:16]


def screen(candidates, *, min_k=1, min_d=1, trials=400, seed=0,
           metric=efficiency, keep=None, verbose=False):
    """Screen an iterable of ``(spec, HX, HZ)`` candidates.

    ``spec`` is any JSON-serializable description of how the code was built (a
    dict of construction parameters is ideal -- it lets you rebuild the winner
    without re-parsing a string). For each distinct code: require ``k >= min_k``,
    estimate ``d`` with ``distance_rand`` (upper bound; require ``d >= min_d``),
    and score with ``metric(n, k, d)``. Returns records
    ``{spec, n, k, d, efficiency, fingerprint}`` sorted by score (best first),
    deduplicated by fingerprint, truncated to ``keep`` if given.
    """
    seen = {}
    for spec, HX, HZ in candidates:
        if not verify_css(HX, HZ):          # constructors guarantee this; stay safe
            continue
        k = compute_k(HX, HZ)
        if k < min_k:
            continue
        fp = fingerprint(HX, HZ)
        if fp in seen:
            continue
        n = int(HX.shape[1])
        d = distance_rand(HX, HZ, trials=trials, seed=seed)
        if d == float("inf") or d < min_d:
            continue
        rec = {"spec": spec, "n": n, "k": int(k), "d": int(d),
               "efficiency": round(float(metric(n, k, d)), 4), "fingerprint": fp}
        seen[fp] = rec
        if verbose:
            print(f"  [[{n},{k},{d}]] eff={rec['efficiency']:.3f}  {spec}")
    out = sorted(seen.values(), key=lambda r: r["efficiency"], reverse=True)
    return out[:keep] if keep else out


def pareto_frontier(records):
    """The Pareto-optimal records over (n smaller, k larger, d larger): those
    not dominated by any other (no other has n' <= n, k' >= k, d' >= d with at
    least one strict). This is the board's frontier view -- there can be many
    co-leaders, none collapsed to a single rank."""
    front = []
    for r in records:
        dominated = any(
            s is not r
            and s["n"] <= r["n"] and s["k"] >= r["k"] and s["d"] >= r["d"]
            and (s["n"] < r["n"] or s["k"] > r["k"] or s["d"] > r["d"])
            for s in records
        )
        if not dominated:
            front.append(r)
    return sorted(front, key=lambda r: (r["n"], -r["k"], -r["d"]))


# ---------------------------------------------------------------------------
#  Persistence: append-and-resume a leaderboard across sweeps
# ---------------------------------------------------------------------------
def load_leaderboard(path):
    """Load a saved leaderboard (list of records), or [] if none exists."""
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []


def update_leaderboard(path, records):
    """Merge ``records`` into the leaderboard at ``path`` (keyed by fingerprint,
    so re-screening the same code just refreshes it), write it back sorted by
    efficiency, and return the merged list. Lets a long search pause and resume."""
    board = {r["fingerprint"]: r for r in load_leaderboard(path)}
    for r in records:
        board[r["fingerprint"]] = r
    out = sorted(board.values(), key=lambda r: r["efficiency"], reverse=True)
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    return out


# ---------------------------------------------------------------------------
#  A ready-made sampler for the BB family
# ---------------------------------------------------------------------------
def sample_bb(num, *, l_range=(4, 12), m_range=(3, 10), weight=3, seed=0):
    """Yield ``num`` random bivariate-bicycle candidates ``(spec, HX, HZ)``.

    Each picks a random torus Z_l x Z_m and two sets of ``weight`` distinct
    monomials (distinct so the supports do not cancel mod 2). ``spec`` is a dict
    ``{"family": "bb", "l", "m", "A", "B"}`` -- pass it straight to ``build_bb``
    to rebuild the code.
    """
    rng = np.random.default_rng(seed)

    def distinct_monomials(l, m):
        grid = [(a, b) for a in range(l) for b in range(m)]
        idx = rng.choice(len(grid), size=min(weight, len(grid)), replace=False)
        return [grid[i] for i in idx]

    for _ in range(num):
        l = int(rng.integers(l_range[0], l_range[1] + 1))
        m = int(rng.integers(m_range[0], m_range[1] + 1))
        if l * m < weight:
            continue
        A = distinct_monomials(l, m)
        B = distinct_monomials(l, m)
        HX, HZ = build_bb(l, m, A, B)
        yield ({"family": "bb", "l": l, "m": m, "A": A, "B": B}, HX, HZ)


if __name__ == "__main__":
    # Sweep a few hundred random BB codes and show the best + the frontier.
    recs = screen(sample_bb(300, seed=1), min_k=4, min_d=4, trials=200)
    print(f"screened -> {len(recs)} distinct codes with k>=4, d>=4")
    print("top 5 by efficiency k*d^2/n:")
    for r in recs[:5]:
        print(f"  [[{r['n']},{r['k']},{r['d']}]]  eff={r['efficiency']:.3f}")
    front = pareto_frontier(recs)
    params = sorted({(r["n"], r["k"], r["d"]) for r in front})   # dedup for display
    print(f"Pareto frontier ({len(front)} codes, {len(params)} distinct params): "
          + ", ".join(f"[[{n},{k},{d}]]" for n, k, d in params[:8]))
