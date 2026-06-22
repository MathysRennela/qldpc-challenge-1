"""
Circuit-level decoding for general CSS qLDPC codes.

The next step up from phenomenological (eval_phenom): noise on every gate of an
explicit syndrome-extraction circuit, not just on the data and the measurement
outcome. Each stabilizer gets an ancilla; the CX gates between ancillas and data
are scheduled into conflict-free layers by a greedy edge colouring of the Tanner
graph, and depolarizing/flip noise is attached to every reset, CX, idle step,
and measurement. T rounds, then a perfect transversal readout. Decoded by BP+OSD
over the circuit detector error model.

Z-memory experiment: data in |0>^n, full syndrome extraction of both stabilizer
types each round, Z logical observables. Detectors compare each stabilizer round
to round (Z stabilizers also to the deterministic init and the perfect readout).

Caveat on the schedule: a greedy colouring is conflict-free but not guaranteed
distance-optimal. A bad CX order can create hook errors that lower the effective
circuit distance, so for a general code these numbers are a conservative read of
what a tuned schedule could reach, not the best achievable. The construction is
validated against the surface/toric code, whose circuit-level threshold (~0.5-1%)
is known: see validate_circuit.py.

    uv run --with stim --with ldpc --with scipy --with numpy \\
           python decode/run_circuit.py
"""
import numpy as np
import stim

from eval_phenom import find_logical_z_basis, _bposd_decode


def color_cx_layers(edges, ndeg):
    """Greedy edge colouring: partition CX edges (control, target) into layers
    where no qubit appears twice. Returns a list of layers (each a list of
    edges). ndeg is unused beyond documentation; colouring is by qubit usage."""
    layers = []
    used = []          # used[c] = set of qubits busy in layer c
    for (a, b) in edges:
        placed = False
        for c in range(len(layers)):
            if a not in used[c] and b not in used[c]:
                layers[c].append((a, b))
                used[c].add(a); used[c].add(b)
                placed = True
                break
        if not placed:
            layers.append([(a, b)])
            used.append({a, b})
    return layers


def build_z_memory_circuit(HX, HZ, z_supports, p, rounds):
    """Circuit-level Z-memory for a CSS code. Full syndrome extraction (both
    stabilizer types) each round with gate-level noise; perfect final readout."""
    HX = (np.asarray(HX) % 2).astype(np.uint8)
    HZ = (np.asarray(HZ) % 2).astype(np.uint8)
    mx, n = HX.shape
    mz = HZ.shape[0]
    xchecks = [np.nonzero(HX[i])[0].tolist() for i in range(mx)]
    zchecks = [np.nonzero(HZ[j])[0].tolist() for j in range(mz)]
    sups = z_supports
    if np.asarray(sups[0]).ndim == 0 or np.asarray(sups).ndim == 1:
        sups = [sups]
    sups = [np.nonzero(np.asarray(s))[0].tolist() for s in sups]

    data = list(range(n))
    ax = [n + i for i in range(mx)]            # X-stabilizer ancillas
    az = [n + mx + j for j in range(mz)]       # Z-stabilizer ancillas

    # Extract the two stabilizer types in separate phases per round. They
    # commute (CSS), so sequential extraction keeps every syndrome bit
    # deterministic; a single interleaved schedule does not. Each phase is its
    # own greedy colouring.
    z_edges = [(q, az[j]) for j, sup in enumerate(zchecks) for q in sup]
    x_edges = [(ax[i], q) for i, sup in enumerate(xchecks) for q in sup]
    z_layers = color_cx_layers(z_edges, None)
    x_layers = color_cx_layers(x_edges, None)

    def run_layers(layers):
        for layer in layers:
            flat, busy = [], set()
            for (a, b) in layer:
                flat += [a, b]; busy.add(a); busy.add(b)
            c.append("CX", flat)
            c.append("DEPOLARIZE2", flat, p)
            idle = [q for q in data if q not in busy]
            if idle:
                c.append("DEPOLARIZE1", idle, p)
            c.append("TICK")

    c = stim.Circuit()
    c.append("R", data)
    c.append("TICK")

    nmeas = 0
    x_idx_hist, z_idx_hist = [], []
    for t in range(rounds):
        # Z-stabilizer extraction phase: ancilla |0>, CX data->az, measure Z.
        c.append("R", az)
        c.append("X_ERROR", az, p)
        c.append("TICK")
        run_layers(z_layers)
        c.append("M", az, p)
        z_idx = list(range(nmeas, nmeas + mz)); nmeas += mz
        # X-stabilizer extraction phase: ancilla |+>, CX ax->data, measure X.
        c.append("RX", ax)
        c.append("Z_ERROR", ax, p)
        c.append("TICK")
        run_layers(x_layers)
        c.append("MX", ax, p)
        x_idx = list(range(nmeas, nmeas + mx)); nmeas += mx
        x_idx_hist.append(x_idx); z_idx_hist.append(z_idx)

        def rec(a, _N=nmeas):
            return stim.target_rec(-(_N - a))
        if t == 0:
            for j in range(mz):                # |0> init: Z stabs deterministic
                c.append("DETECTOR", [rec(z_idx[j])])
        else:
            pz = z_idx_hist[t - 1]
            for j in range(mz):
                c.append("DETECTOR", [rec(z_idx[j]), rec(pz[j])])
            px = x_idx_hist[t - 1]
            for i in range(mx):
                c.append("DETECTOR", [rec(x_idx[i]), rec(px[i])])
        c.append("TICK")

    # perfect final Z readout of the data
    c.append("M", data)
    data_idx = [nmeas + q for q in range(n)]
    nmeas += n

    def rec(a):
        return stim.target_rec(-(nmeas - a))
    lastz = z_idx_hist[-1]
    for j in range(mz):
        c.append("DETECTOR",
                 [rec(lastz[j])] + [rec(data_idx[q]) for q in zchecks[j]])
    for li, sup in enumerate(sups):
        c.append("OBSERVABLE_INCLUDE", [rec(data_idx[q]) for q in sup], li)
    return c


def memory_ler(HX, HZ, p, rounds=None, shots=4000, seed=0, all_logicals=True):
    """Circuit-level Z-memory per-logical LER (and block LER)."""
    HX = (np.asarray(HX) % 2).astype(np.uint8)
    HZ = (np.asarray(HZ) % 2).astype(np.uint8)
    basis = find_logical_z_basis(HX, HZ)
    k = len(basis)
    sups = basis if all_logicals else basis[:1]
    if rounds is None:
        rounds = 4
    circ = build_z_memory_circuit(HX, HZ, sups, p, rounds)
    block = _bposd_decode(circ, shots, seed)
    per_logical = (1.0 - (1.0 - block) ** (1.0 / max(k, 1))
                   if all_logicals else block)
    return {"block_ler": block, "per_logical_ler": per_logical, "k": k,
            "rounds": rounds, "cx_layers": None}
