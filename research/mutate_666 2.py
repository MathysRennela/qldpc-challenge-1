#!/usr/bin/env python3
"""Local mutation search around the PR 577 Z_333 designed-divisor code.

All mutated supports remain in the common ideal because they are XORs of cyclic
shifts of the original supports. Candidates are only staged after packaging
with submit.make_submission, which preserves both logical witnesses.
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research" / "kit"))
sys.path.insert(0, str(ROOT / "verify"))

from css import compute_k  # noqa: E402
from group_algebra import build_2bga, cyclic_product  # noqa: E402
from submit import make_submission  # noqa: E402
from surrogate import distance_rand  # noqa: E402
from validate_candidate import validate_candidate  # noqa: E402

N = 333
A0 = (0, 2, 20, 49, 58, 128, 139, 146, 157, 200, 222, 238, 247, 281)
B0 = (0, 1, 17, 37, 58, 93, 107, 136, 147, 149, 152, 165, 260, 273, 324, 326)
MUL, _ = cyclic_product(N)


def vec(s):
    v = 0
    for x in s:
        v |= 1 << x
    return v


def support(v):
    return tuple(i for i in range(N) if (v >> i) & 1)


def shift(v, t):
    out = 0
    for i in range(N):
        if (v >> i) & 1:
            out |= 1 << ((i + t) % N)
    return out


def random_pool(base, rng, count=3000, max_weight=18):
    pool = {base}
    shifts = [shift(base, t) for t in range(N)]
    pool.update(shifts)
    for _ in range(count):
        v = 0
        for _ in range(rng.choice((2, 2, 3, 3, 4))):
            v ^= shifts[rng.randrange(N)]
        w = v.bit_count()
        if 8 <= w <= max_weight:
            pool.add(v)
    return sorted(pool, key=lambda x: (x.bit_count(), x))


def build(a, b):
    return build_2bga(MUL, list(a), list(b))


def main():
    rng = random.Random(20260816)
    pa = random_pool(vec(A0), rng)
    pb = random_pool(vec(B0), rng)
    print(f"pool A={len(pa)} B={len(pb)}", flush=True)

    # Rank-filter random pairs. A row has weight |A|+|B|, so enforce the
    # public max-check cap while allowing useful nearby changes.
    pairs = []
    seen = set()
    for _ in range(1200):
        a = pa[rng.randrange(len(pa))]
        b = pb[rng.randrange(len(pb))]
        if a.bit_count() + b.bit_count() > 32:
            continue
        key = (a, b)
        if key in seen:
            continue
        seen.add(key)
        HX, HZ = build(support(a), support(b))
        k = compute_k(HX, HZ)
        if k > 150:
            pairs.append((k, a, b, HX, HZ))
            print(f"high-k pair k={k} wa={a.bit_count()} wb={b.bit_count()}", flush=True)
        elif k == 150 and len(pairs) < 8:
            # Keep a few same-k candidates for distance screening.
            pairs.append((k, a, b, HX, HZ))
    pairs.sort(key=lambda x: -x[0])
    print(f"rank survivors={len(pairs)}", flush=True)

    out = ROOT / "research" / "candidates"
    out.mkdir(exist_ok=True)
    staged = 0
    for idx, (k, a, b, HX, HZ) in enumerate(pairs[:4]):
        seed = 20260816 + idx * 100003
        d = distance_rand(HX, HZ, trials=700, seed=seed)
        print(f"screen [[666,{k},{d}]] wa={a.bit_count()} wb={b.bit_count()}", flush=True)
        if k <= 150 and d < 79:
            continue
        doc = make_submission(
            HX, HZ,
            name=f"[[666,{k},d<=screen]] mutated designed-divisor Z_333",
            construction=("Cyclic generalized bicycle over Z_333; A and B are XOR combinations "
                          "of cyclic shifts of the PR 577 degree-75 designed-divisor supports; "
                          f"A={list(support(a))}, B={list(support(b))}."),
            authors=["@mathysrennela"], family="generalized-bicycle",
            confidence="upper_bound", trials=500, seed=seed,
        )
        fp = hashlib.sha256(json.dumps(doc["checks"], sort_keys=True).encode()).hexdigest()[:16]
        stem = f"mutated-666-{doc['k']}-{doc['distance']['d']}-{fp}"
        (out / f"{stem}.json").write_text(json.dumps(doc, indent=2) + "\n")
        verdict = validate_candidate(doc, seed=seed + 900000, refute=True)
        (out / f"{stem}.verdict.json").write_text(json.dumps(verdict, indent=2) + "\n")
        print(f"staged {stem}: passed={verdict['passed']} labels={verdict['labels']}", flush=True)
        staged += int(verdict["passed"])
    print(f"passed candidates staged: {staged}")


if __name__ == "__main__":
    main()
