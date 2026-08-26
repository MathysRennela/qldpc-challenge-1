"""Certification sweep: run sat_certify on 2d-local entries lacking certs.

Writes certs/<slug>.json for each entry that closes (d_exact), skipping any
that time out. Ordered small-to-large so quick wins land first.
"""
import sys, os, json, time, glob
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "kit"))
from distance import sat_exact_distance

def matrices(doc):
    n = doc["n"]
    HX = np.zeros((len(doc["checks"]["X"]), n), dtype=np.int8)
    HZ = np.zeros((len(doc["checks"]["Z"]), n), dtype=np.int8)
    for i, row in enumerate(doc["checks"]["X"]): HX[i, row] = 1
    for i, row in enumerate(doc["checks"]["Z"]): HZ[i, row] = 1
    return HX, HZ

def main(slugs, tlim):
    done, refuted, timed_out = [], [], []
    for slug in slugs:
        path = f"codes/{slug}.json"
        if not os.path.exists(path):
            print(f"skip {slug}: no codes file"); continue
        doc = json.load(open(path))
        d = doc["distance"]["d"]
        HX, HZ = matrices(doc)
        t0 = time.time()
        try:
            res = sat_exact_distance(HX, HZ, tlim=tlim,
                                     d_upper={"X": d, "Z": d})
        except Exception as e:
            print(f"{slug}: ERROR {e}"); timed_out.append(slug); continue
        dt = time.time() - t0
        sides = res.get("sides", {})
        status = [sides[s]["status"] for s in ("X", "Z") if s in sides]
        if res.get("d_exact"):
            cert = {"name": doc.get("name"), "d": d,
                    "solver": "CryptoMiniSat 5.14 SAT",
                    "sides": {s: {"value": d, "exact": True,
                                  "note": f"no logical < {d} exists"}
                              for s in ("X", "Z")},
                    "d_exact": True}
            with open(f"certs/{slug}.json", "w") as f:
                json.dump(cert, f, indent=1)
            done.append(slug)
            print(f"{slug}: CERTIFIED d={d} exact ({dt:.0f}s)", flush=True)
        elif "SAT" in status:
            refuted.append(slug)
            print(f"{slug}: REFUTED! claimed d={d} but lighter logical exists "
                  f"({dt:.0f}s): {json.dumps(sides)[:200]}", flush=True)
        else:
            timed_out.append(slug)
            print(f"{slug}: timeout/inconclusive ({dt:.0f}s)", flush=True)
    print(f"\ndone: {len(done)} certified, {len(refuted)} REFUTED, "
          f"{len(timed_out)} inconclusive")
    if refuted: print("REFUTATIONS:", refuted)

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs", nargs="+")
    ap.add_argument("--tlim", type=int, default=600)
    a = ap.parse_args()
    main(a.slugs, a.tlim)
