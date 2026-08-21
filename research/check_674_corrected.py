"""Test whether corrected-distance candidates still advance the frontier.

campaign-674-86-107 was refuted to d<=105 by the validator (weight-105 logical
found). Recompute its frontier status at d=105 against the current board.
"""
import json
import os
import sys

sys.path.insert(0, "site")
from build import load_entries, pareto, cells, LOCALITY_LABEL, WEIGHT_LABEL

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAND = os.path.join(ROOT, "research", "candidates")


def main():
    entries = load_entries()
    by_cell = {}
    for i, e in enumerate(entries):
        for c in cells(e):
            by_cell.setdefault(c, []).append(i)

    # candidate 674-86-107 at corrected d=105, w=24
    with open(os.path.join(CAND, "campaign-674-86-107.json")) as f:
        doc = json.load(f)
    w = max(len(r) for side in ("X", "Z") for r in doc["checks"][side])
    cand = {
        "slug": "campaign-674-86-107", "n": doc["n"], "k": doc["k"],
        "d": 105, "eff": round(doc["k"] * 105 * 105 / doc["n"], 3), "w": w,
        "locality_class": "unrestricted", "weight_class": "weight-9plus",
        "family": doc.get("family"),
    }
    print(f"[[674,86,d<=105]] w={w} eff={cand['eff']}")
    for c in cells(cand):
        idxs = by_cell.get(c, [])
        te = [entries[i] for i in idxs] + [cand]
        front = pareto(te)
        status = "ADVANCES" if len(te) - 1 in front else "dominated"
        print(f"  {LOCALITY_LABEL[c[0]]}/{WEIGHT_LABEL[c[1]]}: {status}")
        if status == "dominated":
            for other in te:
                if other is cand:
                    continue
                if (other["n"] <= cand["n"] and other["k"] >= cand["k"]
                        and other["d"] >= cand["d"] and other["w"] <= cand["w"]
                        and (other["n"] < cand["n"] or other["k"] > cand["k"]
                             or other["d"] > cand["d"] or other["w"] < cand["w"])):
                    print(f"    dominated by [[{other['n']},{other['k']},{other['d']}]] w={other['w']}")


if __name__ == "__main__":
    main()