#!/usr/bin/env python3
"""Bounded designed-divisor pilot for prime-order cyclic generalized bicycles.

For odd prime N, factor x^N + 1 over GF(2), choose a nontrivial divisor g,
and enumerate low-weight multiples of g. Using two multiples of the same g
makes the intended cyclic rank target k ~= 2*deg(g) explicit, but every result
is checked by the repository's CSS arithmetic and trusted validator.

This is research working code; output belongs in research/candidates/ and is
never committed to codes/ automatically.
"""
from __future__ import annotations

import argparse
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


def factor_polynomial(n: int) -> list[np.ndarray]:
    """Return monic irreducible GF(2) factors of x^n + 1."""
    try:
        from sympy import factor_list, Poly, symbols
    except ImportError as exc:  # pragma: no cover - environment-specific
        raise RuntimeError("pilot requires sympy; install it in the research environment") from exc
    x = symbols("x")
    _, factors = factor_list(Poly(x**n + 1, x, modulus=2))
    out = []
    for poly, multiplicity in factors:
        coeffs = [int(c) % 2 for c in poly.all_coeffs()]
        for _ in range(multiplicity):
            out.append(np.asarray(coeffs, dtype=np.int8))
    return out


def poly_mul_mod2(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    out = np.zeros(len(a) + len(b) - 1, dtype=np.int8)
    for i, ai in enumerate(a):
        if ai:
            out[i:i + len(b)] ^= b
    return out


def support(poly: np.ndarray, n: int) -> tuple[int, ...]:
    """Convert descending-coefficient polynomial to exponents modulo x^n-1."""
    return tuple(i for i, bit in enumerate(poly[::-1]) if bit)


def _canonical_shift(s: tuple[int, ...], n: int) -> tuple[int, ...]:
    """Canonical representative of a support under cyclic translation."""
    return min(tuple(sorted((x - shift) % n for x in s)) for shift in s)


def low_weight_multiples(g: np.ndarray, n: int, multiplier_weight: int,
                         limit: int, max_support_weight: int = 8) -> list[tuple[int, ...]]:
    """Enumerate distinct low-weight multiples g*q within a row-weight cap.

    The cap is applied to the resulting multiple, not to q. This matters here:
    a sparse multiplier can still produce a dense row, which is irrelevant to
    the weight-8 and below board cells.
    """
    max_q_degree = n - len(g)
    found: set[tuple[int, ...]] = set()
    # q is represented ascending here; reverse g for multiplication convenience.
    ga = g[::-1]
    for weight in range(1, multiplier_weight + 1):
        for positions in itertools.combinations(range(max_q_degree + 1), weight):
            q = np.zeros(max_q_degree + 1, dtype=np.int8)
            q[list(positions)] = 1
            product = poly_mul_mod2(ga, q)
            # Degree is below n, so no cyclic wrap ambiguity remains.
            s = tuple(i for i, bit in enumerate(product) if bit)
            if s and len(s) <= max_support_weight:
                found.add(_canonical_shift(s, n))
    return sorted(found, key=lambda s: (len(s), s))[:limit]


_GROUP_CACHE: dict[int, np.ndarray] = {}


def build_candidate(n: int, a: tuple[int, ...], b: tuple[int, ...]):
    if n not in _GROUP_CACHE:
        _GROUP_CACHE[n] = cyclic_product(n)[0]
    return build_2bga(_GROUP_CACHE[n], list(a), list(b))


def run(ns: list[int], divisor_degrees: set[int], multiplier_weight: int,
        multiple_limit: int, max_support_weight: int, screen_trials: int,
        validate_trials: int, min_screen_d: int, seed: int,
        all_factors: bool = False) -> int:
    staged = 0
    seen_codes: set[bytes] = set()
    seen_parameters: set[tuple[int, int, int]] = set()
    for n in ns:
        factors = factor_polynomial(n)
        chosen = [g for g in factors if 1 < len(g) - 1 and len(g) - 1 in divisor_degrees]
        if not all_factors:
            # Factor conjugates often provide equivalent search budgets; one
            # representative per degree keeps the pilot bounded.
            by_degree = {}
            for g in chosen:
                by_degree.setdefault(len(g) - 1, g)
            chosen = list(by_degree.values())
        print(f"N={n}: factors={[len(g)-1 for g in factors]}, selected={len(chosen)}", flush=True)
        for g in chosen:
            multiples = low_weight_multiples(
                g, n, multiplier_weight, multiple_limit, max_support_weight)
            print(f"  deg(g)={len(g)-1}: {len(multiples)} multiples", flush=True)
            for a, b in itertools.combinations_with_replacement(multiples, 2):
                HX, HZ = build_candidate(n, a, b)
                if not verify_css(HX, HZ):
                    continue
                code_key = rref(HX)[0].tobytes() + b"|" + rref(HZ)[0].tobytes()
                if code_key in seen_codes:
                    continue
                seen_codes.add(code_key)
                k = compute_k(HX, HZ)
                code_seed = seed + int.from_bytes(hashlib.sha256(code_key).digest()[:4], "little")
                d = distance_rand(HX, HZ, trials=screen_trials, seed=code_seed)
                if d < min_screen_d:
                    continue
                parameter_key = (2 * n, int(k), int(d))
                if parameter_key in seen_parameters:
                    continue
                seen_parameters.add(parameter_key)
                print(f"  screen [[{2*n},{k},{int(d)}]] eff={k*d*d/(2*n):.3f}", flush=True)
                doc = make_submission(
                    HX, HZ,
                    name=f"[[{2*n},{k},{int(d)}]] designed-divisor prime pilot",
                    construction=(f"Cyclic 2BGA on Z_{n}; both blocks are low-weight multiples "
                                  f"of a common GF(2) divisor g of x^{n}+1, deg(g)={len(g)-1}; "
                                  f"A support={list(a)}, B support={list(b)}."),
                    authors=["@mathysrennela"], family="generalized-bicycle",
                    confidence="upper_bound", trials=validate_trials,
                    seed=code_seed,
                )
                verdict = validate_candidate(doc, seed=code_seed + 100000 + n, refute=True)
                out = ROOT / "research" / "candidates"
                out.mkdir(exist_ok=True)
                # Parameter slugs are not unique: many support pairs can share
                # (n,k,d), and overwriting them would destroy witnesses. Keep a
                # stable code fingerprint in every staging filename.
                code_fp = hashlib.sha256(code_key).hexdigest()[:16]
                stem = f"designed-divisor-{doc['n']}-{doc['k']}-{doc['distance']['d']}-{code_fp}"
                (out / f"{stem}.json").write_text(json.dumps(doc, indent=2) + "\n")
                (out / f"{stem}.verdict.json").write_text(json.dumps(verdict, indent=2) + "\n")
                print(f"  staged {stem}: passed={verdict['passed']} labels={verdict['labels']}", flush=True)
                if verdict["passed"]:
                    staged += 1
    return staged


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=251)
    parser.add_argument("--end", type=int, default=347)
    parser.add_argument("--n", type=int, action="append", help="run only this N; repeatable")
    parser.add_argument("--degree", type=int, action="append", dest="degrees",
                        help="common divisor degree; repeatable")
    parser.add_argument("--multiplier-weight", type=int, default=2)
    parser.add_argument("--multiple-limit", type=int, default=24)
    parser.add_argument("--max-support-weight", type=int, default=8)
    parser.add_argument("--screen-trials", type=int, default=120)
    parser.add_argument("--validate-trials", type=int, default=1200)
    parser.add_argument("--min-screen-d", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20260816)
    parser.add_argument("--all-factors", action="store_true",
                        help="search every factor, not one representative per degree")
    parser.add_argument("--allow-composite", action="store_true",
                        help="also search explicitly requested composite orders")
    args = parser.parse_args()
    ns = args.n or list(range(args.start, args.end + 1))
    if not args.allow_composite:
        ns = [n for n in ns if n > 2 and all(n % p for p in range(2, int(n**0.5) + 1))]
    else:
        ns = [n for n in ns if n > 2]
    degrees = set(args.degrees or [d for d in range(2, 32)])
    staged = run(ns, degrees, args.multiplier_weight, args.multiple_limit,
                 args.max_support_weight, args.screen_trials, args.validate_trials,
                 args.min_screen_d, args.seed, args.all_factors)
    print(f"passed candidates staged: {staged}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
