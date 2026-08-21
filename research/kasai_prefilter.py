#!/usr/bin/env python3
"""Structural prefilter for pair-partition CPM (Kasai) candidates.

Implements route 4 of
fieldnotes/2026-08-20-optional-future-research-board-advancement.md: "Finish
the structural prefilter for mixed collisions, 4-cycles, and 6-cycles,
calibrating it against named table rows and known failures before
reconstructing new witnesses."

WHAT THIS DOES
--------------
For each bundled Kasai instance, the script rebuilds the exact H_X and H_Z
using the SAME construction the trusted bundle audits
(``kasai-repo/scripts/construct_pair_partition_cpm_css_codes.py``: pair-
partition array M over Z_L, exponent arrays E and D over F_P, CPM blocks
C(e_jl) and C(d_jl)).  It then computes structural features:

  * ``four_cycles`` / ``six_cycles`` -- check-pair support intersections of
    size >= 2 / >= 3 (the bundle's ``check_intersection_triangles`` invariant
    is exactly the length-6 count),
  * ``mixed_collisions`` -- pairs (X-check, Z-check) sharing a qubit (a cheap
    obstruction that usually forces a small witness),
  * ``max_check_weight`` and the check-weight histogram,
  * the exact RREF ``fingerprint`` (same convention as the verifier's
    duplicate check).

The point is NOT to certify distance -- this is explicitly a *prefilter*.
A candidate may be rejected cheaply by these counts; it may NOT be promoted.
Every retained reconstruction still goes through research/kit/submit.py and
the trusted validator.

CALIBRATION
-----------
* instance list from ``data/reconstructed_instances/summary.json`` -- the
  named table rows, incl. the named failures ``qc_590_240_12`` and
  ``qc_1524_766_14``;
* the retained forbidden-pattern bank for ``qc_848_430_18``
  (``data/forbidden/qc_848_430_18_forbidden_patterns.json``, patterns mined
  from rejected or neighboring candidates -- search prefilters, NOT distance
  certificates).

OUTPUT
------
Writes ``research/candidates/kasai-prefilter-calibration.json`` with the
per-instance features and forbidden-bank status, and prints a compact table.
This is a calibration artifact, not a submission.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "research" / "kit"), str(ROOT / "verify")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from css import compute_k, verify_css  # noqa: E402
from search import fingerprint  # noqa: E402

KASAI_REPO = ROOT / "research" / "candidates" / "pp_cpm" / "kasai-repo"


# ---------------------------------------------------------------------------
#  Reconstruction helpers (mirror the bundle's construction script)
# ---------------------------------------------------------------------------
def cpm_rows(exponents, p):
    """Sparse row supports of the CPM block matrix C(s): for each of the J
    block rows and each shift a in 0..p-1, the support is
    L*((a - s) % p) + col over the L columns."""
    j = len(exponents)
    l = len(exponents[0])
    rows = []
    for block_row in range(j):
        for a in range(p):
            rows.append(
                sorted(l * ((a - exponents[block_row][col]) % p) + col
                       for col in range(l))
            )
    return rows


def build_instance(instance_dir: Path):
    """Rebuild (HX, HZ) of a bundled instance from reconstructed_exponents.json.

    The JSON carries the instance's M/E/D arrays and parameters; we reuse the
    exact CPM-blocks convention of the trusted bundle so the reconstruction
    is the one the bundle itself audits.
    """
    data = json.loads(instance_dir.read_text())
    p = int(data["parameters"]["P"])
    n = int(data["parameters"]["n"])
    e = [[int(x) % p for x in row] for row in data["E"]]
    d = [[int(x) % p for x in row] for row in data["D"]]
    hx_rows = cpm_rows(e, p)
    hz_rows = cpm_rows(d, p)
    HX = np.zeros((len(hx_rows), n), dtype=np.int8)
    HZ = np.zeros((len(hz_rows), n), dtype=np.int8)
    for i, row in enumerate(hx_rows):
        HX[i, row] = 1
    for i, row in enumerate(hz_rows):
        HZ[i, row] = 1
    return HX, HZ, {"P": p, "n": n}


# ---------------------------------------------------------------------------
#  Structural features
# ---------------------------------------------------------------------------
def cycle_intersections(H):
    """(c4, c6): number of check pairs with support intersection >= 2 / >= 3.
    The bundle's ``check_intersection_triangles`` counts the >=3 case."""
    rows = [np.nonzero(r % 2)[0].tolist() for r in H]
    c4 = c6 = 0
    for i in range(len(rows)):
        si = set(rows[i])
        for j in range(i + 1, len(rows)):
            k = len(si & set(rows[j]))
            if k >= 2:
                c4 += 1
            if k >= 3:
                c6 += 1
    return c4, c6


def mixed_collisions(HX, HZ):
    """Number of (X-check, Z-check) pairs that share at least one qubit."""
    return int(((HX @ HZ.T) > 0).sum())


def weight_hist(H):
    return dict(sorted(Counter(int(r.sum()) for r in H).items()))


def features(HX, HZ, name, paper_d=None):
    c4x, c6x = cycle_intersections(HX)
    c4z, c6z = cycle_intersections(HZ)
    return {
        "instance": name,
        "n": int(HX.shape[1]),
        "k": int(compute_k(HX, HZ)),
        "css": bool(verify_css(HX, HZ)),
        "four_cycles": c4x + c4z,
        "six_cycles": c6x + c6z,
        "mixed_collisions": mixed_collisions(HX, HZ),
        "max_check_weight": max(
            max((int(r.sum()) for r in HX), default=0),
            max((int(r.sum()) for r in HZ), default=0)),
        "hx_weight_hist": weight_hist(HX),
        "hz_weight_hist": weight_hist(HZ),
        "fingerprint": fingerprint(HX, HZ),
        "paper_d": paper_d,
    }


# ---------------------------------------------------------------------------
#  Forbidden bank
# ---------------------------------------------------------------------------
def check_forbidden(patterns):
    """Summarize the retained forbidden-pattern bank (metadata only)."""
    pats = patterns.get("patterns", [])
    weights = Counter(p.get("weight") for p in pats)
    return {
        "bank_size": len(pats),
        "weight_hist": dict(sorted(weights.items())),
        "schema": patterns.get("schema"),
        "note": ("Retained search-prefilter bank; NOT a distance certificate. "
                 "Patterns are mined from rejected or neighboring candidates "
                 "and used only to cheaply reject lookalikes."),
    }


def main():
    inst_dir = KASAI_REPO / "data" / "reconstructed_instances"
    summary = json.loads((inst_dir / "summary.json").read_text())
    rows = []
    for item in summary:
        name = item["instance"]
        path = inst_dir / name / "reconstructed_exponents.json"
        try:
            HX, HZ, _meta = build_instance(path)
        except Exception as exc:  # noqa: BLE001
            rows.append({"instance": name, "error": str(exc)})
            print(f"{name}: ERROR {exc}")
            continue
        feat = features(HX, HZ, name, paper_d=item.get("d"))
        rows.append(feat)
        print(f"{name}: n={feat['n']} k={feat['k']} css={feat['css']} "
              f"4cyc={feat['four_cycles']} 6cyc={feat['six_cycles']} "
              f"mixed={feat['mixed_collisions']} "
              f"wmax={feat['max_check_weight']}")

    fb_path = (KASAI_REPO / "data" / "forbidden" /
               "qc_848_430_18_forbidden_patterns.json")
    fb = check_forbidden(json.loads(fb_path.read_text())) if fb_path.exists() else {}

    result = {
        "instances": rows,
        "forbidden_bank": fb,
        "note": ("Structural prefilter calibration only. Distances reported "
                 "are the paper's published values; no new distance claim is "
                 "made. Feature-based rejection is cheap; promotion is NOT "
                 "allowed without submit + validator."),
    }
    dest = ROOT / "research" / "candidates" / "kasai-prefilter-calibration.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, indent=2) + "\n")
    print(f"wrote {dest}")


if __name__ == "__main__":
    main()