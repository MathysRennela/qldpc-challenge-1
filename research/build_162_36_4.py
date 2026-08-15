"""Rebuild the [[162,36,4]] bivariate-bicycle candidate through the kit's
canonical submission path (make_submission -> save_submission), with
submittable provenance (authors @mathysrennela, model DeepSeek V4 Flash 0731).

Code: periodic bivariate bicycle on Z_9 x Z_9 (arXiv:2308.07915),
  A monomials = [(0,0),(0,3),(3,3)], B monomials = [(0,0),(3,0),(3,3)].
Recovered from the 2026-07-16 weight-6 BB autosearch sweep (sampler
"enumerate", 400-trial screen, seed 7). Gate status recorded as of the
2026-08-15 board: the code sits on the unrestricted/weight-6 Pareto
frontier (eff = 3.556), undominated.

Run:  uv run python research/build_162_36_4.py
Writes: research/candidates/162-36-4-rebuilt.json (gitignored staging).
"""
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "kit"))

from bb import build_bb                       # noqa: E402
from css import compute_k, verify_css         # noqa: E402
from submit import make_submission, save_submission  # noqa: E402

L, M = 9, 9
A = [(0, 0), (0, 3), (3, 3)]
B = [(0, 0), (3, 0), (3, 3)]

HX, HZ = build_bb(L, M, A, B)
assert verify_css(HX, HZ), "CSS commutation failed"
k = compute_k(HX, HZ)
print(f"HX {HX.shape} HZ {HZ.shape}  k = {k}")

doc = make_submission(
    HX, HZ,
    name="[[162,36,4]] bivariate-bicycle autosearch (Z_9 x Z_9)",
    construction=("Periodic bivariate bicycle on Z_9 x Z_9; "
                  "A monomials=[(0,0),(0,3),(3,3)], "
                  "B monomials=[(0,0),(3,0),(3,3)]."),
    authors=["@mathysrennela"],
    family="bivariate-bicycle",
    references=["arXiv:2308.07915"],
    confidence="upper_bound",
    trials=8000, seed=7,
)
print("d =", doc["distance"]["d"],
      "| X:", doc["distance"]["X"]["value"],
      "| Z:", doc["distance"]["Z"]["value"])

out = os.path.join(_HERE, "candidates", "162-36-4-rebuilt.json")
errs = save_submission(doc, out)
print("schema errors:", errs or "none")
print("wrote:", out)