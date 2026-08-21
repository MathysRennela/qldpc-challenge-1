#!/usr/bin/env python3
"""Bounded symmetry-reduced AMC4 nonuniform-weight sweep (n <= 240).

Implements the AMC extensions route of
fieldnotes/2026-08-20-optional-future-research-board-advancement.md, second
stage: AMC4 with *nonuniform* generator weights.

  * uses the independently specified constructor in research/kit/amc.py
    (Koszul boundary maps over F_2[Z_{l1} x Z_{l2} x Z_{l3} x Z_{l4}]).  Its
    embedded calibration reproduces the public AMC4 example [[84,6,7]] at
    parameter level and verifies CSS commutation; this script runs the
    module's own smoke at startup as a construction sanity check.
  * enumerates AMC4 "nonuniform weight" elements: each of the four Koszul
    polynomials is identity-fixed with a support of ``weight`` monomials, and
    the four weights are allowed to differ (the ``--weights`` parameter lists
    the per-polynomial weights, e.g. "3,3,4,4").  The uniform case
    "4,4,4,4" is the AMC4 counterpart of the AMC3 weight-4 slice.
  * applies the quotient-lattice shortest-cycle heuristic as a *prefilter*
    (NOT a distance certificate): the smallest subset of non-identity
    generator monomials that sums to 0 mod (l1,l2,l3,l4).  Candidates whose
    shortest relation is <= 2 are dropped before the distance screen; longer
    cycles are recorded and the distance is still screened (the heuristic may
    reject cheaply, never promote).
  * runs exact CSS / rank / k / row-weight checks BEFORE any distance screen
    (screen does this), screens distance only for ranking (upper bound),
    packages every plausible survivor through submit.make_submission (both
    witnesses persisted) and runs the trusted validate_candidate on the
    finalists.
  * stop conditions: when a slice yields only duplicates, dominated
    candidates, or no k >= 4 records with a credible distance screen, print
    the checkpoint and do NOT expand the budget (a larger random budget for
    the same slice is not a new mechanism).

Symmetry reduction: quotient by permutation of the four cyclic axes and
independent sign flips (automorphisms of the group preserving the CSS
check-weight profile), applied to the (A, B, C, D) quadruple.  A/B/C/D
exchange is intentionally NOT quotiented (it swaps the X and Z systems,
ranked separately).
"""
from __future__ import annotations

import argparse
import itertools
import json
import runpy
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "research" / "kit"), str(ROOT / "verify")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from amc import build_amc, shortest_quotient_cycle  # noqa: E402
from css import compute_k, verify_css  # noqa: E402
from search import fingerprint, screen  # noqa: E402
from submit import make_submission, save_submission  # noqa: E402
from validate_candidate import validate_candidate  # noqa: E402


# ---------------------------------------------------------------------------
#  Quotient-lattice shortest-cycle prefilter
# ---------------------------------------------------------------------------
def _prefilter_reject(orders, supports):
    """True when the quotient-lattice heuristic finds a size-<=2 relation."""
    non_identity = [t for sup in supports for t in sup if any(t)]
    cycle = shortest_quotient_cycle(orders, non_identity)
    return cycle is not None and cycle <= 2


# ---------------------------------------------------------------------------
#  Symmetry reduction
# ---------------------------------------------------------------------------
def _permuted(t, perm, flips, orders):
    out = [0, 0, 0, 0]
    for i in range(4):
        v = t[perm[i]]
        if flips[i]:
            v = (-v) % orders[perm[i]]
        out[i] = v
    return (out[0], out[1], out[2], out[3])


def orbit_key(supports, orders):
    """Canonical key of the (A, B, C, D) quadruple under axis permutations and
    independent sign flips (same transformation applied to every monomial)."""
    orders = tuple(int(o) for o in orders)
    keys = set()
    for perm in itertools.permutations((0, 1, 2, 3)):
        for flips in itertools.product((0, 1), repeat=4):
            canon = []
            for sup in supports:
                canon.append(tuple(sorted(
                    _permuted(t, perm, flips, orders) for t in sup)))
            keys.add(tuple(canon))
    return min(keys)


# ---------------------------------------------------------------------------
#  Enumerator
# ---------------------------------------------------------------------------
def iter_amc4(orders, weights, max_orbits=None, max_combos=None, seed=0):
    """Yield (spec, HX, HZ) for symmetry-reduced AMC4 (A, B, C, D) quadruples.

    ``weights`` is a 4-tuple of per-polynomial support sizes (each >= 1).  The
    identity is always included, so each polynomial has ``weights[i] - 1``
    non-identity monomials.  Bounded seeded random sampling over the
    identity-fixed supports, deduplicated by the orbit key (axis permutations
    + sign flips); ``max_orbits`` caps emitted distinct orbits and
    ``max_combos`` caps sampled quadruples (either bound stops iteration).
    """
    rest = [(a, b, c, d)
            for a in range(orders[0]) for b in range(orders[1])
            for c in range(orders[2]) for d in range(orders[3])
            if (a, b, c, d) != (0, 0, 0, 0)]
    pools = []
    for w in weights:
        pools.append([[(0, 0, 0, 0)] + list(combo)
                      for combo in itertools.combinations(rest, w - 1)])
    rng = np.random.default_rng(seed)
    seen = set()
    emitted = 0
    examined = 0
    while True:
        if max_orbits is not None and emitted >= max_orbits:
            return
        if max_combos is not None and examined >= max_combos:
            return
        A = pools[0][int(rng.integers(len(pools[0])))]
        B = pools[1][int(rng.integers(len(pools[1])))]
        C = pools[2][int(rng.integers(len(pools[2])))]
        D = pools[3][int(rng.integers(len(pools[3])))]
        examined += 1
        key = orbit_key((A, B, C, D), orders)
        if key in seen:
            continue
        seen.add(key)
        if _prefilter_reject(orders, [A, B, C, D]):
            continue
        hx, hz = build_amc(orders, [A, B, C, D])
        yield ({"family": "amc4", "orders": list(orders),
                "weights": list(weights),
                "A": A, "B": B, "C": C, "D": D}, hx, hz)
        emitted += 1


# ---------------------------------------------------------------------------
#  CLI
# ---------------------------------------------------------------------------
def _parse_grids(text):
    """Parse a comma-separated list of parenthesized tuples, e.g.
    "(2,2,2,2),(2,3,3,3)" -> [(2,2,2,2), (2,3,3,3)].  Robust to
    surrounding whitespace and a trailing comma."""
    import re
    return [tuple(int(x) for x in m.split(","))
            for m in re.findall(r"\(([^)]*)\)", text)]


def parse_args(argv):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--grid", default="(2,2,2,2),(2,2,2,3),(2,2,3,3)",
                    help="comma-separated (l1,l2,l3,l4), n=6*l1*l2*l3*l4 <= 240")
    ap.add_argument("--weights", default="3,3,4,4",
                    help="per-polynomial support weights (nonuniform, e.g. "
                         "3,3,4,4 or 4,4,4,4 for the uniform counterpart)")
    ap.add_argument("--min-k", type=int, default=4)
    ap.add_argument("--min-d", type=int, default=4)
    ap.add_argument("--orbits", type=int, default=400,
                    help="max symmetry-reduced quadruples per grid")
    ap.add_argument("--combos", type=int, default=20000,
                    help="max sampled quadruples per grid (runtime bound)")
    ap.add_argument("--trials", type=int, default=400,
                    help="surrogate distance trials (upper bound)")
    ap.add_argument("--seed", type=int, default=20260821)
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--out-dir", default=None,
                    help="output dir under the repo root "
                         "(default research/candidates)")
    return ap.parse_args(argv)


def _top3(records):
    """Top 3 distinct-by-fingerprint records by efficiency."""
    best = {}
    for r in records:
        fp = r["fingerprint"]
        if fp not in best or r["efficiency"] > best[fp]["efficiency"]:
            best[fp] = r
    return sorted(best.values(), key=lambda r: r["efficiency"],
                  reverse=True)[:3]


def main(argv=None):
    args = parse_args(argv)
    # construction sanity: the kit AMC calibration (incl. [[84,6,7]])
    runpy.run_path(str(ROOT / "research" / "kit" / "amc.py"))

    out_dir = ROOT / (args.out_dir or "research/candidates")
    out_dir.mkdir(parents=True, exist_ok=True)

    weights = tuple(int(w) for w in args.weights.split(","))
    if len(weights) != 4 or any(w < 1 for w in weights):
        raise SystemExit("--weights must be four positive integers")

    grids = _parse_grids(args.grid)
    all_records = []
    start = time.time()

    for orders in grids:
        n = 6 * orders[0] * orders[1] * orders[2] * orders[3]
        if n > 240:
            print(f"skip {orders}: n={n} > 240")
            continue
        print(f"--- AMC4 {orders} weights {weights} (n={n}) ---")
        candidates = iter_amc4(orders, weights, max_orbits=args.orbits,
                               max_combos=args.combos, seed=args.seed)
        records = screen(candidates,
                         min_k=args.min_k, min_d=args.min_d,
                         trials=args.trials, seed=args.seed,
                         verbose=args.verbose)
        all_records.extend(records)
        if not records:
            print(f"  no candidate survives k>={args.min_k} d>={args.min_d}; "
                  "slice is dead -- STOP, do not expand budget")
        else:
            print(f"  {len(records)} survivors:")
            for r in sorted(records, key=lambda r: r["efficiency"],
                            reverse=True)[:5]:
                print(f"    [[{r['n']},{r['k']},{r['d']}]] "
                      f"eff={r['efficiency']} fp={r['fingerprint']}")

    summary = {"argv": sys.argv[1:], "weights": list(weights),
               "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "elapsed_s": round(time.time() - start, 3),
               "records": all_records,
               "top": sorted(all_records, key=lambda r: r["efficiency"],
                             reverse=True)[:10]}
    (out_dir / "amc4-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n")

    packaged = []
    for rank, r in enumerate(_top3(all_records), 1):
        c = r["spec"]
        hx, hz = build_amc(c["orders"], [c["A"], c["B"], c["C"], c["D"]])
        assert verify_css(hx, hz)
        k = compute_k(hx, hz)
        assert k == r["k"]
        doc = make_submission(
            hx, hz,
            name=f"[[{hx.shape[1]},{k},d<={r['d']}]] AMC4 candidate {rank}",
            construction=(
                f"AMC4 on Z_{c['orders'][0]} x Z_{c['orders'][1]} x "
                f"Z_{c['orders'][2]} x Z_{c['orders'][3]}; Koszul polynomials "
                f"A={c['A']}, B={c['B']}, C={c['C']}, D={c['D']} with "
                f"nonuniform weights {c['weights']}; identity-fixed, "
                "symmetry-reduced by axis permutations and sign flips; "
                "screened with the research surrogate."
            ),
            authors=["@mathysrennela"],
            family="other",
            references=["Lin et al., Abelian multicycle codes"],
            notes=("Screening distance is an upper bound, not a certificate; "
                   "recheck with verify/validate_candidate.py and compare "
                   "against the current codes/ Pareto frontier (incl. every "
                   "nested track cell) before any claim."),
            confidence="upper_bound",
            trials=800, seed=args.seed + rank,
        )
        path = out_dir / f"amc4-finalist-{rank}-{doc['n']}-{doc['k']}.json"
        save_submission(doc, str(path))
        verdict = validate_candidate(doc, seed=args.seed + rank)
        path.with_suffix(".verdict.json").write_text(
            json.dumps(verdict, indent=2) + "\n")
        packaged.append({"rank": rank, "record": r,
                         "packaged_distance": doc["distance"],
                         "passed": verdict.get("passed", False),
                         "path": str(path.relative_to(ROOT))})
    (out_dir / "amc4-packaged.json").write_text(
        json.dumps(packaged, indent=2) + "\n")
    print(json.dumps(packaged, indent=2))


if __name__ == "__main__":
    main()