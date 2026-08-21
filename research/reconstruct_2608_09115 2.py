"""Reconstruct the [[66,20,7]] row of arXiv:2608.09115v1.

The paper's Table II/III gives the final cyclic supports for a,b in
F_2[x]/(x^33 - 1).  The repository's regular cyclic 2BGA constructor produces
H_X=[L(a)|R(b)] and H_Z=[R(b)^T|L(a)^T], with qubits in the two 33-element
blocks.  The paper reports exact d=7; the staged JSON deliberately records the
kit's independently found witness as an upper bound until the trusted gate is
run.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research" / "kit"))
sys.path.insert(0, str(ROOT / "verify"))

from group_algebra import build_2bga, cyclic_product  # noqa: E402
from css import compute_k, verify_css  # noqa: E402
from submit import make_submission, save_submission  # noqa: E402

L = 33
A_SUPPORT = [1, 2, 3, 5, 10, 27, 32]
B_SUPPORT = [0, 1, 3, 4, 5, 7, 13, 15, 22, 24, 30, 32]


def main() -> None:
    mul, elements = cyclic_product(L)
    index = {element: i for i, element in enumerate(elements)}
    a = [index[(i,)] for i in A_SUPPORT]
    b = [index[(i,)] for i in B_SUPPORT]
    HX, HZ = build_2bga(mul, a, b)
    assert HX.shape == (L, 2 * L)
    assert verify_css(HX, HZ)
    assert compute_k(HX, HZ) == 20
    assert max(int(row.sum()) for row in np.vstack((HX, HZ))) == 19

    doc = make_submission(
        HX,
        HZ,
        name="[[66,20,7]] cyclic bicycle code (arXiv:2608.09115v1)",
        construction=(
            "Cyclic bicycle / regular 2BGA over F_2[Z_33]. "
            "A and B are circulants from the pinned support sets in "
            "arXiv:2608.09115v1, Table II/III."
        ),
        authors=["Liangdong Lu", "Guanmin Guo", "Yang Liu", "Ruipan Yang"],
        family="generalized-bicycle",
        references=["arXiv:2608.09115"],
        notes=(
            "Paper reports exact d=7. This staged record uses the repository "
            "kit's independently found logical witnesses and therefore marks "
            "both sides upper_bound until validate_candidate.py is run."
        ),
        date="2026-08-10",
        trials=8000,
        seed=260809115,
    )
    path = ROOT / "research" / "candidates" / "66-20-7-arxiv-2608-09115.json"
    errors = save_submission(doc, str(path))
    if errors:
        raise ValueError(errors)
    print(path)
    print({"n": doc["n"], "k": doc["k"], "d": doc["distance"]["d"],
           "X": doc["distance"]["X"]["value"],
           "Z": doc["distance"]["Z"]["value"]})


if __name__ == "__main__":
    main()
