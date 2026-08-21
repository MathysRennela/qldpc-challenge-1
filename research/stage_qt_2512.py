"""Stage the quantum-Tanner candidates from arXiv:2512.20532.

Source: the authors' published parity-check matrices (auxiliary files of
arXiv:2512.20532, "Small quantum Tanner codes from left-right Cayley
complexes", Leverrier-Rozendaal-Zemor). We read the Matrix Market HX/HZ pairs
directly from the arXiv e-print tarball rather than reconstructing the lift,
so the staged codes are faithful to the paper.

Unattended autoresearch: candidates are staged under research/candidates/
(gitignored working output) and run through the trusted gate
(verify/validate_candidate.py). Nothing is written to codes/ and no PR is
opened.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "kit"))
sys.path.insert(0, os.path.join(HERE, "..", "verify"))

from submit import make_submission, save_submission  # noqa: E402
from validate_candidate import validate_candidate  # noqa: E402

# arXiv e-print tarball, extracted into the scratch dir .work-qt/
SRC = os.path.join(HERE, "..", ".work-qt", "633x633")

# (name, group, n, k, d_paper, HX file, HZ file)
INSTANCES = [
    ("[[216,8,18]] quantum Tanner C6", "C6", 216, 8, 18,
     "HX_C6_216_8_18.mtx", "HZ_C6_216_8_18.mtx"),
    ("[[432,20,22]] quantum Tanner C6xC2", "C6xC2", 432, 20, 22,
     "HX_C6C2_432_20_22.mtx", "HZ_C6C2_432_20_22.mtx"),
    ("[[576,28,24]] quantum Tanner C4rC4", "C4rC4", 576, 28, 24,
     "HX_C4rC4_576_28_24.mtx", "HZ_C4rC4_576_28_24.mtx"),
]


def read_mtx(path):
    """Read a Matrix Market coordinate file into a dense int8 GF(2) matrix."""
    with open(path) as f:
        lines = [ln for ln in f if not ln.startswith("%")]
    rows, cols, _ = map(int, lines[0].split())
    M = np.zeros((rows, cols), dtype=np.int8)
    for ln in lines[1:]:
        parts = ln.split()
        if not parts:
            continue
        r, c = int(parts[0]) - 1, int(parts[1]) - 1
        M[r, c] = 1
    return M


def main():
    outdir = os.path.join(HERE, "candidates")
    os.makedirs(outdir, exist_ok=True)
    summary = []
    for name, group, n, k, d_paper, hxf, hzf in INSTANCES:
        hx = read_mtx(os.path.join(SRC, hxf))
        hz = read_mtx(os.path.join(SRC, hzf))
        assert hx.shape[1] == n and hz.shape[1] == n, (hx.shape, hz.shape)

        doc = make_submission(
            hx,
            hz,
            name=name,
            construction=(
                f"Quantum Tanner code on a left-right Cayley complex over {group}, "
                "A- and B-side local codes both [6,3,3] shortened Hamming; "
                "parity-check matrices taken verbatim from the arXiv:2512.20532 "
                "auxiliary files (633x633/)."
            ),
            authors=["@mathysrennela"],
            family="quantum-tanner",
            references=["arXiv:2512.20532"],
            notes=(
                f"Paper reports [[{n},{k},<={d_paper}]] (QDistRnd upper bound, "
                "50k-3M trials). This record is witness-backed upper_bound; the "
                "true distance may be lower. Reconstructed from the authors' "
                "published .mtx matrices, not a parameter claim."
            ),
            confidence="upper_bound",
            trials=8000,
            seed=251220532,
        )
        base = f"{n}-{k}-{d_paper}-arxiv-2512-20532.json"
        out = os.path.join(outdir, base)
        errs = save_submission(doc, out)
        print(f"schema errors for {base}:", errs or "none")

        verdict = validate_candidate(doc)
        vout = out.replace(".json", ".verdict.json")
        with open(vout, "w") as f:
            json.dump(verdict, f, indent=2)

        wc = verdict["candidate"].get("weight_class")
        lc = verdict["candidate"].get("locality_class")
        eff = doc["k"] * doc["distance"]["d"] ** 2 / doc["n"]
        summary.append({
            "file": base,
            "n": doc["n"], "k": doc["k"], "d": doc["distance"]["d"],
            "paper_d": d_paper, "w_class": wc, "locality": lc,
            "eff": round(eff, 2),
            "passed": verdict["passed"],
            "labels": verdict["labels"],
        })
        print(f"  passed={verdict['passed']}  {verdict['labels']}")

    print("\n=== SUMMARY ===")
    for s in summary:
        print(f"[[{s['n']},{s['k']},{s['d']}]] paper d<={s['paper_d']} "
              f"cell={s['w_class']}x{s['locality']} eff={s['eff']} "
              f"passed={s['passed']}")
        for lab in s["labels"]:
            print(f"    - {lab}")


if __name__ == "__main__":
    main()
