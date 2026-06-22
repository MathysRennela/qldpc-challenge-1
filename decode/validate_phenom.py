"""
Validate the phenomenological memory circuit (eval_phenom.build_z_memory) on the
toric code, whose phenomenological threshold is known (~2.9-3%). Decode with
pymatching (exact for the toric code) so this checks the *circuit*, not the
general BP+OSD path. If the d=3,5,7 LER curves cross near 3%, the circuit
construction (rounds, detectors, observable) is correct.

    uv run --with stim --with pymatching --with ldpc --with scipy \\
           --with numpy python decode/validate_phenom.py
"""
import sys, os
import numpy as np
import stim
import pymatching

sys.path.insert(0, os.path.dirname(__file__))
from eval_phenom import build_z_memory, find_logical_z, memory_ler


def toric_code(d):
    """Unrotated toric code on a d x d periodic lattice. n = 2 d^2 qubits on
    edges; X = vertex stars, Z = plaquettes. Returns HX, HZ."""
    def h(x, y):  # horizontal edge index
        return (x % d) + d * (y % d)
    def v(x, y):  # vertical edge index
        return d * d + (x % d) + d * (y % d)
    n = 2 * d * d
    HX = np.zeros((d * d, n), dtype=np.uint8)   # vertex stars
    HZ = np.zeros((d * d, n), dtype=np.uint8)   # plaquettes
    for x in range(d):
        for y in range(d):
            vert = x + d * y
            for e in (h(x, y), h(x - 1, y), v(x, y), v(x, y - 1)):
                HX[vert, e] ^= 1
            plaq = x + d * y
            for e in (h(x, y), h(x, y + 1), v(x, y), v(x + 1, y)):
                HZ[plaq, e] ^= 1
    return HX, HZ


def ler_pymatching(HX, HZ, p, rounds, shots, seed):
    zsup = find_logical_z(HX, HZ)
    circ = build_z_memory(HZ, zsup, p, rounds)
    dem = circ.detector_error_model(decompose_errors=True)
    m = pymatching.Matching.from_detector_error_model(dem)
    det, obs = circ.compile_detector_sampler(seed=seed).sample(
        shots=shots, separate_observables=True)
    pred = m.decode_batch(det)
    return float(np.mean(np.any(pred != obs, axis=1)))


def main():
    ps = [0.02, 0.025, 0.03, 0.035, 0.045]
    print("toric phenomenological Z-memory, pymatching, rounds=d, 20000 shots")
    print("commutation check (HX HZ^T = 0):",
          all(not (toric_code(d)[0] @ toric_code(d)[1].T % 2).any()
              for d in (3, 5, 7)))
    for d in (3, 5, 7):
        HX, HZ = toric_code(d)
        row = []
        for p in ps:
            ler = ler_pymatching(HX, HZ, p, rounds=d, shots=20000, seed=7)
            row.append(f"{ler:.4f}")
        print(f"  d={d}: " + "  ".join(f"p={p}:{r}" for p, r in zip(ps, row)))
    # cross-check the BP+OSD path matches pymatching at one point
    HX, HZ = toric_code(5)
    bp = memory_ler(HX, HZ, 0.03, rounds=5, shots=4000, seed=7,
                    all_logicals=False)["block_ler"]
    pm = ler_pymatching(HX, HZ, 0.03, rounds=5, shots=4000, seed=7)
    print(f"\nd=5 p=0.03: BP+OSD={bp:.4f}  pymatching={pm:.4f} (should be close)")


if __name__ == "__main__":
    main()
