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

out = os.path.join(os.path.dirname(__file__), "phenom_results.json")
PROTOCOL = {
    "noise": "phenomenological: per-round data depolarizing + measurement "
             "faults, perfect final readout",
    "p": P_RANK, "p_low": P_LOW, "rounds": ROUNDS,
    "decoder": "BP+OSD over the circuit DEM (osd_cs, order 10)",
    "shots": SHOTS, "seed": SEED,
    "metric": "per-logical-qubit LER (lower is better); ranked at p"}

# Resume: keep any results already computed (incremental writes below mean a
# timed-out run leaves usable partial data, and a re-run continues).
results = {}
if os.path.exists(out):
    try:
        prev = json.load(open(out))
        if prev.get("protocol", {}).get("p") == P_RANK:
            results = prev.get("results", {})
    except Exception:
        results = {}


def save():
    json.dump({"protocol": PROTOCOL, "results": results}, open(out, "w"),
              indent=1)


for f in sorted(glob.glob(os.path.join(ROOT, "codes", "*.json"))):
    slug = os.path.splitext(os.path.basename(f))[0]
    if slug in results:
        print(f"{slug}: cached, skip", flush=True)
        continue
    HX, HZ, n, k = load_code(f)
    hi = memory_ler(HX, HZ, P_RANK, rounds=ROUNDS, shots=SHOTS, seed=SEED)
    lo = memory_ler(HX, HZ, P_LOW, rounds=ROUNDS, shots=SHOTS, seed=SEED)
    results[slug] = {
        "n": n, "k": k,
        "per_logical_ler": round(hi["per_logical_ler"], 6),
        "block_ler": round(hi["block_ler"], 6),
        "per_logical_ler_low": round(lo["per_logical_ler"], 6),
        "rounds": ROUNDS}
    save()   # incremental: survive a timeout
    print(f"{slug}: k={k} per_log@{P_RANK}={hi['per_logical_ler']:.5f} "
          f"@{P_LOW}={lo['per_logical_ler']:.5f}", flush=True)

save()
print(f"\nwrote {out} ({len(results)} codes)", flush=True)
