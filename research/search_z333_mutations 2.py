#!/usr/bin/env python3
"""Bounded local search around a cyclic Z_333 generalized-bicycle pair.

This is unattended autoresearch output: candidates are staged only under
research/candidates.  A/B supports are mutated by cyclic translation-normalized
single substitutions, additions, deletions, and two-term swaps.  The cyclic
2BGA constructor guarantees CSS; exact GF(2) rank and row-weight filters are
applied before the research surrogate.  Every survivor reaching packaging is
saved together with the trusted validator verdict.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research" / "kit"))
sys.path.insert(0, str(ROOT / "verify"))

from css import compute_k, verify_css, rref  # noqa: E402
from group_algebra import build_2bga, cyclic_product  # noqa: E402
from submit import make_submission  # noqa: E402
from surrogate import distance_rand  # noqa: E402
from validate_candidate import validate_candidate  # noqa: E402

N = 333
A0 = (0, 2, 20, 49, 58, 128, 139, 146, 157, 200, 222, 238, 247, 281)
B0 = (0, 1, 17, 37, 58, 93, 107, 136, 147, 149, 152, 165, 260, 273, 324, 326)


def canon(s: set[int]) -> tuple[int, ...]:
    """Canonicalize simultaneous cyclic translation of a support."""
    return min(tuple(sorted((x - shift) % N for x in s)) for shift in s)


def shift_xor(base: set[int], shifts: tuple[int, ...]) -> tuple[int, ...]:
    """XOR cyclic shifts of a base multiple of the common divisor."""
    out: set[int] = set()
    for shift in shifts:
        for x in base:
            y = (x + shift) % N
            if y in out:
                out.remove(y)
            else:
                out.add(y)
    return canon(out) if out else tuple()


def mutations(base: tuple[int, ...], max_weight: int = 32):
    """Generate divisor-preserving support mutations.

    The supplied support is a multiple of the degree-75 common divisor.  XOR
    with its cyclic translates is therefore another multiple, unlike arbitrary
    term substitutions. We enumerate one-, two-, and selected three-shift
    combinations, retaining only rows that can stay at max check weight 32.
    """
    s = set(base)
    out = {canon(s)}
    shifts = list(range(1, N))
    for d in shifts:
        t = shift_xor(s, (0, d))
        if 1 <= len(t) <= max_weight:
            out.add(t)
    # Three shifts are a modest local expansion around the original code.
    for d in range(1, N, 3):
        for e in range(d + 1, min(N, d + 18)):
            t = shift_xor(s, (0, d, e))
            if 1 <= len(t) <= max_weight:
                out.add(t)
    return sorted(out, key=lambda x: (len(x), x))


def build(mul, a, b):
    return build_2bga(mul, list(a), list(b))


def main() -> int:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=20260816)
    p.add_argument("--screen-trials", type=int, default=180)
    p.add_argument("--package-trials", type=int, default=5000)
    p.add_argument("--max-pairs", type=int, default=25000)
    p.add_argument("--max-weight", type=int, default=32)
    p.add_argument("--min-screen-d", type=int, default=76)
    args = p.parse_args()

    mul, elems = cyclic_product(N)
    ia = {x: i for i, x in enumerate(elems)}
    # cyclic_product(Z_333) indexes are exactly 0..332, but retain the map to
    # make the construction explicit and robust to kit indexing changes.
    am = mutations(A0, max_weight=args.max_weight)
    bm = mutations(B0, max_weight=args.max_weight)
    print(f"A mutations={len(am)} B mutations={len(bm)}", flush=True)

    # Keep all candidates with k > 150, and a bounded deterministic sample of
    # k=150 pairs for distance improvement. The exact baseline dimensions are
    # computed, never assumed.
    rng = np.random.default_rng(args.seed)
    pairs = [(a, b) for a in am for b in bm]
    rng.shuffle(pairs)
    seed_pair = (canon(set(A0)), canon(set(B0)))
    pairs = [seed_pair] + [pair for pair in pairs if pair != seed_pair]
    pairs = pairs[:args.max_pairs]
    staged = passed = screened = 0
    seen = set()
    out = ROOT / "research" / "candidates"
    out.mkdir(exist_ok=True)

    for idx, (a, b) in enumerate(pairs):
        HX, HZ = build(mul, a, b)
        if not verify_css(HX, HZ):
            raise RuntimeError("cyclic 2BGA CSS invariant failed")
        maxw = max(int(HX.sum(axis=1).max()), int(HZ.sum(axis=1).max()))
        if maxw > args.max_weight:
            continue
        k = compute_k(HX, HZ)
        key = hashlib.sha256(rref(HX)[0].tobytes() + b"|" + rref(HZ)[0].tobytes()).hexdigest()
        if key in seen:
            continue
        seen.add(key)
        # The target is k>150 or d>=80; k=150 candidates are screened for d.
        if k < 150:
            continue
        d = int(distance_rand(HX, HZ, trials=args.screen_trials, seed=args.seed + idx))
        if not (k > 150 or d >= args.min_screen_d):
            continue
        screened += 1
        print(f"screened [[{2*N},{k},{d}]] w={maxw} A={a} B={b}", flush=True)
        doc = make_submission(
            HX, HZ,
            name=f"[[{2*N},{k},{d}]] Z_333 local support mutation",
            construction=("Cyclic generalized bicycle on Z_333, H_X=[A|B], "
                          "H_Z=[B^T|A^T]. Local support mutation search around "
                          f"A0={list(A0)}, B0={list(B0)}; A={list(a)}, B={list(b)}; "
                          f"screen_trials={args.screen_trials}, seed={args.seed + idx}."),
            authors=["@mathysrennela"], family="generalized-bicycle",
            references=["arXiv:2111.03654", "arXiv:2306.16400"],
            confidence="upper_bound", trials=args.package_trials,
            seed=args.seed + idx,
        )
        fp = hashlib.sha256(key.encode()).hexdigest()[:16]
        stem = f"z333-mutation-{doc['n']}-{doc['k']}-{doc['distance']['d']}-{fp}"
        (out / f"{stem}.json").write_text(json.dumps(doc, indent=2) + "\n")
        verdict = validate_candidate(doc, seed=args.seed + idx + 100000, refute=True)
        (out / f"{stem}.verdict.json").write_text(json.dumps(verdict, indent=2) + "\n")
        staged += 1
        if verdict.get("passed"):
            passed += 1
        print(f"staged {stem}: passed={verdict.get('passed')} labels={verdict.get('labels')}", flush=True)
    print(json.dumps({"pairs": len(pairs), "unique": len(seen), "screened": screened,
                      "staged": staged, "passed": passed}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
