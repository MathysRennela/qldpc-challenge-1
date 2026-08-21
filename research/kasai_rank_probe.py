#!/usr/bin/env python3
"""Probe the Kasai pair-partition search for rank/k variation.

Route 4 phase 2 (reconstruct new witnesses): the paper instances are already
on the board with exact distances, so a new candidate only advances the board
if it beats the current [[n,k,d]] in some cell.  The first question is whether
the construction can even produce a different k at the same n.

This probe runs the kasai-repo search across many seeds for a target instance,
collecting the k of each accepted candidate.  It does NOT claim distance; it
only reports whether higher-k (or different-k) candidates exist.  Any candidate
that looks structurally interesting is persisted to research/candidates/ for
later packaging through the standard kit + validator.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KASAI = ROOT / "research" / "candidates" / "pp_cpm" / "kasai-repo"
sys.path.insert(0, str(KASAI / "scripts"))

from search_inequivalent_pair_partition_cpm_css_codes import (  # noqa: E402
    TARGETS,
    search_instance,
)


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instances", nargs="*", default=["qc_590_240_12"])
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--samples", type=int, default=2000)
    ap.add_argument("--sampler", default="near-source")
    ap.add_argument("--pairing-source", default="reference")
    ap.add_argument("--base-seed", type=int, default=20260821)
    ap.add_argument("--output", type=Path, default=ROOT / "research" / "candidates" / "kasai-rank-probe")
    return ap.parse_args()


def main():
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    results = {}
    for name in args.instances:
        found_any = 0
        best = None  # highest k found
        for seed_off in range(args.seeds):
            seed = args.base_seed + seed_off
            # Reuse the kasai search_instance with a tiny namespace of args.
            class _A:
                pass
            a = _A()
            a.input = KASAI / "data" / "reconstructed_instances"
            a.output = args.output
            a.instances = [name]
            a.samples = args.samples
            a.seed = seed
            a.sampler = args.sampler
            a.pairing_source = args.pairing_source
            a.forbidden_patterns = None
            a.run_distance = False
            a.require_distance = False
            a.exact_isomorphism = False
            a.allow_rank_change = True
            a.allow_zero_exponents = False
            a.make_nonzero_representative = True
            a.near_source_terms = 3
            a.local_restarts = 100
            a.local_steps = 10000
            a.local_kick = 12
            a.zero_walk_steps = 200
            a.zero_walk_trials_per_step = 200
            a.batch_size = 20000
            a.threads = 8
            a.distance_timeout = 1800
            a.use_even_kernel_parity = True
            a.target_distance = None
            try:
                item = search_instance(name, a)
            except Exception as exc:  # noqa: BLE001
                print(f"{name} seed {seed}: ERROR {exc}")
                continue
            if not item.get("found"):
                continue
            found_any += 1
            k = item["checks"]["k"]
            results.setdefault(name, {}).setdefault("k_counts", {})
            results[name]["k_counts"][str(k)] = results[name]["k_counts"].get(str(k), 0) + 1
            if best is None or k > best:
                best = k
                results[name]["best_k"] = k
                results[name]["best_seed"] = seed
                results[name]["best_checks"] = item["checks"]
        results.setdefault(name, {})["found_candidates"] = found_any
        results.setdefault(name, {})["seeds_tried"] = args.seeds
        print(f"{name}: found {found_any}/{args.seeds} seeds, best k={best} "
              f"(target k={TARGETS[name]['k']})")
        print(f"    k distribution: {results[name].get('k_counts', {})}")

    dest = args.output / "summary.json"
    dest.write_text(json.dumps(results, indent=2) + "\n")
    print(f"wrote {dest}")


if __name__ == "__main__":
    main()