"""
Validate the circuit-level syndrome-extraction circuit (eval_circuit) on the
toric code. The circuit-level threshold of the toric/surface code is known
(~0.5-1% depending on the schedule), so if the d=3,5,7 curves cross in that
region and the general BP+OSD path agrees with exact pymatching, the circuit
(ancilla extraction, CX colouring, noise, detectors, observable) is correct.

Because the CX schedule here is a generic greedy colouring rather than the
distance-optimal surface-code order, the crossing may sit a bit below the
optimal threshold; that is the documented caveat, not a bug.

    uv run --with stim --with pymatching --with ldpc --with scipy \\
           --with numpy python decode/validate_circuit.py
"""
import sys, os
import numpy as np
import stim
import pymatching

sys.path.insert(0, os.path.dirname(__file__))
from validate_phenom import toric_code
from eval_circuit import build_z_memory_circuit, memory_ler
from eval_phenom import find_logical_z


def ler_pymatching(HX, HZ, p, rounds, shots, seed):
    zsup = find_logical_z(HX, HZ)
    circ = build_z_memory_circuit(HX, HZ, zsup, p, rounds)
    dem = circ.detector_error_model(decompose_errors=True)
    m = pymatching.Matching.from_detector_error_model(dem)
    det, obs = circ.compile_detector_sampler(seed=seed).sample(
        shots=shots, separate_observables=True)
    pred = m.decode_batch(det)
    return float(np.mean(np.any(pred != obs, axis=1)))


def main():
    ps = [0.002, 0.004, 0.006, 0.009, 0.013]
    print("toric circuit-level Z-memory, pymatching, rounds=d, 20000 shots")
    for d in (3, 5, 7):
        HX, HZ = toric_code(d)
        row = []
        for p in ps:
            ler = ler_pymatching(HX, HZ, p, rounds=d, shots=20000, seed=7)
            row.append(f"p={p}:{ler:.4f}")
        print(f"  d={d}: " + "  ".join(row))
    HX, HZ = toric_code(5)
    bp = memory_ler(HX, HZ, 0.006, rounds=5, shots=4000, seed=7,
                    all_logicals=False)["block_ler"]
    pm = ler_pymatching(HX, HZ, 0.006, rounds=5, shots=4000, seed=7)
    print(f"\nd=5 p=0.006: BP+OSD={bp:.4f}  pymatching={pm:.4f} (should be close)")


if __name__ == "__main__":
    main()
