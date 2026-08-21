#!/usr/bin/env python3
"""Small symmetry-reduced TT Route A (2,2,2) sweep."""
from __future__ import annotations

import hashlib
import itertools
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "research" / "kit"), str(ROOT / "verify")]

from css import compute_k, rref, verify_css  # noqa: E402
from submit import make_submission, save_submission  # noqa: E402
from surrogate import distance_rand  # noqa: E402
from tt import build_tt  # noqa: E402
from validate_candidate import validate_candidate  # noqa: E402


def canonical(triple):
    # Fix identity in every polynomial, quotient by permutation of A/B/C.
    return tuple(sorted(tuple(sorted(t)) for t in triple))


def main() -> None:
    factor_triples = [(2, 2, 2), (2, 2, 3), (2, 3, 3), (2, 2, 5)]
    all_results = []
    for l, m, p in factor_triples:
        nonidentity = [
            t for t in itertools.product(range(l), range(m), range(p))
            if t != (0, 0, 0)
        ]
        supports = [[(0, 0, 0), term] for term in nonidentity]
        seen = set()
        summary = []
        packaged = passed = 0
        for triple in itertools.combinations_with_replacement(supports, 3):
            key = canonical(triple)
            if key in seen:
                continue
            seen.add(key)
            hx, hz = build_tt(l, m, p, *triple)
            assert verify_css(hx, hz)
            k = compute_k(hx, hz)
            if k < 4:
                continue
            d = int(distance_rand(hx, hz, trials=400, seed=20260821 + len(summary)))
            if d < 4:
                continue
            doc = make_submission(
                hx, hz,
                name=f"[[{hx.shape[1]},{k},d<={d}]] TT Route A ({l},{m},{p})",
                construction=(
                    f"Trivariate tricycle over Z_{l} x Z_{m} x Z_{p}; "
                    "identity-fixed two-term supports "
                    f"A={list(triple[0])}, B={list(triple[1])}, C={list(triple[2])}. "
                    "Symmetry-reduced by A/B/C permutation."
                ),
                authors=["@mathysrennela"], family="other",
                references=["arXiv:2508.08191v2"], confidence="upper_bound",
                trials=1200, seed=20260821 + len(summary),
            )
            fingerprint = hashlib.sha256(
                rref(hx)[0].tobytes() + b"|" + rref(hz)[0].tobytes()
            ).hexdigest()[:16]
            stem = f"tt-route-a-{doc['n']}-{k}-{d}-{fingerprint}"
            path = ROOT / "research" / "candidates" / f"{stem}.json"
            save_submission(doc, str(path))
            verdict = validate_candidate(doc, seed=20260821 + len(summary), refute=True)
            path.with_suffix(".verdict.json").write_text(json.dumps(verdict, indent=2) + "\n")
            packaged += 1
            passed += int(verdict.get("passed", False))
            summary.append({"n": doc["n"], "k": doc["k"], "d": doc["distance"]["d"],
                            "fingerprint": fingerprint, "passed": verdict.get("passed"),
                            "labels": verdict.get("labels", [])})
        result = {"factor_triple": [l, m, p], "unique_support_triples": len(seen),
                  "packaged": packaged, "passed": passed, "candidates": summary}
        out = ROOT / "research" / "candidates" / f"tt-route-a-{l}-{m}-{p}-summary.json"
        out.write_text(json.dumps(result, indent=2) + "\n")
        all_results.append({k: result[k] for k in ("factor_triple", "unique_support_triples", "packaged", "passed")})
    print(json.dumps(all_results, indent=2))


if __name__ == "__main__":
    main()
