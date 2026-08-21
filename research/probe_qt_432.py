import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "kit"))
from surrogate import lightest_logical

SRC = os.path.join(HERE, "..", ".work-qt", "633x633")

def read_mtx(path):
    with open(path) as f:
        lines = [ln for ln in f if not ln.startswith("%")]
    rows, cols, _ = map(int, lines[0].split())
    M = np.zeros((rows, cols), dtype=np.int8)
    for ln in lines[1:]:
        parts = ln.split()
        if not parts:
            continue
        r, c = int(parts[0]) - 1, int(parts[1]) - 1
        M[r, c] = 1
    return M

hx = read_mtx(os.path.join(SRC, "HX_C6C2_432_20_22.mtx"))
hz = read_mtx(os.path.join(SRC, "HZ_C6C2_432_20_22.mtx"))

for trials, seed in [(50000, 1), (50000, 2), (50000, 3), (100000, 4)]:
    wx, xw = lightest_logical(hx, hz, trials=trials, seed=seed)
    wz, zw = lightest_logical(hz, hx, trials=trials, seed=seed + 100)
    print(f"trials={trials} seed={seed}: X={wx} Z={wz} min={min(wx,wz)}")
    if wx <= 22:
        print("  X witness weight", wx, xw)
    if wz <= 22:
        print("  Z witness weight", wz, zw)