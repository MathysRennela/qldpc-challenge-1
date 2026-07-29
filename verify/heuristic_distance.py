"""Heuristic distance verification (random-information-set search).

Server-side, reproducible UPPER-BOUND search for a low-weight logical operator. It
sits between the witness upper bound (`d<=`, cheap CI) and exact certification
(`d=`, verify/certify.py), filling the gap for dense / high-rate codes that exact
IP cannot reach. Two outcomes:

  refuted      a logical lighter than the claimed distance was found -> the claim
               is over-stated; the true distance is <= the found weight.
  corroborated a large fixed-budget search found nothing lighter -> confidence
               beyond a single witness (NOT a proof; exact remains the only d=).

This is purely an upper-bound search: every method here only exhibits a logical of
some weight, i.e. tightens d <= w. It never proves a lower bound. The run is
reproducible (fixed seed + trial budget) and computed server-side, never trusted
from the submission.

Engine: random information set (QDistRnd-style). Canonical path is pure Python on
verify/gf2.py (no build). If the gf2_fast C++ extension is importable it is used
for a faster, larger overall weight search; witnesses are always extracted by the
Python path (the C++ returns weights only).

Usage: python verify/heuristic_distance.py codes/foo.json [--trials N] [--seed S]
       exit code 2 on a refuted claim (so it can gate if desired).
"""
import argparse
import json
import sys
import time

import numpy as np

import gf2

try:
    import gf2_fast as _fast            # optional C++ accelerator (weights only)
except ImportError:
    _fast = None


def _matrix(support_list, n):
    H = np.zeros((len(support_list), n), dtype=np.int8)
    for r, sup in enumerate(support_list):
        for q in sup:
            H[r, q] ^= 1
    return H


def _rref_perm(K, perm):
    """RREF of K under a random column permutation, mapped back to original
    columns. Reduced rows are low-weight combinations of K's rows (candidate
    low-weight logicals); the weight is permutation-invariant."""
    R, _ = gf2.rref(K[:, perm])
    out = np.zeros_like(R)
    out[:, perm] = R
    return out


def ris_min_logical(HX, HZ, trials, seed, pair_depth=8, max_seconds=None):
    """RIS upper-bound search for the lightest nontrivial X-type logical: a vector
    in ker(H_Z) that anticommutes with some Z-logical. Returns (weight, witness),
    or (None, None) if the code has no logicals of this type. Stops after `trials`
    permutations or `max_seconds` wall-clock, whichever comes first (the time cap
    keeps the CI gate bounded regardless of n)."""
    n = HX.shape[1]
    K = gf2.kernel_basis(HZ)
    LZ = gf2.logical_basis(HX, HZ)
    if K.shape[0] == 0 or LZ.shape[0] == 0:
        return None, None
    rng = np.random.default_rng(seed)
    best, wit = n + 1, None
    deadline = (time.monotonic() + max_seconds) if max_seconds else None

    def consider(rows):
        nonlocal best, wit
        w = rows.sum(1)
        nontrivial = ((rows @ LZ.T) % 2).any(1)
        for i in np.where(nontrivial & (w > 0) & (w < best))[0]:
            best, wit = int(w[i]), rows[i].copy()

    for t in range(trials):
        red = _rref_perm(K, rng.permutation(n))
        consider(red)
        if pair_depth > 1 and red.shape[0] >= 2:        # short combinations
            w = red.sum(1)
            light = np.argsort(w)[:min(pair_depth, red.shape[0])]
            sub = red[light]
            for a in range(len(light) - 1):
                consider(sub[a] ^ sub[a + 1:])
        if deadline and (t & 63) == 0 and time.monotonic() > deadline:
            break
    return best, wit


def estimate(doc, trials=20000, seed=0, fast_trials=400000, max_seconds=None):
    """Heuristic distance verdict for a submission `doc`.

    ``trials`` is the pure-Python RIS budget per side; ``fast_trials`` is the
    gf2_fast accelerator's overall budget, used only when it exceeds ``trials``
    (the fast path reports weights, not witnesses, so it must out-search the
    Python pass to add anything). Pass ``fast_trials=0`` to disable the
    accelerator explicitly (refute_check does: the CI gate is pure Python with
    a fixed seed, so it stays deterministic). Any other skipped-accelerator
    combination warns on stderr -- see issue #290."""
    n = doc["n"]
    HX = _matrix(doc["checks"]["X"], n)
    HZ = _matrix(doc["checks"]["Z"], n)
    claimed = int(doc["distance"]["d"])

    half = (max_seconds / 2) if max_seconds else None       # split budget per side
    wX, witX = ris_min_logical(HX, HZ, trials, seed, max_seconds=half)        # X (ker HZ)
    wZ, witZ = ris_min_logical(HZ, HX, trials, seed + 1, max_seconds=half)    # Z (ker HX)
    sides = {}
    if wX is not None:
        sides["X"] = {"value": doc["distance"].get("X", {}).get("value"),
                      "lightest_found": wX,
                      "witness": sorted(int(j) for j in np.nonzero(witX)[0])}
    if wZ is not None:
        sides["Z"] = {"value": doc["distance"].get("Z", {}).get("value"),
                      "lightest_found": wZ,
                      "witness": sorted(int(j) for j in np.nonzero(witZ)[0])}
    d_heur = min([w for w in (wX, wZ) if w is not None], default=None)

    method = "ris"
    if _fast is not None and 0 < fast_trials <= trials:
        print(f"warning: gf2_fast is available but skipped "
              f"(fast_trials={fast_trials} <= trials={trials}); raise "
              f"--fast-trials or lower --trials to use the accelerator "
              f"(fast_trials=0 disables it deliberately)", file=sys.stderr)
    # Optional C++ accelerator: a larger overall search (min over both sides).
    if _fast is not None and fast_trials > trials:
        d_fast = int(_fast.distance_rand_parallel(HX, HZ, fast_trials, seed, 8, 8))
        if d_heur is None or d_fast < d_heur:
            d_heur = d_fast                # a lighter logical exists; python re-finds
            # extract a witness at the tighter weight via a focused python pass
            for H_a, H_b, key in ((HX, HZ, "X"), (HZ, HX, "Z")):
                w, wit = ris_min_logical(H_a, H_b, trials * 4, seed + 7)
                if w is not None and w <= d_fast:
                    sides.setdefault(key, {})
                    sides[key].update(lightest_found=w,
                                      witness=sorted(int(j) for j in np.nonzero(wit)[0]))
        method = "ris+gf2_fast"
        trials = max(trials, fast_trials)

    if d_heur is None:
        verdict = "inconclusive"
    elif d_heur < claimed:
        verdict = "refuted"          # found a lighter logical -> claim over-stated
    elif d_heur == claimed:
        verdict = "corroborated"     # found exactly the claimed weight, none lighter
    else:
        verdict = "inconclusive"     # budget too small to even reach the claimed weight

    return {"name": doc.get("name", ""), "claimed_d": claimed,
            "d_heuristic": d_heur, "verdict": verdict,
            "sides": sides, "trials": trials, "seed": seed, "method": method}


def refute_check(doc, seed=0, max_seconds=10.0, trials=None):
    """CI gate. Run a bounded, time-capped RIS search and report whether it found a
    logical LIGHTER than the claimed distance. Returns (refuted, d_found, witness,
    trials). Sound (the witness is a checkable lighter logical) but not complete (a
    null result is not a proof); pure Python with a fixed seed, so deterministic and
    non-flaky. Budget is n-scaled trials under a wall-clock cap; pass ``trials`` to
    override the default target (the CI gate scales both with code size)."""
    n = doc["n"]
    if trials is None:
        trials = min(8000, 2500 + 40 * n)
    res = estimate(doc, trials=trials, seed=seed, fast_trials=0,
                   max_seconds=max_seconds)
    claimed = int(doc["distance"]["d"])
    dh = res["d_heuristic"]
    refuted = dh is not None and dh < claimed
    witness = None
    if refuted:
        for s in res["sides"].values():
            if s.get("lightest_found") == dh:
                witness = s["witness"]
                break
    return refuted, dh, witness, res["trials"]


def main(path, trials, seed, fast_trials=None):
    doc = json.load(open(path))
    # A bigger --trials budget must never silently turn the accelerator off
    # (issue #290): unless --fast-trials is given explicitly, scale the fast
    # budget with the requested depth. --fast-trials 0 forces pure Python.
    if fast_trials is None:
        fast_trials = max(400000, 4 * trials)
    res = estimate(doc, trials=trials, seed=seed, fast_trials=fast_trials)
    print(json.dumps(res, indent=2))
    return 2 if res["verdict"] == "refuted" else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--trials", type=int, default=20000,
                    help="pure-Python RIS trials per side (default 20000)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--fast-trials", type=int, default=None,
                    help="gf2_fast overall trial budget (default: "
                         "max(400000, 4*trials)); 0 disables the accelerator")
    args = ap.parse_args()
    sys.exit(main(args.path, args.trials, args.seed, args.fast_trials))
