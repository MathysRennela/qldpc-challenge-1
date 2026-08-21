"""Recompute the Pareto frontier for staged candidates against the current board.

For each staged candidate JSON under research/candidates/, load its checks and
witnesses, compute n/k/d/w and its locality/weight classes (from the matching
verdict file), then test whether it is on the Pareto frontier of every
(locality, weight) cell it qualifies for, against the CURRENT committed codes/.

This is a read-only comparison. It does not promote anything and does not
modify the board. Distances are witness-backed upper bounds.
"""
import glob
import json
import os
import sys

sys.path.insert(0, "site")
from build import load_entries, pareto, cells, LOCALITY_LABEL, WEIGHT_LABEL

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAND = os.path.join(ROOT, "research", "candidates")

# Candidates that were reported board-advancing in their verdict files.
TARGETS = [
    "campaign-666-150-90", "campaign-666-150-92", "campaign-674-86-107",
    "mutated-666-150-91-9a8027169d3608f4", "mutated-666-150-93-39f7994f18585cd3",
    "mutated-666-150-95-67275d626f0a1342",
    "z333-mutation-666-150-90-c957fd89675db556",
    "z333-mutation-666-150-91-c957fd89675db556",
    "amc3-finalist-1-54-9", "amc3-finalist-2-36-9", "amc3-finalist-3-36-9",
    "weight4-mvb-finalist-1-96-12", "weight4-mvb-finalist-2-176-22",
    "weight4-mvb-finalist-3-192-6", "weight4-mvb-finalist-4-192-24",
    "weight4-mvb-finalist-5-84-2",
    "bb-weight26-108-8-12", "bb-weight26-196-12-26",
    "bb-weight26-272-6-41", "bb-weight26-288-6-45",
    "bb-weight26-312-10-48", "bb-weight26-600-8-110",
    "bb-weight27-288-8-41", "bb-weight27-300-16-43",
    "bb-weight27-600-8-108", "bb-weight29-196-6-26",
    "bb-weight29-360-8-56",
]


def max_check_weight(checks):
    return max(len(row) for side in ("X", "Z") for row in checks[side])


def load_verdict(base):
    vp = os.path.join(CAND, base + ".verdict.json")
    if not os.path.exists(vp):
        return None
    with open(vp) as f:
        return json.load(f)


def load_candidate(base):
    jp = os.path.join(CAND, base + ".json")
    if not os.path.exists(jp):
        return None
    with open(jp) as f:
        doc = json.load(f)
    w = max_check_weight(doc["checks"])
    d = doc["distance"]["d"]
    return {
        "slug": base, "n": doc["n"], "k": doc["k"], "d": d,
        "eff": round(doc["k"] * d * d / doc["n"], 3), "w": w,
        "doc": doc,
    }


def main():
    entries = load_entries()
    by_cell = {}
    for i, e in enumerate(entries):
        for c in cells(e):
            by_cell.setdefault(c, []).append(i)

    print(f"Board snapshot: {len(entries)} committed codes\n")

    for base in TARGETS:
        cand = load_candidate(base)
        if cand is None:
            print(f"[{base}] no staged JSON; skipping")
            continue
        verdict = load_verdict(base)
        if verdict is None:
            print(f"[{base}] no verdict file; skipping")
            continue
        cand["locality_class"] = verdict["candidate"]["locality_class"]
        cand["weight_class"] = verdict["candidate"]["weight_class"]
        cand["family"] = verdict["candidate"]["family"]

        # Which cells does this candidate qualify for?
        cand_cells = cells(cand)
        # Add the candidate to each cell and test the frontier.
        advancing_cells = []
        dominated_by = {}
        for c in cand_cells:
            idxs = by_cell.get(c, [])
            te = [entries[i] for i in idxs] + [cand]
            front = pareto(te)
            if len(te) - 1 in front:  # candidate index is last
                advancing_cells.append(c)
            else:
                # find who dominates it
                dom = []
                for other in te:
                    if other is cand:
                        continue
                    if (other["n"] <= cand["n"] and other["k"] >= cand["k"]
                            and other["d"] >= cand["d"] and other["w"] <= cand["w"]
                            and (other["n"] < cand["n"] or other["k"] > cand["k"]
                                 or other["d"] > cand["d"] or other["w"] < cand["w"])):
                        dom.append(f"[[{other['n']},{other['k']},{other['d']}]] w={other['w']}")
                dominated_by[c] = dom

        label = f"[[{cand['n']},{cand['k']},d<={cand['d']}]] w={cand['w']} fam={cand['family']}"
        print(f"{base}\n   {label}  eff={cand['eff']}  {cand['locality_class']}/{cand['weight_class']}")
        if advancing_cells:
            print(f"   ADVANCES: " + ", ".join(
                f"{LOCALITY_LABEL[L]}/{WEIGHT_LABEL[W]}" for L, W in advancing_cells))
        else:
            print("   dominated in every cell:")
            for c, dom in dominated_by.items():
                print(f"     {LOCALITY_LABEL[c[0]]}/{WEIGHT_LABEL[c[1]]}: "
                      + ("; ".join(dom) if dom else "(no dominator found)"))
        print()


if __name__ == "__main__":
    main()