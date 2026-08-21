"""Reconstruct explicit cyclic rows from arXiv:2608.09115v1.

Source: Tables II/III (support sets are exponents in F_2[x]/(x^l - 1)).
This script only stages candidate JSON documents; it never writes codes/.
Paper distances are reported as exact in the source, while staged documents use
repository witness-backed upper bounds until the trusted gate/certifier says more.
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

# (name, l, supp(a), supp(b), paper distance, source location)
ROWS = [
    (
        "[[90,18,8]]", 45,
        [0, 1, 2, 3, 4, 6, 8, 9, 12, 15, 16, 17, 20, 21, 36, 39, 40, 41, 42, 44],
        [0, 1, 2, 3, 4, 5, 8, 9, 27, 30, 31, 32, 34, 35, 36, 37, 39, 41],
        8, "Table III",
    ),
    (
        "[[90,20,7]]", 45,
        [0, 1, 3, 5, 7, 8, 9, 10, 36, 39, 40, 42],
        [0, 1, 2, 4, 5, 8, 10, 21, 22, 23, 25, 26, 29, 30, 32, 34, 35, 38, 40],
        7, "Table III",
    ),
    (
        "[[42,16,6]]", 21,
        [0, 1, 2, 8, 9, 11, 17, 18, 20],
        [0, 1, 2, 3, 4, 6, 8, 11, 12, 14, 18, 19, 20],
        6, "Table III",
    ),
    (
        "[[42,14,6]]", 21,
        [1, 3, 5, 6, 7, 9, 12, 13, 14, 16, 17, 19],
        [1, 2, 4, 6, 11, 12, 13, 14, 15, 18, 19, 20],
        6, "Table III",
    ),
    (
        "[[70,16,7]]", 35,
        [0, 1, 3, 5, 6, 8, 10, 11, 13, 15, 16, 18, 21, 23, 24, 25, 26, 28, 29, 30],
        [1, 2, 3, 5, 6, 8, 11, 13, 14, 15, 16, 18, 19, 20, 29, 30, 32, 34],
        7, "Table III",
    ),
    (
        "[[54,16,6]]", 27,
        [0, 1, 2, 3, 4, 5, 6, 8, 25],
        [0, 1, 3, 5, 6, 8, 11, 22, 25],
        6, "Table III",
    ),
    (
        "[[170,18,8]]", 85,
        [0, 3, 4, 5, 6, 7, 8, 46, 49, 50, 51, 52, 53, 54, 59, 62, 63, 64, 65, 66, 67, 72, 75, 76, 77, 78, 79, 80],
        [0, 3, 4, 5, 6, 7, 8, 46, 49, 50, 51, 52, 53, 54, 61, 64, 65, 66, 67, 68, 69, 70, 73, 74, 75, 76, 77, 78],
        8, "Table III",
    ),
    (
        "[[170,18,7]]", 85,
        [0, 1, 3, 9, 22, 23, 25, 31, 38, 39, 41, 47, 69, 70, 72, 78],
        [0, 1, 3, 9, 11, 12, 14, 20, 22, 23, 25, 31],
        7, "Table III",
    ),
    (
        "[[170,16,7]]", 85,
        [0, 1, 6, 7, 8, 10, 12, 13, 45, 46, 50, 52, 53],
        [0, 1, 6, 7, 8, 10, 12, 13, 22, 23, 27, 29, 30, 68, 69, 73, 75, 76],
        7, "Table III",
    ),
    (
        "[[170,18,6]]", 85,
        [0, 1, 3, 9, 39, 40, 42, 46, 47, 48, 49, 55],
        [0, 1, 3, 9, 31, 32, 34, 40, 54, 55, 57, 63],
        6, "Table III",
    ),
    (
        "[[170,10,8]]", 85,
        [0, 1, 3, 5, 8, 78, 81, 83],
        [0, 1, 10, 76],
        8, "Table III",
    ),
    (
        "[[170,10,6]]", 85,
        [0, 5, 11, 16, 74, 79],
        [0, 5, 27, 32, 58, 63],
        6, "Table III",
    ),
    (
        "[[170,10,7]]", 85,
        [0, 1, 5, 72, 76, 77],
        [0, 5, 36, 41, 72, 77],
        7, "Table III",
    ),
]


def main() -> None:
    for name, l, a_support, b_support, paper_d, location in ROWS:
        HX, HZ = build_bb(
            l=l,
            m=1,
            A_terms=[(a, 0) for a in a_support],
            B_terms=[(b, 0) for b in b_support],
        )
        assert HX.shape == (l, 2 * l)
        assert verify_css(HX, HZ)
        k = compute_k(HX, HZ)
        max_weight = max(int(row.sum()) for row in np.vstack((HX, HZ)))
        print(f"{name}: k={k}, max_check_weight={max_weight}")
        if max_weight > 32:
            print("  BLOCKED: raw maximum check weight exceeds repository cap")
            continue
        if k != int(name.split(",")[1]):
            print("  BLOCKED: reconstructed k disagrees with paper row")
            continue
        doc = make_submission(
            HX,
            HZ,
            name=f"{name} cyclic bicycle code (arXiv:2608.09115v1)",
            construction=(
                f"Cyclic bicycle over F_2[Z_{l}], with circulant supports "
                f"a={a_support} and b={b_support}, from {location} of "
                "arXiv:2608.09115v1."
            ),
            authors=["Liangdong Lu", "Guanmin Guo", "Yang Liu", "Ruipan Yang"],
            family="generalized-bicycle",
            references=["arXiv:2608.09115"],
            notes=(
                f"The paper reports exact d={paper_d}. This staged record keeps "
                "the repository's witness-backed distance evidence as upper_bound "
                "until trusted certification."
            ),
            date="2026-08-10",
            trials=8000,
            seed=260809115 + l + len(a_support),
        )
        path = ROOT / "research" / "candidates" / (name[2:-2].replace(",", "-") + "-arxiv-2608-09115.json")
        errors = save_submission(doc, str(path))
        if errors:
            raise ValueError(f"{name}: {errors}")
        print(f"  staged {path}")


if __name__ == "__main__":
    main()
