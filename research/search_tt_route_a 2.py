"""Bounded Route A search for weight-6 (2,2,2) TT codes.

This is an exploratory campaign script. It persists the complete screening
archive and packages the top finalists through submit.make_submission, so no
witness found for a finalist is discarded.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research" / "kit"))
sys.path.insert(0, str(ROOT / "verify"))

from css import compute_k, verify_css  # noqa: E402
from search import screen  # noqa: E402
from submit import make_submission, save_submission  # noqa: E402
from tt import build_tt  # noqa: E402


# Small and medium factor triples, all within the verifier's n <= 700 cap.
DIMENSIONS = [
    (3, 3, 2),
    (4, 3, 2),
    (5, 3, 2),
    (4, 4, 2),
    (5, 4, 2),
    (6, 4, 2),
    (3, 3, 3),
    (4, 3, 3),
    (5, 3, 3),
    (4, 4, 3),
]
SAMPLES_PER_DIMENSION = 20
SCREEN_TRIALS = 120
PACKAGE_TRIALS = 1200
SEED = 20260816


def _terms(rng, dims):
    """Return one identity-normalized weight-2 polynomial support."""
    identity = (0, 0, 0)
    other = tuple(int(rng.integers(0, order)) for order in dims)
    while other == identity:
        other = tuple(int(rng.integers(0, order)) for order in dims)
    return [identity, other]


def candidates():
    rng = np.random.default_rng(SEED)
    for dims in DIMENSIONS:
        l, m, p = dims
        for sample in range(SAMPLES_PER_DIMENSION):
            A = _terms(rng, dims)
            B = _terms(rng, dims)
            C = _terms(rng, dims)
            spec = {
                "family": "tt-route-a-222",
                "dims": list(dims),
                "sample": sample,
                "seed": SEED,
                "A": [list(x) for x in A],
                "B": [list(x) for x in B],
                "C": [list(x) for x in C],
            }
            HX, HZ = build_tt(l, m, p, A, B, C)
            yield spec, HX, HZ


def main():
    records, audit = screen(
        candidates(),
        min_k=4,
        min_d=3,
        trials=SCREEN_TRIALS,
        seed=SEED,
        keep=20,
        family="trivariate-tricycle",
        campaign="tt-route-a-222-2026-08-16",
        round_id=1,
        return_audit=True,
    )
    out_dir = ROOT / "research" / "candidates"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "tt-route-a-screen.json").write_text(
        json.dumps({"audit": audit, "records": records}, indent=2) + "\n"
    )

    packaged = []
    for rank, record in enumerate(records[:5], start=1):
        spec = record["spec"]
        l, m, p = spec["dims"]
        HX, HZ = build_tt(l, m, p, spec["A"], spec["B"], spec["C"])
        assert verify_css(HX, HZ)
        k = compute_k(HX, HZ)
        n = HX.shape[1]
        doc = make_submission(
            HX,
            HZ,
            name=f"[[{n},{k},?]] TT Route A finalist {rank}",
            construction=(
                "Trivariate tricycle Route A (2,2,2) search on "
                f"Z_{l} x Z_{m} x Z_{p}; A={spec['A']}, "
                f"B={spec['B']}, C={spec['C']}; seed={SEED}, sample={spec['sample']}."
            ),
            authors=["@mathysrennela"],
            family="other",
            references=["arXiv:2508.08191v2"],
            notes=(
                "Screened with the research surrogate at "
                f"{SCREEN_TRIALS} trials; finalist packaging used "
                f"{PACKAGE_TRIALS} trials. Screening distance is an upper bound."
            ),
            confidence="upper_bound",
            trials=PACKAGE_TRIALS,
            seed=SEED + rank,
        )
        path = out_dir / f"tt-route-a-finalist-{rank}-{n}-{k}.json"
        save_submission(doc, str(path))
        packaged.append({
            "rank": rank,
            "screen": record,
            "packaged": doc["distance"],
            "path": str(path.relative_to(ROOT)),
        })

    (out_dir / "tt-route-a-packaged.json").write_text(
        json.dumps({"audit": audit, "packaged": packaged}, indent=2) + "\n"
    )
    print(json.dumps({"audit": audit, "top": packaged}, indent=2))


if __name__ == "__main__":
    main()
