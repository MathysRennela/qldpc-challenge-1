"""Verify every submission under codes/ and examples/. Used by CI.
Exit 0 only if all pass."""

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from qldpc_verify import verify

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    paths = sorted(glob.glob(os.path.join(ROOT, "codes", "*.json"))
                   + glob.glob(os.path.join(ROOT, "examples", "*.json")))
    if not paths:
        print("no submissions found")
        sys.exit(0)
    failed = []
    for p in paths:
        with open(p) as f:
            doc = json.load(f)
        rep = verify(doc)
        rel = os.path.relpath(p, ROOT)
        if rep["ok"]:
            ed = rep["earned_distance"].get("d", {})
            print(f"PASS  {rel}  -> earned d{ed.get('value','?')} "
                  f"({ed.get('tier','-')})")
        else:
            failed.append(rel)
            bad = [c["check"] for c in rep["checks"] if not c["ok"]]
            print(f"FAIL  {rel}  -> {', '.join(bad)}")
    print(f"\n{len(paths)-len(failed)}/{len(paths)} passed")
    sys.exit(1 if failed else 0)
