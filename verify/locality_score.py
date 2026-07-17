"""Locality track score f (issue #168).

For a stabilizer code embedded on a D-dimensional grid of sites, with every
stabilizer generator supported inside a box of w sites per axis, the
Bravyi-Poulin-Terhal tradeoff (arXiv:0909.5200), with the w- and D-dependence
made explicit via the Bravyi-Terhal cleaning lemma (arXiv:0810.1983), reads

    k * d^(2/(D-1))  <=  64 * g(D) * w^(2 + 2/(D-1)) * n,
    g(D) = D(D-1) * (4D)^(2/(D-1)).

The exponents are provably optimal (tiling of an asymptotically good qLDPC code
into w-boxes saturates them in every D; see issue #168). The multiplicative
constant is not: the true ceiling lies between ~rho*delta^(2/(D-1)) and
64*g(D), and the g(D) shape is proof bookkeeping, not a matching construction.

The score keeps only what is proven tight -- the exponents -- plus a fixed
display constant chosen so the rotated surface code scores exactly 1:

    f = 16 * k * d^(2/(D-1)) / ( w^(2 + 2/(D-1)) * n ).

The proven ceiling is quoted separately (never mixed into the score):

    f <= 1024 * g(D)            (= 2^17 at D=2).

"Ceiling v1": future tightening of the constant changes this quoted ceiling and
never any published score. f is scale-free (a code family converges to a
constant instead of inflating with n) and, being decreasing in both D and w, a
code's score is the maximum of f over its certified embeddings.
"""
from __future__ import annotations

import math

# The display constant is fixed by the surface-code calibration below; it is not
# a free knob. SCORE_CONST / (surface w^4) = 1  =>  SCORE_CONST = 16 at D=2, and
# the same 16 normalizes every D (the surface anchor is a D=2 object).
SCORE_CONST = 16.0
# Ceiling multiplier: f <= CEILING_CONST * g(D). This is the loose, versioned
# part; bump CEILING_VERSION whenever the tracked constant improves.
CEILING_CONST = 1024.0
CEILING_VERSION = "v1"


def g(D: int) -> float:
    """The D-shape of the (loose) BPT constant: D(D-1)*(4D)^(2/(D-1))."""
    if D < 2:
        raise ValueError("locality score is defined for D >= 2")
    return D * (D - 1) * (4 * D) ** (2.0 / (D - 1))


def ceiling(D: int) -> float:
    """Proven upper bound on f in dimension D (loose, constant-only slack)."""
    return CEILING_CONST * g(D)


def score(n: int, k: int, d: int, D: int, w: float) -> float:
    """f = 16 * k * d^(2/(D-1)) / ( w^(2+2/(D-1)) * n ). Requires D >= 2, w > 0."""
    if D < 2:
        raise ValueError("locality score is defined for D >= 2")
    if not (w and w > 0 and n > 0):
        raise ValueError("need positive w and n")
    e = 2.0 / (D - 1)
    return SCORE_CONST * k * (d ** e) / ((w ** (2.0 + e)) * n)


def box_range(coords, supports, spacing: float | None = None) -> int:
    """Box-side range w: the smallest integer such that every stabilizer's
    support fits in a w-site box along each axis.

    Measured as the largest per-axis site span across all supports, plus one: a
    support spanning s lattice steps needs a box of s+1 sites per axis. The
    rotated surface-code plaquette spans one step per axis, giving w = 2, which
    is what fixes the f = 1 calibration.

    coords    : list of D-dim coordinate tuples, one per qubit.
    supports  : iterable of qubit-index lists (the stabilizer generators).
    spacing   : lattice step; inferred as the min nonzero pairwise site spacing
                when omitted.
    """
    coords = [tuple(c) for c in coords]
    if spacing is None:
        sites = sorted(set(coords))
        spacing = min((math.dist(a, b)
                       for i, a in enumerate(sites) for b in sites[i + 1:]),
                      default=1.0)
        if not spacing or spacing == float("inf"):
            spacing = 1.0
    wmax = 1
    for sup in supports:
        if not sup:
            continue
        pts = [coords[q] for q in sup]
        for axis in range(len(pts[0])):
            vals = [p[axis] for p in pts]
            span = (max(vals) - min(vals)) / spacing
            wmax = max(wmax, int(round(span)) + 1)
    return wmax


def dimension_of_class(locality_class: str) -> int | None:
    """Certified grid dimension implied by a locality class (None = no embedding
    / unrestricted, where f is undefined)."""
    if locality_class in ("local-2d-single", "local-2d-bilayer"):
        return 2
    if locality_class in ("local-3d-single", "local-3d-bilayer"):
        return 3
    return None


def score_from_computed(n, k, d, computed) -> dict | None:
    """Compute the locality score from a verifier `computed` block. Returns
    {'f','D','w','ceiling','ceiling_version'} or None when no embedding certifies
    a dimension (f is undefined for unrestricted / expander codes)."""
    D = dimension_of_class(computed.get("locality_class", "unrestricted"))
    if D is None:
        return None
    w = computed.get("locality", {}).get("box_range")
    if not w:
        return None
    return {
        "f": round(score(n, k, d, D, w), 4),
        "D": D,
        "w": w,
        "ceiling": round(ceiling(D), 1),
        "ceiling_version": CEILING_VERSION,
    }


def evaluate_embedding(n, k, d, coords, supports, layers: int = 1) -> dict:
    """Score a single embedding. Returns a dict with the geometry and, when the
    layout is honest and a distance is known, the score f. `valid` is False for a
    crammed or malformed layout (more qubits per site than declared layers, or
    sites closer than one lattice unit, which would fake a small range)."""
    if len(coords) != n:
        return {"valid": False, "reason": f"{len(coords)} coords != n={n}"}
    import collections
    pts = [tuple(c) for c in coords]
    D = len(pts[0]) if pts else 0
    mult = collections.Counter(pts)
    max_mult = max(mult.values())
    sites = sorted(mult)
    min_spacing = min((math.dist(a, b)
                       for i, a in enumerate(sites) for b in sites[i + 1:]),
                      default=float("inf"))

    def diam(sup):
        ps = [pts[q] for q in sup]
        return max((math.dist(a, b) for a in ps for b in ps), default=0.0)

    radius = max((diam(s) for s in supports), default=0.0)
    honest = (max_mult <= layers
              and (min_spacing >= 1.0 - 1e-9 or min_spacing == float("inf")))
    spacing = min_spacing if min_spacing != float("inf") else 1.0
    w = box_range(pts, supports, spacing)
    out = {
        "valid": bool(honest and D >= 2 and w > 0 and k and d),
        "D": D, "w": w, "radius": round(radius, 4),
        "max_qubits_per_site": max_mult,
        "min_spacing": (round(min_spacing, 4)
                        if min_spacing != float("inf") else None),
    }
    if not honest:
        out["reason"] = "crammed layout (qubits/site > layers or spacing < 1)"
    elif out["valid"]:
        out["f"] = round(score(n, k, d, D, w), 4)
    return out


def best_over_embeddings(n, k, d, embeddings) -> dict | None:
    """f* = max f over a code's certified embeddings. `embeddings` is a list of
    (coords, layers, label). Returns the winning embedding's score dict
    augmented with how many embeddings were scored and which one won, or None if
    none is valid (f is undefined)."""
    scored = []
    for coords, layers, label, supports in embeddings:
        ev = evaluate_embedding(n, k, d, coords, supports, layers)
        if ev.get("valid"):
            scored.append((ev, label))
    if not scored:
        return None
    ev, label = max(scored, key=lambda s: s[0]["f"])
    return {
        "f": ev["f"], "D": ev["D"], "w": ev["w"],
        "ceiling": round(ceiling(ev["D"]), 1),
        "ceiling_version": CEILING_VERSION,
        "n_embeddings": len(scored),
        "source": label,
    }


def _surface_code_layout(d: int):
    """Rotated surface code, distance d: d^2 data qubits on an integer grid with
    weight<=4 plaquettes on unit 2x2 cells. Returns (n, k, coords, supports)."""
    coords = [(x, y) for y in range(d) for x in range(d)]
    idx = {(x, y): i for i, (x, y) in enumerate(coords)}
    supports = []
    for y in range(d - 1):
        for x in range(d - 1):
            supports.append([idx[(x, y)], idx[(x + 1, y)],
                             idx[(x, y + 1)], idx[(x + 1, y + 1)]])
    return d * d, 1, coords, supports


if __name__ == "__main__":
    # Calibration: the rotated surface code must score f = 1 at every size.
    for d in (3, 5, 9, 25):
        n, k, coords, supports = _surface_code_layout(d)
        w = box_range(coords, supports)
        f = score(n, k, d, 2, w)
        print(f"surface d={d:>2}: n={n:>4} w={w} f={f:.6f}")
        assert w == 2, w
        assert abs(f - 1.0) < 1e-9, f
    print(f"g(2)={g(2):.0f} ceiling(2)={ceiling(2):.0f} (2^17={2**17})")
    assert abs(ceiling(2) - 2 ** 17) < 1e-6
    print("OK: surface code calibrates to f=1; ceiling(2)=2^17")
