#!/usr/bin/env python3
"""Seeded search around PR 580's degree-64 cyclic ideal.

Working output belongs in research/candidates; this script never writes codes/.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

from sympy import Poly, gcd, symbols

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research" / "kit"))

from css import compute_k
from group_algebra import build_2bga, cyclic_product
from submit import make_submission, save_submission
from surrogate import distance_rand
from validate_candidate import validate_candidate

N = 337
A0 = (0, 1, 12, 24, 27, 69, 93, 113, 128, 143, 149, 162, 262, 269, 294, 309)
B0 = (17, 36, 38, 50, 64, 79, 81, 82, 83, 144, 145, 247, 291, 325)

def mask(s):
    return sum(1 << x for x in s)

def tup(m):
    return tuple(i for i in range(N) if (m >> i) & 1)

def rotate(m, shift):
    return ((m << shift) | (m >> (N - shift))) & ((1 << N) - 1) if shift else m

def main():
    x = symbols("x")
    p = Poly(x**N + 1, x, modulus=2)
    pa = Poly(sum(x**i for i in A0), x, modulus=2)
    g = gcd(p, pa)
    assert g.degree() == 64
    gmask = mask(tuple(i for i, bit in enumerate(g.all_coeffs()[::-1]) if int(bit) & 1))
    print("common divisor degree", g.degree(), flush=True)

    mul, _ = cyclic_product(N)
    rng = random.Random(20260816)
    seen = set()
    base_a, base_b = mask(A0), mask(B0)
    # Mutations use paired shifts so the output remains in the same ideal.
    shifts = list(range(N))
    records = []
    for trial in range(12000):
        a, b = base_a, base_b
        for _ in range(rng.randint(1, 5)):
            s1, s2 = rng.sample(shifts, 2)
            delta = gmask ^ rotate(gmask, (s2 - s1) % N)
            if rng.random() < 0.5:
                a ^= delta
            else:
                b ^= delta
        aa, bb = tup(a), tup(b)
        if not (10 <= len(aa) <= 16 and 10 <= len(bb) <= 16):
            continue
        key = (aa, bb)
        if key in seen:
            continue
        seen.add(key)
        HX, HZ = build_2bga(mul, aa, bb)
        k = compute_k(HX, HZ)
        if k != 128:
            continue
        d = int(distance_rand(HX, HZ, trials=300, seed=20260816 + trial))
        records.append((d, len(aa), len(bb), aa, bb))
        if len(records) % 20 == 0:
            print("tested", trial, "accepted", len(records), "best", max(r[0] for r in records), flush=True)
        if d < 80:
            continue
        name = f"[[674,128,d<={d}]] N337 ideal mutation"
        doc = make_submission(
            HX, HZ, name=name,
            construction=("Cyclic 2BGA on Z_337 using the degree-64 common divisor "
                          "of x^337+1; seeded mutations of the PR 580 ideal supports; "
                          f"A={list(aa)}, B={list(bb)}."),
            authors=["@mathysrennela"], family="generalized-bicycle",
            confidence="upper_bound", trials=2000, seed=20260816 + trial,
        )
        out = ROOT / "research" / "candidates"
        out.mkdir(exist_ok=True)
        stem = f"n337-ideal-{doc['n']}-{doc['k']}-{doc['distance']['d']}"
        save_submission(doc, str(out / f"{stem}.json"))
        verdict = validate_candidate(doc, seed=20260816 + trial, refute=True)
        (out / f"{stem}.verdict.json").write_text(json.dumps(verdict, indent=2) + "\n")
        print("candidate", stem, "passed", verdict.get("passed"), verdict.get("labels"), flush=True)
    print("finished accepted", len(records), "best", max((r[0] for r in records), default=None), flush=True)
    if records:
        print("top", sorted(records, reverse=True)[:5], flush=True)

if __name__ == "__main__":
    main()
