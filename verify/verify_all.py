"""Verify every submission under codes/ and examples/, and flag possible
duplicates by permutation-invariant signature. Used by CI. Exit 0 only if all
pass and no two codes/ entries share a signature."""

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from qldpc_verify import verify

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    code_paths = sorted(glob.glob(os.path.join(ROOT, "codes", "*.json")))
    paths = code_paths + sorted(glob.glob(os.path.join(ROOT, "examples", "*.json")))
    if not paths:
        print("no submissions found")
        sys.exit(0)
    failed = []
    sigs = {}
    for p in paths:
        with open(p) as f:
            doc = json.load(f)
        rep = verify(doc)
        rel = os.path.relpath(p, ROOT)
        if rep["ok"]:
            ed = rep["earned_distance"].get("d", {})
            print(f"PASS  {rel}  -> d{ed.get('value','?')} "
                  f"({ed.get('tier','-')})")
            if rel.startswith("codes/") and "signature" in rep:
                sigs.setdefault(rep["signature"]["hash"], []).append(rel)
        else:
            failed.append(rel)
            bad = [c["check"] for c in rep["checks"] if not c["ok"]]
            print(f"FAIL  {rel}  -> {', '.join(bad)}")

    dups = {h: v for h, v in sigs.items() if len(v) > 1}
    if dups:
        print("\nPOSSIBLE DUPLICATES (same permutation-invariant signature; "
              "review for equivalence):")
        for h, v in dups.items():
            print(f"  {h}: {', '.join(v)}")

    print(f"\n{len(paths)-len(failed)}/{len(paths)} passed")
    sys.exit(1 if (failed or dups) else 0)
