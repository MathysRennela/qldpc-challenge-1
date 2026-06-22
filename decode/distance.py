"""Syndrome-decoder distance cross-check (Phase 2 of heuristic distance verification).

An independent upper-bound search that uses a decoder's mistakes instead of the
linear-algebra search of verify/heuristic_distance.py (RIS). Inject random errors,
decode with BP+OSD; the residual e ^ correction lies in ker(H_check) and, when it
anticommutes with an opposite-type logical, is an explicit nontrivial logical
whose weight upper-bounds the distance. The minimum residual weight over many
trials is d_ub >= d.

Same nature as RIS (an upper-bound search, reproducible), but a genuinely
different mechanism, so agreement strengthens a corroboration. Offline tooling
(needs ldpc): run with `uv run --with ldpc python decode/distance.py codes/foo.json`.
Pinned decoder matches decode/eval.py: BpOsdDecoder, osd_cs, order 10, max_iter 30.

Usage: python decode/distance.py codes/foo.json [--trials N] [--seed S]
"""
import argparse
import json
import os
import sys

import numpy as np
from ldpc import BpOsdDecoder

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "verify"))
import gf2

OSD_ORDER = 10


def _matrix(supports, n):
    H = np.zeros((len(supports), n), dtype=np.uint8)
    for r, sup in enumerate(supports):
        for q in sup:
            H[r, q] ^= 1
    return H


def _side(Hcheck, Lopp, n, weights, trials, seed):
    """Min residual logical weight from decoder failures (one Pauli sector).
    Errors of weight in `weights` are injected; Hcheck detects them; Lopp is the
    opposite-type logical basis used to test nontriviality. Returns (weight, witness)."""
    rng = np.random.default_rng(seed)
    decs = {w: BpOsdDecoder(Hcheck, error_rate=min(0.4, max(1e-3, w / n)),
                            max_iter=30, bp_method="minimum_sum",
                            ms_scaling_factor=0.625, osd_method="osd_cs",
                            osd_order=OSD_ORDER) for w in weights}
    best, wit = n + 1, None
    for _ in range(trials):
        w = weights[rng.integers(len(weights))]
        e = np.zeros(n, np.uint8)
        e[rng.choice(n, w, replace=False)] = 1
        r = (e + decs[w].decode((Hcheck @ e) % 2)) % 2
        if np.any((Lopp @ r) % 2):                 # nontrivial logical
            wt = int(r.sum())
            if wt < best:
                best, wit = wt, r.copy()
    return (best if wit is not None else None), wit


def estimate(doc, trials=200000, seed=0):
    n = doc["n"]
    HX = _matrix(doc["checks"]["X"], n)
    HZ = _matrix(doc["checks"]["Z"], n)
    claimed = int(doc["distance"]["d"])
    LZ = (gf2.logical_basis(HX, HZ) % 2).astype(np.uint8)   # for X residuals
    LX = (gf2.logical_basis(HZ, HX) % 2).astype(np.uint8)   # for Z residuals
    w0 = (claimed + 1) // 2
    weights = list(range(max(1, w0), w0 + 3))               # ceil(d/2) .. +2

    sides = {}
    wX, witX = _side(HZ, LZ, n, weights, trials, seed)       # X-logical in ker(HZ)
    wZ, witZ = _side(HX, LX, n, weights, trials, seed + 1)   # Z-logical in ker(HX)
    if witX is not None:
        sides["X"] = {"lightest_found": wX,
                      "witness": sorted(int(j) for j in np.nonzero(witX)[0])}
    if witZ is not None:
        sides["Z"] = {"lightest_found": wZ,
                      "witness": sorted(int(j) for j in np.nonzero(witZ)[0])}
    found = [w for w in (wX, wZ) if w is not None]
    d_heur = min(found) if found else None

    if d_heur is None:
        verdict = "inconclusive"
    elif d_heur < claimed:
        verdict = "refuted"
    elif d_heur == claimed:
        verdict = "corroborated"
    else:
        verdict = "inconclusive"
    return {"name": doc.get("name", ""), "claimed_d": claimed,
            "d_heuristic": d_heur, "verdict": verdict, "sides": sides,
            "trials": trials, "seed": seed, "method": "syndrome_decoder"}


def main(path, trials, seed):
    doc = json.load(open(path))
    res = estimate(doc, trials=trials, seed=seed)
    print(json.dumps(res, indent=2))
    return 2 if res["verdict"] == "refuted" else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--trials", type=int, default=200000)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    sys.exit(main(args.path, args.trials, args.seed))
