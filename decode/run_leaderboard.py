"""
Generate the decoding-track leaderboard data: evaluate every board code under
the pinned code-capacity protocol and write decode/results.json. The site reads
that file to render the ranking. Computed offline (needs ldpc), like the exact
certs; not part of the cheap CI verifier.

Protocol (v1): independent code-capacity noise at p_ref, BP+OSD (osd_cs,
order 10), fixed seed, fixed shot budget. Metric: per-logical-qubit LER (the
fair cross-code metric; lower is better).
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from eval import load_code, logical_error_rate

ROOT = os.path.join(os.path.dirname(__file__), "..")
P_REF = 0.04
SHOTS = 6000
SEED = 11

results = {}
for f in sorted(glob.glob(os.path.join(ROOT, "codes", "*.json"))):
    slug = os.path.splitext(os.path.basename(f))[0]
    HX, HZ, n, k = load_code(f)
    r = logical_error_rate(HX, HZ, P_REF, shots=SHOTS, seed=SEED)
    results[slug] = {"n": n, "k": k, "block_ler": round(r["ler"], 6),
                     "per_logical_ler": round(r["ler_per_logical"], 6),
                     "stderr": round(r["stderr"], 6)}
    print(f"{slug}: k={k} per_logical={r['ler_per_logical']:.5f} "
          f"block={r['ler']:.5f}", flush=True)

doc = {
    "protocol": {
        "noise": "code-capacity, independent X and Z at p",
        "p": P_REF, "decoder": "BP+OSD (ldpc, osd_cs, order 10, max_iter 30)",
        "shots": SHOTS, "seed": SEED,
        "metric": "per-logical-qubit LER (lower is better)"},
    "results": results,
}
out = os.path.join(os.path.dirname(__file__), "results.json")
json.dump(doc, open(out, "w"), indent=1)
print(f"\nwrote {out} ({len(results)} codes)", flush=True)
