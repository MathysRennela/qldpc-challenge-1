import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "kit"))
sys.path.insert(0, os.path.join(HERE, "..", "verify"))
from submit import make_submission, save_submission
from validate_candidate import validate_candidate

SRC = os.path.join(HERE, "..", ".work-qt", "633x633")

def read_mtx(path):
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

name = "[[576,28,24]] quantum Tanner C4rC4"
n, k, d_paper = 576, 28, 24
hx = read_mtx(os.path.join(SRC, "HX_C4rC4_576_28_24.mtx"))
hz = read_mtx(os.path.join(SRC, "HZ_C4rC4_576_28_24.mtx"))
doc = make_submission(
    hx, hz,
    name=name,
    construction=(
        "Quantum Tanner code on a left-right Cayley complex over C4rC4, "
        "A- and B-side local codes both [6,3,3] shortened Hamming; "
        "parity-check matrices taken verbatim from the arXiv:2512.20532 "
        "auxiliary files (633x633/)."
    ),
    authors=["@mathysrennela"],
    family="quantum-tanner",
    references=["arXiv:2512.20532"],
    notes=(
        f"Paper reports [[{n},{k},<={d_paper}]] (QDistRnd upper bound, 3M trials). "
        "This record is witness-backed upper_bound; the true distance may be lower. "
        "Reconstructed from the authors' published .mtx matrices."
    ),
    confidence="upper_bound",
    trials=8000,
    seed=251220532,
)
out = os.path.join(HERE, "candidates", "576-28-24-arxiv-2512-20532.json")
errs = save_submission(doc, out)
print("schema errors:", errs or "none")
verdict = validate_candidate(doc)
with open(out.replace(".json", ".verdict.json"), "w") as f:
    json.dump(verdict, f, indent=2)
print("passed=", verdict["passed"])
print("labels:", json.dumps(verdict["labels"], indent=2))