"""Reconstruct [[234,28,18]] from arXiv:2608.08996v1 Supplementary Information.

The paper's free-action host is Z_13 x Z_9, so this row is an ordinary abelian
2BGA and can be assembled by the repository's bivariate-bicycle constructor.
The paper reports an exact MILP distance; the staged document retains the
repository's witness-backed upper-bound confidence.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research" / "kit"))
sys.path.insert(0, str(ROOT / "verify"))

from bb import build_bb  # noqa: E402
from css import compute_k, verify_css  # noqa: E402
from submit import make_submission, save_submission  # noqa: E402

L, M = 13, 9
A = [(0, 0), (0, 2), (0, 8), (4, 4), (6, 8)]
B = [(2, 8), (5, 4), (10, 2), (11, 5), (12, 0)]


def main() -> None:
    HX, HZ = build_bb(l=L, m=M, A_terms=A, B_terms=B)
    assert HX.shape == (L * M, 2 * L * M)
    assert verify_css(HX, HZ)
    assert compute_k(HX, HZ) == 28
    max_weight = max(int(row.sum()) for row in np.vstack((HX, HZ)))
    assert max_weight <= 32
    print({"n": HX.shape[1], "k": compute_k(HX, HZ), "max_check_weight": max_weight})

    doc = make_submission(
        HX,
        HZ,
        name="[[234,28,18]] abelian lifted product (arXiv:2608.08996v1)",
        construction=(
            "Free-action abelian 2BGA / lifted product over Z_13 x Z_9, "
            "with A support {(0,0),(0,2),(0,8),(4,4),(6,8)} and B support "
            "{(2,8),(5,4),(10,2),(11,5),(12,0)}, from the Supplementary "
            "Information construction data for arXiv:2608.08996v1."
        ),
        authors=["Dongheng Qian", "Tianyi Li"],
        family="lifted-product",
        references=["arXiv:2608.08996"],
        notes=(
            "The paper reports exact d=18 by MILP. This staged record uses "
            "repository witnesses and therefore retains upper_bound confidence "
            "until trusted certification."
        ),
        date="2026-08-10",
        trials=8000,
        seed=260808996,
    )
    path = ROOT / "research" / "candidates" / "234-28-18-arxiv-2608-08996.json"
    errors = save_submission(doc, str(path))
    if errors:
        raise ValueError(errors)
    print(path)


if __name__ == "__main__":
    main()
