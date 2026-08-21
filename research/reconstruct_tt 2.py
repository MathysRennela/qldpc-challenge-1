"""Reconstruct selected TT examples from arXiv:2508.08191v2.

This script is a calibration pass, not a board submission. It rebuilds the
paper's explicit polynomial examples, packages side witnesses through the
research kit, and writes JSON only under the ignored research/candidates/
working directory.

Run from the repository root with:
    uv run python research/reconstruct_tt.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research" / "kit"))
sys.path.insert(0, str(ROOT / "verify"))

from css import compute_k, verify_css  # noqa: E402
from submit import make_submission, save_submission  # noqa: E402
from tt import build_tt  # noqa: E402


# Terms are exponent triples (x, y, z).  These are transcribed from Tables 1
# and 3 of arXiv:2508.08191v2.  The first three are the main calibration set;
# the last two exercise the (2,2,2) CCZ family.
EXAMPLES = [
    {
        "slug": "72-6-6",
        "expected": (72, 6),
        "dims": (4, 3, 2),
        "A": [(0, 0, 0), (0, 1, 0), (1, 2, 0)],
        "B": [(0, 0, 0), (0, 1, 1), (2, 2, 0)],
        "C": [(0, 0, 0), (1, 2, 1), (2, 1, 0)],
        "paper_d": "dX=12, dZ=6",
    },
    {
        "slug": "180-12-8",
        "expected": (180, 12),
        "dims": (5, 4, 3),
        "A": [(0, 0, 0), (2, 3, 1), (4, 1, 0)],
        "B": [(0, 0, 0), (3, 0, 0), (4, 0, 2)],
        "C": [(0, 0, 0), (3, 3, 0), (4, 1, 2)],
        "paper_d": "dX=20, dZ=8",
    },
    {
        "slug": "432-12-12",
        "expected": (432, 12),
        "dims": (6, 6, 4),
        "A": [(0, 0, 0), (1, 1, 3), (3, 4, 2)],
        "B": [(0, 0, 0), (3, 1, 2), (3, 2, 3)],
        "C": [(0, 0, 0), (4, 3, 3), (5, 0, 2)],
        "paper_d": "dX<=36, dZ=12",
    },
    {
        "slug": "48-3-4",
        "expected": (48, 3),
        "dims": (4, 2, 2),
        "A": [(0, 0, 0), (1, 0, 0)],
        "B": [(0, 0, 0), (1, 0, 1)],
        "C": [(0, 0, 0), (1, 1, 0)],
        "paper_d": "dX=8, dZ=4",
    },
    {
        "slug": "90-3-5",
        "expected": (90, 3),
        "dims": (5, 3, 2),
        "A": [(0, 0, 0), (1, 0, 0)],
        "B": [(0, 0, 0), (1, 1, 0)],
        "C": [(0, 0, 0), (2, 2, 1)],
        "paper_d": "dX=15, dZ=5",
    },
]


def main() -> None:
    out_dir = ROOT / "research" / "candidates"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = []

    for item in EXAMPLES:
        l, m, p = item["dims"]
        HX, HZ = build_tt(l, m, p, item["A"], item["B"], item["C"])
        n = HX.shape[1]
        k = compute_k(HX, HZ)
        max_weight = max(
            max(int(row.sum()) for row in HX),
            max(int(row.sum()) for row in HZ),
        )
        expected_n, expected_k = item["expected"]
        assert n == expected_n, (item["slug"], n, expected_n)
        assert k == expected_k, (item["slug"], k, expected_k)
        assert verify_css(HX, HZ)

        doc = make_submission(
            HX,
            HZ,
            name=f"[[{n},{k},?]] TT calibration {item['slug']}",
            construction=(
                "Trivariate tricycle code from arXiv:2508.08191v2, "
                f"G=Z_{l} x Z_{m} x Z_{p}; A={item['A']}, "
                f"B={item['B']}, C={item['C']}."
            ),
            authors=["Abraham Jacob", "Campbell McLauchlan", "Dan E. Browne"],
            family="other",
            references=["arXiv:2508.08191v2"],
            confidence="upper_bound",
            trials=300,
            seed=17,
        )
        path = out_dir / f"tt-{item['slug']}.json"
        save_submission(doc, str(path))
        summary.append({
            "slug": item["slug"],
            "n": n,
            "k": k,
            "max_check_weight": max_weight,
            "paper_distance": item["paper_d"],
            "observed_distance": doc["distance"],
            "staged": os.fspath(path.relative_to(ROOT)),
        })

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
