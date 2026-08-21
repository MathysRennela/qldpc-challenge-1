#!/usr/bin/env python3
"""Stage-only search around the Z_333 generalized-bicycle seed for w=25..29."""
from __future__ import annotations
import hashlib, json, random, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "research" / "kit"), str(ROOT / "verify")]
from group_algebra import build_2bga, cyclic_product  # noqa: E402
from css import compute_k  # noqa: E402
from surrogate import distance_rand  # noqa: E402
from submit import make_submission  # noqa: E402
from validate_candidate import validate_candidate  # noqa: E402

N = 333
SEED_DOC = ROOT / "research/candidates/mutated-666-150-95-67275d626f0a1342.json"
OUT = ROOT / "research/candidates"


def actual_supports(doc):
    x = doc["checks"]["X"][0]
    a = tuple(i for i in x if i < N)
    b = tuple(i - N for i in x if i >= N)
    return a, b


def shift(v, t):
    return tuple(sorted((x + t) % N for x in v))


def xor_support(terms):
    s = set()
    for v in terms:
        for x in v:
            if x in s: s.remove(x)
            else: s.add(x)
    return tuple(sorted(s))


def pool(base, rng, target_max=18, count=4000):
    shifts = [shift(base, t) for t in range(N)]
    vals = {tuple(base), *shifts}
    for _ in range(count):
        terms = [shifts[rng.randrange(N)] for _ in range(rng.choice((2, 2, 3, 3, 4)))]
        v = xor_support(terms)
        if 8 <= len(v) <= target_max:
            vals.add(v)
    return sorted(vals, key=lambda x: (len(x), x))


def main():
    doc = json.loads(SEED_DOC.read_text())
    a0, b0 = actual_supports(doc)
    rng = random.Random(20260818)
    pa, pb = pool(a0, rng), pool(b0, rng)
    mul, _ = cyclic_product(N)
    print(f"seed sizes A={len(a0)} B={len(b0)}; pools A={len(pa)} B={len(pb)}", flush=True)
    rank_survivors = []
    seen = set()
    # Rank-filter first; only build candidates with requested raw support sum.
    for _ in range(2500):
        a, b = pa[rng.randrange(len(pa))], pb[rng.randrange(len(pb))]
        target = len(a) + len(b)
        if target < 25 or target > 29: continue
        key = (a, b)
        if key in seen: continue
        seen.add(key)
        HX, HZ = build_2bga(mul, a, b)
        k = compute_k(HX, HZ)
        if k >= 100:
            rank_survivors.append((k, a, b, HX, HZ))
    rank_survivors.sort(key=lambda z: -z[0])
    print(f"rank survivors k>=100: {len(rank_survivors)}", flush=True)
    for i, (k, a, b, HX, HZ) in enumerate(rank_survivors[:30]):
        seed = 20260818 + i * 1009
        d = distance_rand(HX, HZ, trials=1200, seed=seed, backend="auto", threads=8)
        w = len(a) + len(b)
        print(f"screen [[666,{k},{d}]] w={w} |A|={len(a)} |B|={len(b)}", flush=True)
        # Stronger than the existing w=25/28 baselines only if k*d^2/n improves;
        # all board advancement is decided by the trusted validator below.
        if d < 4: continue
        submission = make_submission(
            HX, HZ,
            name=f"[[666,{k},d<=screen]] Z_333 weight-{w} mutation",
            construction=("Cyclic generalized bicycle over Z_333; supports are XORs of cyclic "
                          f"shifts of the PR 577 seed supports; A={list(a)}, B={list(b)}."),
            authors=["@mathysrennela"], family="generalized-bicycle",
            references=[], confidence="upper_bound", trials=1200, seed=seed)
        fp = hashlib.sha256(json.dumps(submission["checks"], sort_keys=True).encode()).hexdigest()[:16]
        stem = f"weight{w}-666-{submission['k']}-{submission['distance']['d']}-{fp}"
        path = OUT / f"{stem}.json"
        path.write_text(json.dumps(submission, indent=2) + "\n")
        verdict = validate_candidate(submission, seed=seed + 900000, refute=True)
        (OUT / f"{stem}.verdict.json").write_text(json.dumps(verdict, indent=2) + "\n")
        print(f"staged {stem}: passed={verdict['passed']} labels={verdict['labels']}", flush=True)
    print("search complete", flush=True)

if __name__ == "__main__": main()
