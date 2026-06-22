"""
Code-capacity decoding evaluator for the decoding track (v1).

Measures a CSS code's logical error rate (LER) under independent code-capacity
noise, decoded by a pinned BP+OSD decoder. The result is computed here (fixed
seed, fixed shot budget), not claimed by the submitter, so it is reproducible
and not gameable.

X errors are detected by H_Z and corrected with BP+OSD on H_Z; a residual is a
logical failure if it lies outside rowspace(H_X). Z errors mirror this. A shot
fails if either side fails. LER is reported per block with a binomial stderr.

Pinned: ldpc.BpOsdDecoder, osd_method='osd_cs', osd_order=10, max_iter=30.
"""
import json
import os
import sys

import numpy as np
from ldpc import BpOsdDecoder

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "verify"))
import gf2

OSD_ORDER = 10
MAX_ITER = 30


def _matrix(supports, n):
    H = np.zeros((len(supports), n), dtype=np.uint8)
    for r, s in enumerate(supports):
        for q in s:
            H[r, q] ^= 1
    return H


def load_code(path):
    d = json.load(open(path))
    n = d["n"]
    return _matrix(d["checks"]["X"], n), _matrix(d["checks"]["Z"], n), n, d["k"]


def _side_failures(H, H_opp, p, shots, rng):
    """Decode errors detected by H; count residuals outside rowspace(H_opp)."""
    n = H.shape[1]
    dec = BpOsdDecoder(H.astype(np.uint8), error_rate=float(p),
                       max_iter=MAX_ITER, bp_method="product_sum",
                       osd_method="osd_cs", osd_order=OSD_ORDER)
    base_rank = gf2.rank(H_opp)
    fails = 0
    for _ in range(shots):
        e = (rng.random(n) < p).astype(np.uint8)
        syn = (H @ e) % 2
        corr = dec.decode(syn).astype(np.uint8)
        res = (e ^ corr) % 2
        if res.any():
            # residual is a logical failure iff it is NOT in rowspace(H_opp)
            stacked = np.vstack([H_opp, res])
            if gf2.rank(stacked) > base_rank:
                fails += 1
    return fails


def logical_error_rate(HX, HZ, p, shots=20000, seed=0):
    """LER under code-capacity noise (a shot fails if the X or Z side fails).

    Reports both block LER and per-logical-qubit LER. Per-logical is the fair
    metric for ranking codes of different k (block LER penalizes high-k codes,
    which have more logical operators that can fail); it is the recommended
    decoding-track metric.
    """
    rng = np.random.default_rng(seed)
    k = HX.shape[1] - gf2.rank(HX) - gf2.rank(HZ)
    # decode X errors via H_Z (residual tested against rowspace(H_X)); Z mirrors
    fx = _side_failures(HZ, HX, p, shots, rng)
    fz = _side_failures(HX, HZ, p, shots, rng)
    lx, lz = fx / shots, fz / shots
    ler = lx + lz - lx * lz                      # block LER
    per_logical = 1 - (1 - ler) ** (1 / k) if k else ler
    err = (ler * (1 - ler) / shots) ** 0.5
    return {"p": p, "k": k, "ler": ler, "ler_per_logical": per_logical,
            "ler_X": lx, "ler_Z": lz, "stderr": err, "shots": shots}


if __name__ == "__main__":
    HX, HZ, n, k = load_code(sys.argv[1])
    p = float(sys.argv[2]) if len(sys.argv) > 2 else 0.05
    shots = int(sys.argv[3]) if len(sys.argv) > 3 else 20000
    r = logical_error_rate(HX, HZ, p, shots=shots, seed=1)
    print(f"[[{n},{k}]] p={p}: block_LER={r['ler']:.4g} +- {r['stderr']:.2g}, "
          f"per_logical={r['ler_per_logical']:.4g} "
          f"(X={r['ler_X']:.4g} Z={r['ler_Z']:.4g}, {shots} shots)")
