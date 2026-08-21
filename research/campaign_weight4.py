"""Bounded weight-4 multivariate-bicycle campaign.

This uses the repository BB constructor with two terms per polynomial. The
allowed terms are the three one-parameter families x^a, y^b, and (xy)^c,
which is the small-support multivariate-bicycle search space. All finalists
are persisted through submit.make_submission before validation.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research" / "kit"))
sys.path.insert(0, str(ROOT / "verify"))

from bb import build_bb  # noqa: E402
from css import compute_k, verify_css  # noqa: E402
from search import fingerprint, screen  # noqa: E402
from submit import make_submission, save_submission  # noqa: E402
from validate_candidate import validate_candidate  # noqa: E402

DIMS = [(5, 6), (6, 6), (7, 6), (8, 6), (9, 7), (10, 7), (11, 8), (12, 8)]
SAMPLES_PER_DIM = 60
SCREEN_TRIALS = 160
PACKAGE_TRIALS = 1600
SEED = 20260816


def support_pool(l: int, m: int) -> list[tuple[int, int]]:
    terms = {(0, 0)}
    terms.update((a, 0) for a in range(1, l))
    terms.update((0, b) for b in range(1, m))
    terms.update((a % l, a % m) for a in range(1, max(l, m)))
    return sorted(terms)


def candidates():
    rng = np.random.default_rng(SEED)
    for l, m in DIMS:
        pool = support_pool(l, m)
        for sample in range(SAMPLES_PER_DIM):
            # Identity-normalized supports; the second term is drawn from the
            # multivariate x/y/xy families, and A/B are independently chosen.
            a = [(0, 0), pool[int(rng.integers(1, len(pool)))] ]
            b = [(0, 0), pool[int(rng.integers(1, len(pool)))] ]
            spec = {
                "family": "multivariate-bicycle-weight4",
                "dims": [l, m], "sample": sample, "seed": SEED,
                "A": [list(x) for x in a], "B": [list(x) for x in b],
            }
            HX, HZ = build_bb(l, m, a, b)
            yield spec, HX, HZ


def main() -> int:
    records, audit = screen(
        candidates(), min_k=2, min_d=3, trials=SCREEN_TRIALS,
        seed=SEED, keep=20, family="multivariate-bicycle",
        campaign="weight4-mvb-2026-08-16", round_id=1, return_audit=True,
    )
    out = ROOT / "research" / "candidates"
    out.mkdir(parents=True, exist_ok=True)
    (out / "weight4-mvb-screen.json").write_text(
        json.dumps({"audit": audit, "records": records}, indent=2) + "\n"
    )

    packaged = []
    for rank, record in enumerate(records[:5], 1):
        spec = record["spec"]
        l, m = spec["dims"]
        HX, HZ = build_bb(l, m, spec["A"], spec["B"])
        assert verify_css(HX, HZ)
        k = compute_k(HX, HZ)
        n = int(HX.shape[1])
        doc = make_submission(
            HX, HZ,
            name=f"[[{n},{k},?]] weight-4 multivariate-bicycle finalist {rank}",
            construction=(
                f"Two-term multivariate bicycle on Z_{l} x Z_{m}; "
                f"A={spec['A']}, B={spec['B']}; identity-normalized x/y/xy supports; "
                f"screen seed={SEED}, sample={spec['sample']}."
            ),
            authors=["@mathysrennela"], family="bivariate-bicycle",
            references=["arXiv:2406.19151"], confidence="upper_bound",
            trials=PACKAGE_TRIALS, seed=SEED + rank,
            notes=(f"Screened at {SCREEN_TRIALS} trials; package witness search "
                   f"used {PACKAGE_TRIALS} trials. Distance is an upper bound."),
        )
        path = out / f"weight4-mvb-finalist-{rank}-{n}-{k}.json"
        save_submission(doc, str(path))
        verdict = validate_candidate(doc, seed=SEED + 100000 + rank, refute=True)
        (out / f"weight4-mvb-finalist-{rank}-{n}-{k}.verdict.json").write_text(
            json.dumps(verdict, indent=2) + "\n"
        )
        packaged.append({
            "rank": rank, "screen": record, "distance": doc["distance"],
            "path": str(path.relative_to(ROOT)), "verdict": verdict,
            "fingerprint": fingerprint(HX, HZ),
        })
    (out / "weight4-mvb-results.json").write_text(
        json.dumps({"audit": audit, "packaged": packaged}, indent=2) + "\n"
    )
    print(json.dumps({"audit": audit, "packaged": packaged}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
