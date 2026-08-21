#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research" / "kit"))
sys.path.insert(0, str(ROOT / "verify"))

from css import compute_k, verify_css
from group_algebra import build_2bga, cyclic_product
from submit import make_submission, save_submission
from validate_candidate import validate_candidate

N = 333
A = (0, 1, 7, 18, 35, 61, 83, 87, 89, 99, 107, 108, 136, 142, 145, 194, 196, 214, 215, 226, 233, 243, 244, 252, 287, 309, 322, 325)
B = (0, 1, 8, 17, 19, 21, 24, 58, 93, 107, 132, 136, 145, 147, 149, 152, 165, 196, 198, 205, 206, 222, 242, 260, 263, 273, 298, 312, 324, 326)

mul, _ = cyclic_product(N)
HX, HZ = build_2bga(mul, list(A), list(B))
assert verify_css(HX, HZ)
k = compute_k(HX, HZ)
assert k == 150

# make_submission performs the trusted-kit witness search and embeds both witnesses.
doc = make_submission(
    HX, HZ,
    name="[[666,150,d<=?]] Z_333 divisor-preserving high-weight mutation",
    construction=(
        "Cyclic generalized bicycle on Z_333, H_X=[A|B], H_Z=[B^T|A^T]. "
        f"Divisor-preserving support mutation with A={list(A)}, B={list(B)}."
    ),
    authors=["@mathysrennela"],
    family="generalized-bicycle",
    references=["arXiv:2111.03654", "arXiv:2306.16400"],
    confidence="upper_bound",
    trials=300,
    seed=20260817,
    notes="Screened at 40 trials with an apparent upper bound near 98; this is an independent validation attempt."
)

out = ROOT / "research" / "candidates"
key = hashlib.sha256((repr(A) + "|" + repr(B)).encode()).hexdigest()[:16]
stem = f"z333-alt-666-150-{doc['distance']['d']}-{key}"
path = out / f"{stem}.json"
save_submission(doc, str(path))
verdict = validate_candidate(doc, seed=20260817, refute=True)
verdict_path = out / f"{stem}.verdict.json"
verdict_path.write_text(json.dumps(verdict, indent=2) + "\n")
print(json.dumps({"path": str(path.relative_to(ROOT)), "distance": doc["distance"], "verdict": verdict}, indent=2))
