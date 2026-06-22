"""Validation for heuristic_distance.

1. Corroboration: over every exact-certified code, the heuristic search must never
   find a logical LIGHTER than the certified distance (that would be a bug or a bad
   cert); ideally it corroborates (finds exactly the certified weight).
2. Refutation: an inflated (over-claimed) distance must be refuted.
"""
import copy
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heuristic_distance as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(trials=2500):
    certs = sorted(glob.glob(os.path.join(ROOT, "certs", "*.json")))
    contradictions = corr = inconcl = 0
    print(f"=== corroboration over {len(certs)} exact certs (trials={trials}) ===")
    for cf in certs:
        slug = os.path.basename(cf)
        codef = os.path.join(ROOT, "codes", slug)
        if not os.path.exists(codef):
            continue
        doc = json.load(open(codef))
        cert = json.load(open(cf))
        if not cert.get("d_exact"):
            continue                       # only validate where exactness is proven
        exact_d = int(doc["distance"]["d"])  # the cert certifies this as exact
        res = H.estimate(doc, trials=trials, seed=0)
        dh = res["d_heuristic"]
        flag = ""
        if dh is not None and dh < exact_d:
            flag = "  <<< FOUND LIGHTER THAN EXACT (bug/bad cert)"
            contradictions += 1
        elif res["verdict"] == "corroborated":
            corr += 1
        else:
            inconcl += 1
        print(f"  {slug:16s} exact_d={exact_d:2d} d_heur={dh} "
              f"verdict={res['verdict']}{flag}")
    print(f"\n  corroborated={corr}  inconclusive={inconcl}  "
          f"contradictions={contradictions}")

    print("\n=== refutation: planted over-claim ===")
    doc = json.load(open(os.path.join(ROOT, "codes", "16-2-4.json")))
    true_d = doc["distance"]["d"]
    over = copy.deepcopy(doc)
    over["distance"]["d"] = true_d + 3
    res = H.estimate(over, trials=4000, seed=0)
    print(f"  16-2-4 claimed {true_d + 3} (true {true_d}) -> "
          f"verdict={res['verdict']} d_heur={res['d_heuristic']}")
    ok = res["verdict"] == "refuted"
    print("  refutation", "OK" if ok else "FAILED")

    sys.exit(1 if (contradictions or not ok) else 0)


if __name__ == "__main__":
    main()
