#!/usr/bin/env python3
import itertools
import json
import random
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))
sys.path.insert(0, str(ROOT / "research" / "kit"))
sys.path.insert(0, str(ROOT / "verify"))

from designed_divisor_search import factor_polynomial, poly_mul_mod2, build_candidate
from css import compute_k
from submit import make_submission, save_submission
from surrogate import distance_rand
from validate_candidate import validate_candidate


def product(fs):
    p = np.array([1], dtype=np.int8)
    for f in fs:
        p = poly_mul_mod2(p, f)
    return p


def support(p):
    return tuple(i for i, bit in enumerate(p[::-1]) if bit)


def shifted_xor(base, shifts, n=337):
    out = set()
    for s in shifts:
        for x in base:
            out.add((x + s) % n)
    # GF(2) parity
    counts = {}
    for s in shifts:
        for x in base:
            y = (x + s) % n
            counts[y] = counts.get(y, 0) ^ 1
    return tuple(sorted(x for x, bit in counts.items() if bit))


def multiples(g, cap=16, random_three=2000, rng=None):
    rng = rng or random.Random(7)
    base = support(g)
    found = {tuple(base)} if len(base) <= cap else set()
    # q=1 and q=2, canonicalize by fixing first shift to zero.
    for j in range(1, 337):
        s = shifted_xor(base, (0, j))
        if 0 < len(s) <= cap:
            found.add(s)
    for _ in range(random_three):
        shifts = (0, rng.randrange(1, 337), rng.randrange(1, 337))
        if shifts[1] == shifts[2]:
            continue
        s = shifted_xor(base, shifts)
        if 0 < len(s) <= cap:
            found.add(s)
    return sorted(found, key=lambda x: (len(x), x))


def main():
    fs = factor_polynomial(337)
    degree21 = [f for f in fs if len(f) - 1 == 21]
    factors = []
    for combo in itertools.combinations(degree21, 3):
        factors.append((63, product(combo)))
        factors.append((64, product((np.array([1, 1], dtype=np.int8),) + combo)))
    rng = random.Random(20260816)
    tested = 0
    for degree, g in factors:
        if degree != 64:
            continue
        ms = multiples(g, cap=30, random_three=10000, rng=rng)
        if len(ms) < 2:
            continue
        print("degree", degree, "multiples", len(ms), flush=True)
        # Prefer pairs with distinct supports and bounded number of candidates.
        pairs = list(itertools.combinations_with_replacement(ms, 2))
        rng.shuffle(pairs)
        for a, b in pairs[:100]:
            HX, HZ = build_candidate(337, a, b)
            k = compute_k(HX, HZ)
            tested += 1
            if k != 128:
                continue
            d = int(distance_rand(HX, HZ, trials=100, seed=20260816 + tested))
            if d < 10:
                continue
            print("PROMISING", degree, k, d, len(a), len(b), a, b, flush=True)
            doc = make_submission(
                HX, HZ,
                name=f"[[674,{k},d<={d}]] N337 designed-divisor probe",
                construction=f"Cyclic 2BGA on Z_337; sparse multiples of a common degree-{degree} GF(2) divisor of x^337+1; A={list(a)}, B={list(b)}.",
                authors=["@mathysrennela"], family="generalized-bicycle",
                confidence="upper_bound", trials=2000, seed=20260816,
            )
            verdict = validate_candidate(doc, seed=20260816 + tested, refute=True)
            out = ROOT / "research" / "candidates"
            out.mkdir(exist_ok=True)
            save_submission(doc, str(out / f"n337-{doc['n']}-{doc['k']}-{doc['distance']['d']}.json"))
            (out / f"n337-{doc['n']}-{doc['k']}-{doc['distance']['d']}.verdict.json").write_text(json.dumps(verdict, indent=2) + "\n")
            print("VALIDATED", verdict, flush=True)
            if verdict.get("passed"):
                return
    print("done tested", tested, flush=True)


if __name__ == "__main__":
    main()
