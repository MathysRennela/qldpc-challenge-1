"""Check whether staged candidates are exact duplicates of committed codes.

Compares the CSS check matrices (X and Z) between a staged candidate and every
committed code with the same (n, k). Two codes are exact duplicates if their
check matrices are identical up to row/column permutation (the verifier's
fingerprint notion). Here we do a cheap canonical comparison: sort rows and
columns.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAND = os.path.join(ROOT, "research", "candidates")
CODES = os.path.join(ROOT, "codes")

TARGETS = [
    "weight4-mvb-finalist-1-96-12", "weight4-mvb-finalist-2-176-22",
    "weight4-mvb-finalist-3-192-6", "weight4-mvb-finalist-4-192-24",
    "weight4-mvb-finalist-5-84-2",
    "campaign-666-150-90", "campaign-666-150-92", "campaign-674-86-107",
    "amc3-finalist-1-54-9", "amc3-finalist-2-36-9", "amc3-finalist-3-36-9",
]


def canonical(checks):
    """Canonical form: sorted rows, each row sorted, both sides sorted."""
    out = []
    for side in ("X", "Z"):
        rows = [tuple(sorted(r)) for r in checks[side]]
        out.append(tuple(sorted(rows)))
    return tuple(out)


def load(path):
    with open(path) as f:
        return json.load(f)


def main():
    committed = {}
    for fn in sorted(os.listdir(CODES)):
        if not fn.endswith(".json"):
            continue
        doc = load(os.path.join(CODES, fn))
        committed.setdefault((doc["n"], doc["k"], doc["distance"]["d"]), []).append(
            (fn, canonical(doc["checks"])))

    for base in TARGETS:
        jp = os.path.join(CAND, base + ".json")
        if not os.path.exists(jp):
            print(f"[{base}] no staged JSON")
            continue
        cand = load(jp)
        key = (cand["n"], cand["k"], cand["distance"]["d"])
        cand_can = canonical(cand["checks"])
        matches = [fn for fn, cc in committed.get(key, []) if cc == cand_can]
        if matches:
            print(f"{base} -> EXACT DUPLICATE of committed: {matches}")
        else:
            # same params but different matrix
            same_params = [fn for fn, _ in committed.get(key, [])]
            print(f"{base} -> distinct matrix (same (n,k,d) as {same_params or 'none'})")


if __name__ == "__main__":
    main()