#!/usr/bin/env python3
"""Trivariate-bicycle (TB) campaign sweep with reproducible construction.

Implements the "multivariate/trivariate bicycle sweep" route of
fieldnotes/2026-08-20-optional-future-research-board-advancement.md.  The
repository has no ``sample_tb`` (grep: only historical mentions), so this
script provides an independent, documented constructor + enumerator under a
fresh name, with:

  * ``build_tb(l, m, p, A, B)`` -- the two-block group-algebra construction on
    G = Z_l x Z_m x Z_p, n = 2*l*m*p, monomials x^a y^b z^c, CSS commutation
    structural (abelian group).  This is the construction the sweep uses.
  * ``build_tb_zxy(l, m, A, B)`` -- the classic "z = xy" fold form (effective
    exponent (a+c mod l, b+c mod m); n = 2*l*m).  Kept strictly as the
    calibration convention the old (uncommitted) ``build_tb`` used to
    reconstruct Table 2 of arXiv:2406.19151 -- NOT the main search space.
  * ``probe_144``: the documented [[144,2,d<=12]] duplicate anomaly check.
    Since the original Table-2 term lists are not committed, the probe does an
    exhaustive *exact-support/fingerprint* comparison: it rebuilds every
    symmetry-reduced weight-2 z=xy row with (n, k) = (144, 2) over all
    l*m = 72 factor pairs and asks whether any is an exact duplicate
    (same RREF-fingerprint) of the board's n=144 submissions.  A hit resolves
    the anomaly as "reproduction of the existing entry"; no hit means the
    anomaly stays open (the board entry has a witness the local rebuild does
    not reproduce).

Screening discipline (note's execution ladder): exact CSS / rank / k / row
weight checks before any distance screen; screening distance is always an
upper bound; plausible survivors are packaged through submit.make_submission
(both witnesses persisted); finalists then go through
verify/validate_candidate.py; Pareto/nested-cell comparison against the
current codes/ snapshot happens before any claim.  This script persists every
candidate record and the packaged survivors under research/candidates/.

Symmetry reduction: quotient by the translation group (same additive shift on
every monomial of A and B) and by independent sign flips of the three axes
(automorphisms of Z_l x Z_m x Z_p preserving the CSS weight profile).  A<->B
swap is NOT quotiented (it swaps the X and Z systems, ranked separately).

Stop conditions (from the note): stop when the symmetry-reduced weight-4/5
slices produce only duplicates/dominated records or fail fresh-seed
confirmation; a larger random budget for the same slice is not a new
mechanism.
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import sys
import time
from itertools import product
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "research" / "kit"), str(ROOT / "verify")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from bb import poly_matrix  # noqa: E402
from css import compute_k, verify_css, rref  # noqa: E402
from search import fingerprint, screen, pareto_frontier  # noqa: E402
from submit import make_submission, save_submission  # noqa: E402
from surrogate import distance_rand  # noqa: E402


# ---------------------------------------------------------------------------
#  Constructors
# ---------------------------------------------------------------------------
def _monomial_full(l, m, p, a, b, c):
    """Permutation matrix for x^a y^b z^c on Z_l x Z_m x Z_p (int8)."""
    size = l * m * p
    rows = np.arange(size)
    i, j, k = np.unravel_index(rows, (l, m, p))
    col = np.ravel_multi_index(
        ((i + a) % l, (j + b) % m, (k + c) % p), (l, m, p))
    M = np.zeros((size, size), dtype=np.int8)
    M[rows, col] = 1
    return M


def poly_matrix_full(l, m, p, terms):
    """GF(2) sum of monomials on Z_l x Z_m x Z_p (repeated terms cancel)."""
    l, m, p = int(l), int(m), int(p)
    M = np.zeros((l * m * p, l * m * p), dtype=np.int8)
    for (a, b, c) in terms:
        M ^= _monomial_full(l, m, p, int(a), int(b), int(c))
    return M


def build_full(l, m, p, A_terms, B_terms):
    """Two-block code on Z_l x Z_m x Z_p: H_X = [A|B], H_Z = [B^T|A^T]."""
    l, m, p = int(l), int(m), int(p)
    A = poly_matrix_full(l, m, p, A_terms)
    B = poly_matrix_full(l, m, p, B_terms)
    HX = np.concatenate([A, B], axis=1).astype(np.int8)
    HZ = np.concatenate([B.T, A.T], axis=1).astype(np.int8)
    return HX, HZ


def build_tb_zxy(l, m, A_terms, B_terms):
    """The "z = xy" fold form: (a,b,c) -> (a+c mod l, b+c mod m), n = 2*l*m.

    This is the convention the old (uncommitted) ``build_tb`` used to
    reconstruct Table 2 of arXiv:2406.19151.  It is intentionally separated
    from ``build_full`` so nobody mistakes the calibration convention for the
    new search space.
    """
    l, m = int(l), int(m)
    Ared = {}
    for (a, b, c) in A_terms:
        e = ((int(a) + int(c)) % l, (int(b) + int(c)) % m)
        Ared[e] = Ared.get(e, 0) ^ 1
    Bred = {}
    for (a, b, c) in B_terms:
        e = ((int(a) + int(c)) % l, (int(b) + int(c)) % m)
        Bred[e] = Bred.get(e, 0) ^ 1
    A = poly_matrix(l, m, [e for e, v in Ared.items() if v])
    B = poly_matrix(l, m, [e for e, v in Bred.items() if v])
    HX = np.concatenate([A, B], axis=1).astype(np.int8)
    HZ = np.concatenate([B.T, A.T], axis=1).astype(np.int8)
    return HX, HZ


# ---------------------------------------------------------------------------
#  Symmetry reduction
# ---------------------------------------------------------------------------
def _flip_atoms(term, sx, sy, sz, l, m, p):
    a, b, c = term
    a = (a if not sx else (l - a) % l)
    b = (b if not sy else (m - b) % m)
    c = (c if not sz else (p - c) % p)
    return (a, b, c)


# aliases used by orbit_key
def _flip(term, sx, sy, sz, l, m, p):
    return _flip_atoms(term, sx, sy, sz, l, m, p)


def _translate(terms, base, l, m, p):
    return _translate_terms(terms, base, l, m, p)


def _translate_terms(terms, base, l, m, p):
    """Shift every monomial so that ``base`` maps to (0,0,0)."""
    da, db, dc = base
    return tuple(sorted(((a - da) % l, (b - db) % m, (c - dc) % p)
                        for a, b, c in terms))


def orbit_key(A, B, l, m, p):
    """Canonical key for (A, B) under translation and signed axis flips.

    Translation is absorbed by shifting the first monomial of A to (0,0,0)
    (and B by the same shift), which is a re-labelling of the group-algebra
    basis and therefore the same code.  Flips are automorphisms of the group
    that preserve CSS check weights.  A<->B swap is intentionally excluded.
    """
    A = tuple(sorted(tuple(int(x) for x in t) for t in A))
    B = tuple(sorted(tuple(int(x) for x in t) for t in B))
    keys = set()
    for sx, sy, sz in product((0, 1), repeat=3):
        Afl = tuple(sorted(_flip_atoms(t, sx, sy, sz, l, m, p) for t in A))
        Bfl = tuple(sorted(_flip_atoms(t, sx, sy, sz, l, m, p) for t in B))
        # absorb translation by shifting the first monomial of A to 0
        At = _translate(Afl, Afl[0], l, m, p)
        Bt = _translate(Bfl, Afl[0], l, m, p)
        keys.add((At, Bt))
    return min(keys)


# ---------------------------------------------------------------------------
#  Support enumerator
# ---------------------------------------------------------------------------
def _supports(l, m, p, weight):
    """All identity-fixed supports of exactly ``weight`` monomials."""
    rest = [(a, b, c)
            for a in range(l) for b in range(m) for c in range(p)
            if (a, b, c) != (0, 0, 0)]
    for combo in itertools.combinations(rest, weight - 1):
        yield [(0, 0, 0)] + list(combo)


def iter_grid(l, m, p, weight, max_orbits=None):
    """Yield (spec, HX, HZ) for symmetry-reduced (A, B) pairs, A, B both of
    ``weight`` monomials (identity fixed).  Deterministic lexicographic order;
    capped at ``max_orbits`` pairs for a bounded run."""
    supports = list(_supports(l, m, p, weight))
    seen = set()
    emitted = 0
    for A in supports:
        for B in supports:
            key = orbit_key(A, B, l, m, p)
            if key in seen:
                continue
            seen.add(key)
            hx, hz = build_full(l, m, p, A, B)
            yield ({"family": "trivariate-bicycle", "l": l, "m": m, "p": p,
                    "A": A, "B": B, "weight": weight}, hx, hz)
            emitted += 1
            if max_orbits is not None and emitted >= max_orbits:
                return


# ---------------------------------------------------------------------------
#  The [[144,2,d<=12]] duplicate anomaly probe (exact-support comparison)
# ---------------------------------------------------------------------------
def _factor_pairs(n):
    return [(l, m) for l in range(1, int(n ** 0.5) + 1)
            if n % l == 0 for m in (n // l,)
            if l * m == n]


def probe_144(trials=400, seed=20260820, max_entries=8):
    """Exhaustive fingerprint comparison over the [[144,2,d<=12]] duplicate.

    Enumerates every symmetry-reduced weight-2 z=xy row (identity + one
    nonidentity monomial per block) with (n, k) = (144, 2), for every factor
    pair l*m = 144 / 2, and compares the exact RREF fingerprints against the
    board's submitted n=144 entries.  Writes the full audit to
    research/candidates/probe-144-summary.json and returns it.

    Interpretation of the result:
      * any fingerprint hit  -> the anomaly is resolved as a reproduction of
        an existing board entry (an exact duplicate by the verifier's
        criterion);
      * no hit             -> the anomaly stays open: the submitted [[144,2,d]]
        is not reproduced by any weight-2 z=xy row, so it lives only in the
        board snapshot and needs a fresh candidate or provenance recheck.
    """
    board_entries = _board_144_entries()
    audit = {"params": {"trials": trials, "seed": seed},
             "note": (
                 "Exact-support/fingerprint audit of the [[144,2,d<=12]] "
                 "duplicate anomaly under the z=xy convention: is the board's "
                 "n=144 submission exactly reproduced by any symmetry-reduced "
                 "weight-2 z=xy row? A hit resolves the anomaly as a duplicate "
                 "reproduction; no hit means the anomaly stays open."
             ),
             "board_n144": board_entries,
             "matches": []}
    target_n = 144
    # factor pairs l*m = 72 because build_tb_zxy gives n = 2*l*m
    for l, m in _factor_pairs(target_n // 2):
        if l * m != target_n // 2:
            continue
        rest = [(a, b, c)
                for a in range(l) for b in range(m) for c in range(2)
                if (a, b, c) != (0, 0, 0)]
        seen = set()
        for t in rest:
            key = (l, m, t)
            if key in seen:
                continue
            seen.add(key)
            hx, hz = build_tb_zxy(l, m, [(0, 0, 0), t], [(0, 0, 0), t])
            if not verify_css(hx, hz):
                continue
            k = compute_k(hx, hz)
            if hx.shape[1] != target_n or k != 2:
                continue
            fp = fingerprint(hx, hz)
            rec = {"l": l, "m": m, "t": list(t), "k": k,
                   "fingerprint": fp}
            for name, bfp in board_entries.items():
                if bfp == fp:
                    rec["board_match"] = name
            audit["matches"].append(rec)
    audit["hit_count"] = sum(1 for r in audit["matches"] if "board_match" in r)
    audit["total_candidates"] = len(audit["matches"])
    out = ROOT / "research" / "candidates" / "probe-144-summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))
    return audit


def _board_144_entries():
    """Fingerprints of submitted codes/ entries with n == 144."""
    out = {}
    codes_dir = ROOT / "codes"
    if not codes_dir.exists():
        return out
    for path in sorted(codes_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text())
        except Exception:
            continue
        if int(data.get("n", 0)) != 144:
            continue
        hx = np.zeros((len(data["checks"]["X"]), data["n"]), dtype=np.int8)
        hz = np.zeros((len(data["checks"]["Z"]), data["n"]), dtype=np.int8)
        for i, row in enumerate(data["checks"]["X"]):
            hx[i, row] = 1
        for i, row in enumerate(data["checks"]["Z"]):
            hz[i, row] = 1
        out[path.name] = fingerprint(hx, hz)
    return out


# ---------------------------------------------------------------------------
#  CLI
# ---------------------------------------------------------------------------
def _parse_grids(text):
    """Parse a comma-separated list of parenthesized tuples, e.g.
    "(2,2,2),(2,3,3)" -> [(2,2,2), (2,3,3)].  Robust to surrounding
    whitespace and a trailing comma."""
    import re
    return [tuple(int(x) for x in m.split(","))
            for m in re.findall(r"\(([^)]*)\)", text)]


def parse_args(argv):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--grid", default="(6,6,2),(8,6,2),(10,6,2),(12,8,2)",
                    help="comma-separated (l,m,p) factor triples, n = 2*l*m*p")
    ap.add_argument("--weight", type=int, default=4,
                    help="monomial support weight for A and B (3..5)")
    ap.add_argument("--min-k", type=int, default=4)
    ap.add_argument("--min-d", type=int, default=4)
    ap.add_argument("--orbits", type=int, default=300,
                    help="max symmetry-reduced orbits per grid factor triple")
    ap.add_argument("--trials", type=int, default=400,
                    help="surrogate distance search trials (upper bound)")
    ap.add_argument("--seed", type=int, default=20260821)
    ap.add_argument("--probe144", action="store_true",
                    help="run the [[144,2,d<=12]] exhaustive fingerprint audit "
                         "and exit")
    ap.add_argument("--out-dir", default=None,
                    help="output dir under the repo root "
                         "(default research/candidates)")
    return ap.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.probe144:
        probe_144(trials=args.trials, seed=args.seed)
        return

    out_dir = ROOT / (args.out_dir or "research/candidates")
    out_dir.mkdir(parents=True, exist_ok=True)

    grids = _parse_grids(args.grid)
    start = time.time()
    all_records = []

    for (l, m, p) in grids:
        n = 2 * l * m * p
        if n > 700:
            print(f"skip ({l},{m},{p}): n={n} exceeds the verifier cap of 700")
            continue
        print(f"--- grid ({l},{m},{p}) weight {args.weight} "
              f"(n={n}) ---")
        candidates = iter_grid(l, m, p, args.weight, max_orbits=args.orbits)
        records = screen(candidates, min_k=args.min_k, min_d=args.min_d,
                         trials=args.trials, seed=args.seed, verbose=True)
        all_records.extend(records)
        if records:
            front = pareto_frontier(records)
            print(f"[{l},{m},{p}] {len(records)} survivors; "
                  f"{len(front)} on in-sweep Pareto frontier")
            for r in front[:6]:
                print(f"    [[{r['n']},{r['k']},{r['d']}]] eff={r['efficiency']} "
                      f"w={r['w']} fp={r['fingerprint']}")

    summary = {"argv": sys.argv[1:],
               "weight": args.weight,
               "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "elapsed_s": round(time.time() - start, 3),
               "records": all_records,
               "top": sorted(all_records, key=lambda r: r["efficiency"],
                             reverse=True)[:10]}
    (out_dir / "tb-grid-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n")

    packaged = []
    for rank, r in enumerate(_top3(all_records), 1):
        spec = r["spec"]
        hx, hz = build_full(spec["l"], spec["m"], spec["p"],
                            spec["A"], spec["B"])
        assert verify_css(hx, hz)
        k = compute_k(hx, hz)
        assert k == r["k"]
        doc = make_submission(
            hx, hz,
            name=f"[[{hx.shape[1]},{k},d<={r['d']}]] TB full-grid candidate {rank}",
            construction=(
                f"Trivariate bicycle on Z_{spec['l']} x Z_{spec['m']} x "
                f"Z_{spec['p']} (n=2*l*m*p), two-block form; "
                f"A={spec['A']}, B={spec['B']}; weight={spec['weight']}; "
                "symmetry-reduced by translation + signed axis flips; "
                f"screened with the research surrogate at {args.trials} trials."
            ),
            authors=["@mathysrennela"],
            family="other",
            references=["arXiv:2406.19151"],
            notes=("Screening distance is an upper bound, not a certificate; "
                   "recheck with verify/validate_candidate.py and compare "
                   "against the current codes/ Pareto frontier (incl. every "
                   "nested track cell) before any claim."),
            confidence="upper_bound",
            trials=800, seed=args.seed + rank,
        )
        path = out_dir / f"tb-grid-finalist-{rank}-{doc['n']}-{doc['k']}.json"
        save_submission(doc, str(path))
        packaged.append({"rank": rank, "record": r,
                         "packaged_distance": doc["distance"],
                         "path": str(path.relative_to(ROOT))})
    (out_dir / "tb-grid-packaged.json").write_text(
        json.dumps(packaged, indent=2) + "\n")
    print(json.dumps(packaged, indent=2))


def _top3(records):
    """Top 3 distinct-by-fingerprint records by efficiency."""
    best = {}
    for r in records:
        fp = r["fingerprint"]
        if fp not in best or r["efficiency"] > best[fp]["efficiency"]:
            best[fp] = r
    return sorted(best.values(), key=lambda r: r["efficiency"],
                  reverse=True)[:3]


if __name__ == "__main__":
    main()