"""
Circuit-level decoding leaderboard. Like run_phenom.py but with the gate-level
single-basis Z-memory syndrome-extraction circuit (eval_circuit, z_only): noise
on every reset, CX, idle step, and measurement. Writes
decode/circuit_results.json. Incremental and resumable (a timed-out run keeps its
progress; a re-run continues). Pass slugs to restrict to specific codes.

    uv run --with stim --with ldpc --with scipy --with numpy \\
           python decode/run_circuit.py [slug ...]
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from eval import load_code
from eval_circuit import memory_ler

ROOT = os.path.join(os.path.dirname(__file__), "..")
P_RANK = 0.006        # ranking noise rate (sub-threshold; Z-only threshold ~0.01)
P_LOW = 0.004         # second point to show scaling
ROUNDS = 6
SHOTS = 5000
SEED = 17

out = os.path.join(os.path.dirname(__file__), "circuit_results.json")
PROTOCOL = {
    "noise": "circuit-level Z-memory (single-basis): depolarizing CX, "
             "reset/measurement flips, idle depolarizing on an explicit "
             "Z-stabilizer extraction circuit",
    "p": P_RANK, "p_low": P_LOW, "rounds": ROUNDS,
    "decoder": "BP+OSD over the circuit DEM (osd_cs, order 10)",
    "shots": SHOTS, "seed": SEED,
    "schedule": "greedy edge-colouring of the Z-extraction CXs",
    "metric": "per-logical-qubit LER (lower is better); ranked at p"}

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


only = set(a for a in sys.argv[1:])
for f in sorted(glob.glob(os.path.join(ROOT, "codes", "*.json"))):
    slug = os.path.splitext(os.path.basename(f))[0]
    if only and slug not in only:
        continue
    if slug in results:
        print(f"{slug}: cached, skip", flush=True)
        continue
    HX, HZ, n, k = load_code(f)
    hi = memory_ler(HX, HZ, P_RANK, rounds=ROUNDS, shots=SHOTS, seed=SEED,
                    z_only=True)
    lo = memory_ler(HX, HZ, P_LOW, rounds=ROUNDS, shots=SHOTS, seed=SEED,
                    z_only=True)
    results[slug] = {
        "n": n, "k": k,
        "per_logical_ler": round(hi["per_logical_ler"], 6),
        "block_ler": round(hi["block_ler"], 6),
        "per_logical_ler_low": round(lo["per_logical_ler"], 6),
        "rounds": ROUNDS}
    save()
    print(f"{slug}: k={k} per_log@{P_RANK}={hi['per_logical_ler']:.5f} "
          f"@{P_LOW}={lo['per_logical_ler']:.5f}", flush=True)

save()
print(f"\nwrote {out} ({len(results)} codes)", flush=True)
