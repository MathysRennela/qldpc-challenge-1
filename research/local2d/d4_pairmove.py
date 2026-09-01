#!/usr/bin/env python
"""d=4 chamfer revival: exact annealer with pair moves, warm-started at k=51.

State: hole set on the 26x26 face grid of codes/676-110-3.json (fixed
boundary w2 checks). Exactness: every accepted config has zero weight<=3
logicals on both sides (short_logicals, exhaustive), so d >= 4 exactly.
Single-hole moves are exhausted at k=51; this run adds pair moves
(swap2/add2/rm2). Target: k=52 -> [[676,52,4]], g = 1.2308, which would
dominate the submitted [[676,51,4]] (PR #753).
"""
import json
import random
import sys
import time

import numpy as np

sys.path.insert(0, "research/local2d")
from chamfer4 import gf2_rank, rows, short_logicals  # noqa: E402

TIME_BUDGET_S = 6 * 3600
OUT = "research/candidates/overnight-chamfer4"


def main():
    t0 = time.time()
    d = json.load(open("codes/676-110-3.json"))
    n = d["n"]
    coords = [tuple(c) for c in d["locality"]["coordinates"]]
    c2i = {c: i for i, c in enumerate(coords)}
    L = int(max(max(c) for c in coords)) + 1
    faces = {}
    for i in range(L - 1):
        for j in range(L - 1):
            faces[(i, j)] = frozenset((c2i[(i, j)], c2i[(i + 1, j)],
                                       c2i[(i, j + 1)], c2i[(i + 1, j + 1)]))
    HXb = rows(d["checks"]["X"], n)
    HZb = rows(d["checks"]["Z"], n)
    xsets = {frozenset(np.nonzero(r)[0]) for r in HXb}
    zsets = {frozenset(np.nonzero(r)[0]) for r in HZb}
    base_holes = {pos for pos, fs in faces.items()
                  if fs not in xsets and fs not in zsets}
    bx = [c for c in d["checks"]["X"] if len(c) == 2]
    bz = [c for c in d["checks"]["Z"] if len(c) == 2]

    def build_H(holeset):
        Xl, Zl = [], []
        for (i, j), fs in faces.items():
            if (i, j) in holeset:
                continue
            (Xl if (i + j) % 2 == 0 else Zl).append(sorted(fs))
        return (rows(Xl + bx, n), rows(Zl + bz, n))

    def exact(holeset):
        HX, HZ = build_H(holeset)
        k = n - gf2_rank(HX) - gf2_rank(HZ)
        clean = (not short_logicals(HX, HZ)) and (not short_logicals(HZ, HX))
        return k, clean

    # warm start: the submitted k=51 config
    doc = json.load(open("research/candidates/676-51-4-chamfer.json"))
    holes = set()
    # artifact stores either hole list or the submission; handle both
    if "holes" in doc:
        holes = {tuple(h) if isinstance(h, list) else h
                 for h in doc["holes"]}
    elif "locality" in doc:
        # reconstruct: holes = faces whose support is not a check
        coords2 = [tuple(c) for c in doc["locality"]["coordinates"]]
        c2i2 = {c: i for i, c in enumerate(coords2)}
        L2 = int(max(max(c) for c in coords2)) + 1
        f2 = {}
        for i in range(L2 - 1):
            for j in range(L2 - 1):
                f2[(i, j)] = frozenset((c2i2[(i, j)], c2i2[(i + 1, j)],
                                        c2i2[(i, j + 1)], c2i2[(i + 1, j + 1)]))
        xs = {frozenset(np.nonzero(r)[0]) for r in rows(doc["checks"]["X"], doc["n"])}
        zs = {frozenset(np.nonzero(r)[0]) for r in rows(doc["checks"]["Z"], doc["n"])}
        holes = {pos for pos, fs in f2.items() if fs not in xs and fs not in zs}
    k0, clean0 = exact(holes)
    print(f"warm start: k={k0} clean={clean0} holes={len(holes)}", flush=True)
    if not clean0:
        print("warm start DIRTY — aborting", flush=True)
        return

    rng = random.Random(7)
    best = {"holes": set(holes), "k": k0}
    all_faces = set(faces)

    def persist(k, holeset):
        with open(f"{OUT}/d4-pairmove-best.json", "w") as f:
            json.dump({"k": k, "holes": sorted(holeset), "n": n,
                       "verification": "exhaustive weight<=3, both sides",
                       "date": time.strftime("%Y-%m-%d %H:%M:%S")}, f, indent=1)
        print(f"PERSISTED k={k}", flush=True)

    def climb(seed, deadline, label):
        holes = set(seed)
        k, clean = exact(holes)
        if not clean:
            return
        stale = 0
        while time.time() < deadline and stale < 8:
            moved = False
            non_holes = sorted(all_faces - holes)
            hs = sorted(holes)
            moves = []
            if non_holes:
                moves.append(("add1", (rng.choice(non_holes),)))
            if holes and non_holes:
                moves.append(("move1", (rng.choice(hs), rng.choice(non_holes))))
            if len(hs) >= 2 and len(non_holes) >= 2:
                moves.append(("swap2", (rng.sample(hs, 2),
                                        rng.sample(non_holes, 2))))
            if len(non_holes) >= 2:
                moves.append(("add2", tuple(rng.sample(non_holes, 2))))
            if len(hs) >= 2:
                moves.append(("rm2", tuple(rng.sample(hs, 2))))
            rng.shuffle(moves)
            for kind, arg in moves:
                if kind == "add1":
                    trial = holes | {arg[0]}
                elif kind == "move1":
                    trial = (holes - {arg[0]}) | {arg[1]}
                elif kind == "swap2":
                    trial = (holes - set(arg[0])) | set(arg[1])
                elif kind == "add2":
                    trial = holes | set(arg)
                else:
                    trial = holes - set(arg)
                k2, clean2 = exact(trial)
                if clean2 and k2 >= k:
                    if k2 > k:
                        print(f"  [{label}] {kind} -> k={k2}", flush=True)
                        if k2 > best["k"]:
                            best["holes"], best["k"] = set(trial), k2
                            persist(k2, trial)
                    holes, k = trial, k2
                    moved, stale = True, 0
                    break
            if not moved:
                stale += 1

    climb(holes, t0 + TIME_BUDGET_S * 0.3, "base")
    r = 0
    while time.time() < t0 + TIME_BUDGET_S:
        r += 1
        seed = set(best["holes"])
        for p in rng.sample(sorted(seed), min(8, len(seed))):
            seed.discard(p)
        climb(seed, min(t0 + TIME_BUDGET_S, time.time() + 1500), f"r{r}")
    print(f"FINAL: best k={best['k']}", flush=True)


if __name__ == "__main__":
    main()
