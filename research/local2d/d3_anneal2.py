#!/usr/bin/env python
"""d=3 campaign v2: exact annealer with pair moves.

Same exactness contract as d3_anneal.py (every accepted config passes the
exhaustive weight-<=2 logical test d3_clean on both sides), but the move set
adds two-anchor moves: pair-swap (remove 2, add 2) and pair-add/remove.
Single-anchor moves died at k=9 on L=10 and k=3 on L=8; progress needs
multi-anchor moves (same lesson as the d=4 chamfer run at k=51).
"""
import json
import random
import sys
import time

import numpy as np

sys.path.insert(0, "research/local2d")
from chamfer4 import gf2_rank, rows  # noqa: E402
from sat_map_ortho import build_grid, d3_clean  # noqa: E402

TIME_BUDGET_S = 6 * 3600
OUT = "research/candidates/overnight-chamfer4"


def main():
    t0 = time.time()
    L = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    seed_k = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    rng_seed = int(sys.argv[3]) if len(sys.argv) > 3 else 17
    n, faces, w2 = build_grid(L)
    items = ([(p, faces[p], (p[0] + p[1]) % 2 == 0) for p in sorted(faces)]
             + [(f"w{i}", frozenset(s), isx) for i, (s, isx) in enumerate(w2)])
    N = len(items)
    rng = random.Random(rng_seed)
    print(f"L={L}: n={n}, {N} anchors (v2 pair moves, seed={rng_seed})",
          flush=True)

    def exact(active):
        HX = rows([s for _, s, isx in active if isx], n)
        HZ = rows([s for _, s, isx in active if not isx], n)
        k = n - gf2_rank(HX) - gf2_rank(HZ)
        return k, d3_clean(HX, HZ)

    best = {"active": None, "k": 0}
    improvements = 0

    def persist(tag, active, k):
        nonlocal improvements
        improvements += 1
        doc = {"tag": tag, "L": L, "n": n, "k": k,
               "active": [a[0] for a in active],
               "d_lower_bound": 3,
               "verification": "exhaustive weight<=2 enumeration, both sides",
               "annealer": "d3_anneal2 (pair moves)",
               "date": time.strftime("%Y-%m-%d %H:%M:%S")}
        with open(f"{OUT}/d3-L{L}-k{k}-{tag}.json", "w") as f:
            json.dump(doc, f, indent=1)
        print(f"PERSISTED k={k} ({tag})", flush=True)

    def climb(seed, deadline, label):
        nonlocal best
        active = set(seed)
        k, clean = exact(active)
        if not clean:
            return
        stale = 0
        while time.time() < deadline and stale < 8:
            moved = False
            free = [it for it in items if it not in active]
            act = sorted(active, key=str)
            fr = sorted(free, key=str)
            moves = []
            if free:
                moves.append(("add1", (rng.choice(fr),)))
            if active and free:
                moves.append(("move1", (rng.choice(act), rng.choice(fr))))
            if len(act) >= 2 and len(fr) >= 2:
                rm2 = rng.sample(act, 2)
                ad2 = rng.sample(fr, 2)
                moves.append(("swap2", (rm2, ad2)))
            if len(fr) >= 2:
                moves.append(("add2", tuple(rng.sample(fr, 2))))
            if len(act) >= 2:
                moves.append(("rm2", tuple(rng.sample(act, 2))))
            rng.shuffle(moves)
            for mv in moves:
                kind, arg = mv
                if kind == "add1":
                    trial = active | {arg[0]}
                elif kind == "move1":
                    rm, pos = arg
                    if pos in active:
                        continue
                    trial = (active - {rm}) | {pos}
                elif kind == "swap2":
                    trial = (active - set(arg[0])) | set(arg[1])
                elif kind == "add2":
                    trial = active | set(arg)
                else:
                    trial = active - set(arg)
                k2, clean2 = exact(trial)
                if clean2 and k2 >= k:
                    if k2 > k:
                        print(f"  [{label}] {kind} -> k={k2}", flush=True)
                        if k2 > best["k"]:
                            best = {"active": set(trial), "k": k2}
                            persist(label, trial, k2)
                    active, k = trial, k2
                    moved, stale = True, 0
                    break
            if not moved:
                stale += 1

    # seed 1: warm start from the best v1 config if requested/available
    start = set(items)
    if seed_k:
        try:
            with open(f"{OUT}/d3-L{L}-k{seed_k}-base.json") as f:
                names = {tuple(a) if isinstance(a, list) else a
                         for a in json.load(f)["active"]}
            start = {it for it in items if it[0] in names}
            print(f"warm start from k={seed_k} artifact", flush=True)
        except OSError:
            print("warm-start artifact missing; using base", flush=True)
    climb(start, t0 + TIME_BUDGET_S * 0.25, "base")
    r = 0
    while time.time() < t0 + TIME_BUDGET_S:
        r += 1
        seed = set(best["active"]) if best["active"] else set(items)
        # deeper perturbation than v1: drop up to 14 anchors
        for it in rng.sample(sorted(seed, key=str), min(14, len(seed))):
            seed.discard(it)
        climb(seed, min(t0 + TIME_BUDGET_S, time.time() + 1500), f"r{r}")
    print(f"FINAL L={L}: best k={best['k']} "
          f"({improvements} improvements, {r} restarts)", flush=True)
    if best["active"]:
        with open(f"{OUT}/d3-L{L}-v2-final.json", "w") as f:
            json.dump({"k": best["k"],
                       "active": sorted(a[0] for a in best["active"])}, f,
                      indent=1)


if __name__ == "__main__":
    main()
