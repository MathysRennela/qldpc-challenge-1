#!/usr/bin/env python3
"""Bitset probe for rare low-weight multiples of prime-order divisors.

This complements designed_divisor_search.py: numpy enumeration is adequate for
multiplier weight <=2, but weight 3/4 needs integer XORs. The probe searches
XORs of shifted copies of g, canonicalizes cyclic shifts, and only constructs
CSS matrices for supports within the requested row-weight cap.
"""
from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))
from designed_divisor_search import factor_polynomial, build_candidate  # noqa: E402


def bits(poly):
    return sum(int(bit) << i for i, bit in enumerate(poly[::-1]) if bit)


def support(mask):
    return tuple(i for i in range(mask.bit_length()) if (mask >> i) & 1)


def canonical(s, n):
    return min(tuple(sorted((x - shift) % n for x in s)) for shift in s)


def probe(n, degree, multiplier_weight, row_cap, limit, samples=None, seed=0):
    g = next(g for g in factor_polynomial(n) if len(g) - 1 == degree)
    gmask = bits(g)
    max_shift = n - degree
    shifts = [gmask << p for p in range(max_shift + 1)]
    found = set()
    if samples is None:
        positions_iter = itertools.combinations(range(max_shift + 1), multiplier_weight)
    else:
        import random
        rng = random.Random(seed + n + degree)
        positions_iter = (tuple(sorted(rng.sample(range(max_shift + 1), multiplier_weight)))
                          for _ in range(samples))
    for positions in positions_iter:
        mask = 0
        for p in positions:
            mask ^= shifts[p]
        if 0 < mask.bit_count() <= row_cap:
            found.add(canonical(support(mask), n))
    out = sorted(found, key=lambda s: (len(s), s))[:limit]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weight", type=int, default=3)
    ap.add_argument("--row-cap", type=int, default=8)
    ap.add_argument("--limit", type=int, default=32)
    ap.add_argument("--n", type=int, action="append")
    ap.add_argument("--samples", type=int,
                    help="random multiplier samples instead of exhaustive enumeration")
    ap.add_argument("--seed", type=int, default=20260816)
    args = ap.parse_args()
    cases = args.n or [251, 257, 331, 337]
    for n in cases:
        factors = sorted(set(len(g) - 1 for g in factor_polynomial(n)))
        for degree in factors:
            if degree <= 1 or degree >= n - 1:
                continue
            supports = probe(n, degree, args.weight, args.row_cap, args.limit,
                              args.samples, args.seed)
            print(f"N={n} degree={degree} weight={args.weight} supports={len(supports)} "
                  f"weights={[len(s) for s in supports]}", flush=True)
            if supports:
                # Report CSS parameters for unique A/B pairs. Distance is left
                # to the normal search driver so this probe remains cheap.
                for a, b in itertools.combinations_with_replacement(supports, 2):
                    HX, HZ = build_candidate(n, a, b)
                    from css import compute_k
                    k = compute_k(HX, HZ)
                    w = max(max(int(row.sum()) for row in HX),
                            max(int(row.sum()) for row in HZ))
                    print(f"  pair k={k} w={w} A={a} B={b}", flush=True)


if __name__ == "__main__":
    main()
