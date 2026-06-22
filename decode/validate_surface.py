"""
Validate the evaluator: the surface code's X-side code-capacity LER curves for
increasing distance must cross at the known threshold (~0.10-0.11). Below
threshold larger d gives lower LER; above threshold the order flips. A clean
crossing in that range means the evaluator captures threshold behavior.
"""
import os

import numpy as np

from eval import load_code, _side_failures

ROOT = os.path.join(os.path.dirname(__file__), "..")
CODES = [("25-1-5", 5), ("49-1-7", 7), ("81-1-9", 9)]
PS = [0.06, 0.08, 0.10, 0.11, 0.12, 0.14]
SHOTS = 8000

rows = {}
for slug, dist in CODES:
    HX, HZ, n, k = load_code(os.path.join(ROOT, "codes", f"{slug}.json"))
    rng = np.random.default_rng(7)
    rows[dist] = {}
    for p in PS:
        f = _side_failures(HZ, HX, p, SHOTS, rng)  # X errors via H_Z
        rows[dist][p] = f / SHOTS
        print(f"d={dist} p={p}: LER_X={f/SHOTS:.4f}", flush=True)

print("\n  p   " + "".join(f"  d={d}    " for d, _ in [(d, 0) for d in rows]))
for p in PS:
    print(f"{p:.2f} " + "".join(f"  {rows[d][p]:.4f}" for d in rows))
print("\nThreshold = p where the d-ordering flips (larger d stops helping).")
