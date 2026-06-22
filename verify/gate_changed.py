"""Distance-refutation gate for the codes changed in a PR (CI).

Runs the bounded, fixed-seed RIS refutation (heuristic_distance.refute_check) only
on the code/example submissions changed in this PR, and exits non-zero if any of
them over-claims its distance (an independent search finds a lighter logical). Bulk
re-verification of the whole board stays cheap -- only new/changed files pay the
~10 s search cost.

Usage:
  python verify/gate_changed.py [BASE] [files...]
    BASE     git ref to diff against (default origin/main); ignored if files given
    files    explicit code JSONs to gate (otherwise computed from the diff)
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heuristic_distance as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def changed_codes(base):
    try:
        out = subprocess.check_output(
            ["git", "diff", "--name-only", f"{base}...HEAD", "--", "codes", "examples"],
            cwd=ROOT, text=True)
    except Exception as e:
        print(f"(could not compute diff vs {base}: {e}); gating nothing")
        return []
    return [f for f in out.split() if f.endswith(".json")]


def main(argv):
    files = [a for a in argv if a.endswith(".json")]
    base = next((a for a in argv if not a.endswith(".json")), "origin/main")
    if not files:
        files = changed_codes(base)
    if not files:
        print("no changed code submissions to gate")
        return 0

    refuted = 0
    for f in files:
        p = f if os.path.isabs(f) else os.path.join(ROOT, f)
        if not os.path.exists(p):                 # deleted/renamed away
            continue
        doc = json.load(open(p))
        if "distance" not in doc or "d" not in doc.get("distance", {}):
            continue
        is_ref, dh, wit, ntr = H.refute_check(doc, seed=0)
        if is_ref:
            refuted += 1
            print(f"REFUTED  {f}: found a weight-{dh} logical < claimed distance "
                  f"{doc['distance']['d']}\n         witness = {wit}")
        else:
            print(f"ok       {f}: no logical lighter than {doc['distance']['d']} "
                  f"in {ntr} RIS trials")
    if refuted:
        print(f"\n{refuted} submission(s) refuted: claimed distance is not supported "
              f"by an independent search. See witnesses above.")
    return 1 if refuted else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
