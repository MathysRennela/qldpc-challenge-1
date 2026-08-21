#!/usr/bin/env python3
"""Deep confirmation for staged campaign candidates.

All search results are persisted. A lighter logical is repackaged through
submit.make_submission so its witness is not lost.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "research" / "kit"), str(ROOT / "verify")]
from submit import make_submission, save_submission  # noqa: E402
import heuristic_distance as hd  # noqa: E402
from distance import decoder_distance  # noqa: E402


def matrices(doc):
    return hd._matrix(doc["checks"]["X"], doc["n"]), hd._matrix(doc["checks"]["Z"], doc["n"])


def run(path, seed, fast_trials, python_trials, decoder_trials):
    doc = json.loads(Path(path).read_text())
    hx, hz = matrices(doc)
    out = {"candidate": str(path), "seed": seed, "claimed_d": doc["distance"]["d"]}
    # Independent pure-Python RIS, with both sides searched.
    out["python_ris"] = hd.estimate(
        doc, trials=python_trials, seed=seed, fast_trials=0,
        max_seconds=None)
    # C++ RIS reports weights and supports; validate any improving result with
    # the repository's Python logical test before calling it a refutation.
    w, side, support = hd._fast.distance_rand_witness(
        hx, hz, trials=fast_trials, seed=seed + 7, pair_depth=8, threads=8)
    out["ris_fast"] = {"weight": int(w), "side": side,
                       "support": sorted(int(x) for x in support),
                       "trials": fast_trials}
    claimed = int(doc["distance"]["d"])
    lighter = bool(side and w < claimed)
    out["ris_fast"]["lighter_than_claim"] = lighter
    if lighter:
        v = np.zeros(doc["n"], dtype=np.int8)
        v[list(support)] = 1
        opposite = hz if side == "X" else hx
        basis = hd.gf2.logical_basis(hx, hz) if side == "X" else hd.gf2.logical_basis(hz, hx)
        valid = (int(v.sum()) == int(w) and not ((opposite @ v) % 2).any()
                 and bool(((basis @ v) % 2).any()))
        out["ris_fast"]["python_validated"] = valid
        if valid:
            side_values = {"X": int(doc["distance"]["X"]["value"]),
                           "Z": int(doc["distance"]["Z"]["value"])}
            side_values[side] = int(w)
            new_doc = make_submission(
                hx, hz,
                name=f"[[{doc['n']},{doc['k']},d<={min(side_values.values())}]] deep-refuted campaign candidate",
                construction=doc["provenance"]["construction"] +
                             f" Deep confirmation found a {side}-logical of weight {w}.",
                authors=doc["provenance"]["authors"], family=doc.get("family"),
                confidence="upper_bound", trials=2000, seed=seed)
            stem = Path(path).stem + f"-refuted-{w}"
            save_submission(new_doc, str(ROOT / "research" / "candidates" / f"{stem}.json"))
            out["corrected_submission"] = f"research/candidates/{stem}.json"
    # Decoder confirmation is optional in the quick ladder; retain failures as
    # explicit evidence when enabled.
    if decoder_trials > 0:
        out["decoder"] = decoder_distance(
            hx, hz, trials=decoder_trials, seed=seed + 1000,
            max_seconds=300, witness_trials=2000)
    else:
        out["decoder"] = {"skipped": True, "reason": "quick RIS ladder"}
    result_path = ROOT / "research" / "candidates" / (Path(path).stem + ".deep-confirmation.json")
    result_path.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"candidate": path, "python": out["python_ris"].get("d_heuristic"),
                      "fast": out["ris_fast"],
                      "decoder": {"d_heuristic": out["decoder"].get("d_heuristic"),
                                  "verdict": out["decoder"].get("verdict")},
                      "saved": str(result_path)}, indent=2), flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("paths", nargs="+", help="staged candidate JSON files")
    p.add_argument("--seed", type=int, default=20260818)
    p.add_argument("--fast-trials", type=int, default=8_000_000)
    p.add_argument("--python-trials", type=int, default=60_000)
    p.add_argument("--decoder-trials", type=int, default=200_000,
                   help="set to 0 to skip BP+OSD in a quick ladder")
    a = p.parse_args()
    for i, path in enumerate(a.paths):
        run(path, a.seed + i * 10000, a.fast_trials, a.python_trials, a.decoder_trials)

if __name__ == "__main__":
    main()
