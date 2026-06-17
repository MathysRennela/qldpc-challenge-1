"""Exact-distance certification (server-cert tier), via MILP over GF(2).

This is the offline / maintainer-side certifier, NOT the CI verifier. It proves
the exact distance of a CSS code and writes certs/<slug>.json, which upgrades
the code from a self-certified upper bound (d <=) to certified exact (d =) on
the board. It needs scipy (HiGHS) and the qLDPC library, so it is kept out of
the dependency-light CI verifier:

    uv run --with qldpc --with scipy python tools/certify_distance.py <slug>

Method (per-logical formulation). For the X-distance, for each Z-logical
generator l, solve  min |w|  s.t.  H_Z w = 0 (mod 2)  and  l . w = 1 (mod 2);
w is then a nontrivial X logical and |w| an upper bound. The minimum over all
generators is d_X, and solving every program to proven optimality establishes
it exactly. Symmetric for Z. d = min(d_X, d_Z).
"""
import json
import os
import sys

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "verify"))
from qldpc.codes import CSSCode          # noqa: E402
from qldpc.objects import Pauli          # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _matrix(supports, n):
    H = np.zeros((len(supports), n), dtype=int)
    for r, sup in enumerate(supports):
        for q in sup:
            H[r, q] ^= 1
    return H


def min_logical(checks, logical_row, time_limit):
    """min |w| s.t. checks @ w = 0 (mod 2) and logical_row . w = 1 (mod 2).
    Returns (weight, support, proven_optimal)."""
    m, n = checks.shape
    nv = n + m + 1                       # w (n), parity slacks s (m), slack t (1)
    A = np.zeros((m + 1, nv))
    A[:m, :n] = checks
    for r in range(m):
        A[r, n + r] = -2
    A[m, :n] = logical_row
    A[m, n + m] = -2
    lo = np.zeros(m + 1); hi = np.zeros(m + 1); lo[m] = hi[m] = 1
    c = np.concatenate([np.ones(n), np.zeros(m + 1)])
    bounds = Bounds(np.zeros(nv),
                    np.concatenate([np.ones(n), np.full(m + 1, n)]))
    res = milp(c, constraints=LinearConstraint(A, lo, hi),
               integrality=np.ones(nv), bounds=bounds,
               options={"time_limit": time_limit, "mip_rel_gap": 0.0})
    if res.x is None:
        return None, None, False
    w = np.round(res.x[:n]).astype(int) % 2
    return int(w.sum()), [int(j) for j in np.nonzero(w)[0]], res.status == 0


def certify(slug, time_limit=60):
    doc = json.load(open(os.path.join(ROOT, "codes", slug + ".json")))
    n = doc["n"]
    HX = _matrix(doc["checks"]["X"], n)
    HZ = _matrix(doc["checks"]["Z"], n)
    code = CSSCode(HX, HZ)
    LX = np.array(code.get_logical_ops(Pauli.X)).astype(int) % 2
    LZ = np.array(code.get_logical_ops(Pauli.Z)).astype(int) % 2
    out = {}
    for side, checks, gens in (("X", HZ, LZ), ("Z", HX, LX)):
        best, proven = None, True
        for l in gens:
            w, _, ok = min_logical(checks, l, time_limit)
            if w is None:
                proven = False
                continue
            proven = proven and ok
            best = w if best is None else min(best, w)
        out[side] = (best, proven, len(gens))
    dx, px, kx = out["X"]; dz, pz, kz = out["Z"]
    d, exact = min(dx, dz), (px and pz)
    print(f"{slug}: d_X={dx} (proven={px})  d_Z={dz} (proven={pz})  "
          f"-> d={d}, certified-exact={exact}  (claimed d={doc['distance']['d']})")
    if exact and d == doc["distance"]["d"]:
        cert = {"d_exact": True, "solver": "scipy/HiGHS MILP",
                "sides": {"X": {"note": f"min over {kx} Z-logical cosets = {dx}, all proven"},
                          "Z": {"note": f"min over {kz} X-logical cosets = {dz}, all proven"}}}
        with open(os.path.join(ROOT, "certs", slug + ".json"), "w") as f:
            json.dump(cert, f, indent=1)
        print(f"  wrote certs/{slug}.json")
    else:
        print("  not written (not proven exact, or distance != claimed)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: certify_distance.py <slug> [time_limit_s]", file=sys.stderr)
        sys.exit(2)
    certify(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 60)
