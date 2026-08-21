#!/usr/bin/env python3
"""Persisted BP+OSD cross-checks for the staged Z_333 candidates."""
from __future__ import annotations

import argparse
import importlib.util
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = sorted((ROOT / "research" / "candidates").glob("mutated-666-150-*.json"))
DECODE = ROOT / "decode" / "distance.py"


def load_decoder():
    spec = importlib.util.spec_from_file_location("qldpc_decoder_distance", DECODE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_phase(label: str, seconds: float, trials: int, seed: int):
    mod = load_decoder()
    for i, path in enumerate(CANDIDATES):
        doc = json.loads(path.read_text())
        started = time.time()
        result = mod.estimate(doc, trials=trials, seed=seed + i, max_seconds=seconds)
        result["phase"] = label
        result["wall_seconds"] = time.time() - started
        out = path.with_suffix(f".{label}.decoder.json")
        out.write_text(json.dumps(result, indent=2) + "\n")
        print(path.name, json.dumps({
            "phase": label,
            "claimed_d": result.get("claimed_d"),
            "d_heuristic": result.get("d_heuristic"),
            "verdict": result.get("verdict"),
            "trials": result.get("trials"),
            "wall_seconds": round(result["wall_seconds"], 1),
            "output": str(out.relative_to(ROOT)),
        }), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=("quick", "strong"), required=True)
    ap.add_argument("--seconds", type=float, required=True)
    ap.add_argument("--trials", type=int, default=200000)
    ap.add_argument("--seed", type=int, default=20260817)
    args = ap.parse_args()
    run_phase(args.phase, args.seconds, args.trials, args.seed)
