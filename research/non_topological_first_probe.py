#!/usr/bin/env python3
"""Small co-designed bilayer local-2D calibration probe."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research" / "local2d"))
sys.path.insert(0, str(ROOT / "research" / "kit"))
sys.path.insert(0, str(ROOT / "verify"))

from planar import build_open_directional, grid_coordinates  # noqa: E402
from submit import make_submission, save_submission  # noqa: E402
from validate_candidate import validate_candidate  # noqa: E402


if __name__ == "__main__":
    results = []
    for Lx, Ly in ((6, 8), (8, 8), (8, 10)):
        hx, hz = build_open_directional(Lx, Ly)
        coordinates = grid_coordinates(Lx, Ly)
        n = 2 * Lx * Ly
        doc = make_submission(
            hx,
            hz,
            name=f"[[{n},8,d<=?]] flagship planar bilayer calibration {Lx}x{Ly}",
            construction=(
                "Open-boundary planar bivariate-bicycle calibration using the "
                "validated flagship supports f=x+x^2+y^2, g=1+x^2y+x^2y^2 "
                f"on an {Lx}x{Ly} bilayer grid."
            ),
            authors=["@mathysrennela"],
            family="bivariate-bicycle",
            references=["arXiv:2504.08887"],
            confidence="upper_bound",
            coordinates=coordinates,
            layers=2,
            trials=8000,
            seed=20260820 + Lx * 100 + Ly,
        )
        out = ROOT / "research" / "candidates" / f"non-topological-flagship-{n}-{Lx}x{Ly}.json"
        save_submission(doc, str(out))
        verdict = validate_candidate(doc, seed=20260820 + Lx * 100 + Ly, refute=True)
        (out.with_suffix(".verdict.json")).write_text(json.dumps(verdict, indent=2) + "\n")
        results.append({"size": [Lx, Ly], "n": n, "k": doc["k"], "d": doc["distance"]["d"],
                       "passed": verdict.get("passed"), "labels": verdict.get("labels", [])})
    print(json.dumps(results, indent=2))
