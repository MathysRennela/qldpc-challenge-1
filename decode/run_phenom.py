"""
Phenomenological-noise decoding leaderboard. Like run_leaderboard.py but with
T noisy rounds of stabilizer measurement and measurement faults (eval_phenom),
not a single perfect round. Fixed rounds for every code so the time exposure is
comparable across distances. Writes decode/phenom_results.json.

    uv run --with stim --with ldpc --with scipy --with numpy \\
           python decode/run_phenom.py
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from eval import load_code
from eval_phenom import memory_ler

ROOT = os.path.join(os.path.dirname(__file__), "..")
P_RANK = 0.035        # ranking noise rate (sub-threshold ~0.04, resolvable)
P_LOW = 0.025         # second point to show scaling
ROUNDS = 6
SHOTS = 6000
SEED = 13

results = {}
for f in sorted(glob.glob(os.path.join(ROOT, "codes", "*.json"))):
    slug = os.path.splitext(os.path.basename(f))[0]
    HX, HZ, n, k = load_code(f)
    hi = memory_ler(HX, HZ, P_RANK, rounds=ROUNDS, shots=SHOTS, seed=SEED)
    lo = memory_ler(HX, HZ, P_LOW, rounds=ROUNDS, shots=SHOTS, seed=SEED)
    results[slug] = {
        "n": n, "k": k,
        "per_logical_ler": round(hi["per_logical_ler"], 6),
        "block_ler": round(hi["block_ler"], 6),
        "per_logical_ler_low": round(lo["per_logical_ler"], 6),
        "rounds": ROUNDS}
    print(f"{slug}: k={k} per_log@{P_RANK}={hi['per_logical_ler']:.5f} "
          f"@{P_LOW}={lo['per_logical_ler']:.5f}", flush=True)

doc = {
    "protocol": {
        "noise": "phenomenological: per-round data depolarizing + measurement "
                 "faults, perfect final readout",
        "p": P_RANK, "p_low": P_LOW, "rounds": ROUNDS,
        "decoder": "BP+OSD over the circuit DEM (osd_cs, order 10)",
        "shots": SHOTS, "seed": SEED,
        "metric": "per-logical-qubit LER (lower is better); ranked at p"},
    "results": results,
}
out = os.path.join(os.path.dirname(__file__), "phenom_results.json")
json.dump(doc, open(out, "w"), indent=1)
print(f"\nwrote {out} ({len(results)} codes)", flush=True)
