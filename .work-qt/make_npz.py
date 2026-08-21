import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "633x633")
OUT = HERE


def read_mtx(path):
    with open(path) as f:
        lines = [ln for ln in f if not ln.startswith("%")]
    rows, cols, _ = map(int, lines[0].split())
    M = np.zeros((rows, cols), dtype=np.uint8)
    for ln in lines[1:]:
        parts = ln.split()
        if not parts:
            continue
        r, c = int(parts[0]) - 1, int(parts[1]) - 1
        M[r, c] = 1
    return M


instances = {
    "216-8-18": ("HX_C6_216_8_18.mtx", "HZ_C6_216_8_18.mtx"),
    "432-20-22": ("HX_C6C2_432_20_22.mtx", "HZ_C6C2_432_20_22.mtx"),
    "576-28-24": ("HX_C4rC4_576_28_24.mtx", "HZ_C4rC4_576_28_24.mtx"),
}

for slug, (hxf, hzf) in instances.items():
    hx = read_mtx(os.path.join(SRC, hxf))
    hz = read_mtx(os.path.join(SRC, hzf))
    out = os.path.join(OUT, f"{slug}.npz")
    np.savez(out, hx=hx, hz=hz)
    print(f"wrote {out}: HX {hx.shape} HZ {hz.shape}")
