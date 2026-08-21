"""Print the Pareto frontier of every populated board cell (site logic)."""
import sys
sys.path.insert(0, "site")
from collections import defaultdict
from build import load_entries, pareto, cells, LOCALITY_LABEL, WEIGHT_LABEL

entries = load_entries()
by_cell = defaultdict(list)
for i, e in enumerate(entries):
    for c in cells(e):
        by_cell[c].append(i)

for c in sorted(by_cell):
    idx = by_cell[c]
    front = pareto([entries[i] for i in idx])
    print("CELL", LOCALITY_LABEL[c[0]], "/", WEIGHT_LABEL[c[1]], ":",
          len(idx), "entries,", len(front), "on frontier")
    for i in sorted(front):
        e = entries[idx[i]]
        print("   [[%d,%d,%d]] w=%d eff=%.1f fam=%s" % (e["n"], e["k"], e["d"], e["w"], e["eff"], e["family"]))