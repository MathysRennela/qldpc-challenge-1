"""
Phenomenological-noise decoding for general CSS qLDPC codes.

A step up from the code-capacity track (eval.py): instead of one perfect round
of syndrome extraction, this runs T noisy rounds of stabilizer measurement with
measurement errors, then a final perfect readout. It is still not full
circuit-level noise (no gate-by-gate scheduling, which for a general code is
construction-dependent and easy to get misleadingly wrong); it sits between
code-capacity and circuit-level, adding the time dimension and measurement
faults that code-capacity ignores.

Model (Z-memory experiment, detecting X errors via the Z stabilizers):
  - data initialised in |0>^n,
  - each of T rounds: depolarize every data qubit with prob p, then measure
    every Z stabilizer (row of H_Z) with the outcome flipped with prob p,
  - a final perfect (noiseless) transversal Z readout of the data.
Detectors compare each stabilizer to the previous round (and round 0 to the
deterministic |0> value, the final round to the perfect readout). The logical
observable is a Z logical operator. Decoding is BP+OSD over the circuit's
detector error model (so it handles the hyperedges code-capacity BP+OSD does).

Validated against the toric code, whose phenomenological threshold (~2.9-3%) is
known: see `validate_phenom.py`.
"""
import numpy as np
import stim
from scipy.sparse import csc_matrix
from ldpc import BpOsdDecoder


def dem_to_matrices(dem):
    """Convert a (possibly hyperedge) detector error model into the matrices
    BP+OSD needs: H (detectors x errors), L (observables x errors), and the
    per-error prior probabilities. Each independent error mechanism is one
    column, regardless of how many detectors/observables it flips, so this works
    for general qLDPC codes where an edge-only (matching) converter does not."""
    dem = dem.flattened()
    nd, no = dem.num_detectors, dem.num_observables
    h_rows, h_cols, l_rows, l_cols, priors = [], [], [], [], []
    col = 0
    for inst in dem:
        if inst.type != "error":
            continue
        p = inst.args_copy()[0]
        dets, obs = [], []
        for t in inst.targets_copy():
            if t.is_relative_detector_id():
                dets.append(t.val)
            elif t.is_logical_observable_id():
                obs.append(t.val)
            # separators (is_separator) are ignored: treat as one hyperedge
        if not dets and not obs:
            continue
        for d in dets:
            h_rows.append(d); h_cols.append(col)
        for o in obs:
            l_rows.append(o); l_cols.append(col)
        priors.append(p)
        col += 1
    H = csc_matrix((np.ones(len(h_rows), np.uint8), (h_rows, h_cols)),
                   shape=(nd, col))
    L = csc_matrix((np.ones(len(l_rows), np.uint8), (l_rows, l_cols)),
                   shape=(no, col))
    return H, L, np.array(priors)


def find_logical_z(HX, HZ):
    """A single Z logical operator (boolean support over n qubits)."""
    b = find_logical_z_basis(HX, HZ)
    if not b:
        raise ValueError("no logical Z found (k=0?)")
    return b[0]


def find_logical_z_basis(HX, HZ):
    """A basis of k independent Z logical operators: each is in ker(H_X) but
    not in rowspace(H_Z), and they are independent modulo rowspace(H_Z).
    Returns a list of boolean support vectors over the n data qubits."""
    HX = (np.asarray(HX) % 2).astype(np.uint8)
    HZ = (np.asarray(HZ) % 2).astype(np.uint8)
    ker = _nullspace_gf2(HX)              # vectors commuting with all X stabs
    rr = _row_reduce_gf2(HZ)             # rowspace(H_Z) basis for quotient
    span, logicals = list(rr[0]), []     # span accumulates HZ rows + chosen logs
    span_rr = _row_reduce_gf2(np.array(span)) if span else (
        np.zeros((0, HX.shape[1]), np.uint8), [])
    for v in ker:
        r = _reduce_against(v, span_rr)
        if r.any():
            logicals.append(r.astype(bool))
            span.append(r)
            span_rr = _row_reduce_gf2(np.array(span))
    return logicals


def _row_reduce_gf2(M):
    M = (np.asarray(M) % 2).astype(np.uint8).copy()
    rows, cols = M.shape
    piv = []
    r = 0
    for c in range(cols):
        sel = None
        for i in range(r, rows):
            if M[i, c]:
                sel = i
                break
        if sel is None:
            continue
        M[[r, sel]] = M[[sel, r]]
        for i in range(rows):
            if i != r and M[i, c]:
                M[i] ^= M[r]
        piv.append(c)
        r += 1
        if r == rows:
            break
    return M[:r], piv


def _nullspace_gf2(M):
    M = (np.asarray(M) % 2).astype(np.uint8)
    rows, cols = M.shape
    A = M.copy()
    piv_cols = []
    r = 0
    for c in range(cols):
        sel = None
        for i in range(r, rows):
            if A[i, c]:
                sel = i
                break
        if sel is None:
            continue
        A[[r, sel]] = A[[sel, r]]
        for i in range(rows):
            if i != r and A[i, c]:
                A[i] ^= A[r]
        piv_cols.append(c)
        r += 1
        if r == rows:
            break
    free = [c for c in range(cols) if c not in piv_cols]
    basis = []
    for f in free:
        v = np.zeros(cols, dtype=np.uint8)
        v[f] = 1
        for ri, pc in enumerate(piv_cols):
            if A[ri, f]:
                v[pc] = 1
        basis.append(v)
    return basis


def _reduce_against(v, basis_rr):
    """Reduce v by the row-reduced basis_rr (rows, pivots from _row_reduce)."""
    M, piv = basis_rr
    v = (np.asarray(v) % 2).astype(np.uint8).copy()
    for ri, c in enumerate(piv):
        if v[c]:
            v ^= M[ri]
    return v


def build_z_memory(HZ, z_supports, p, rounds):
    """Phenomenological Z-memory circuit for a CSS code with Z-check matrix HZ.
    z_supports: a single support vector, or a list of them (one OBSERVABLE per
    logical Z), over the n data qubits."""
    HZ = (np.asarray(HZ) % 2).astype(np.uint8)
    m, n = HZ.shape
    checks = [np.nonzero(HZ[i])[0].tolist() for i in range(m)]
    sups = z_supports
    if len(np.asarray(sups[0]).shape) == 0 or np.asarray(sups).ndim == 1:
        sups = [sups]
    sups = [np.nonzero(np.asarray(s))[0].tolist() for s in sups]
    c = stim.Circuit()
    data = list(range(n))
    c.append("R", data)
    c.append("TICK")

    # Track absolute measurement indices; convert to rec offsets on the spot.
    nmeas = 0
    stab_idx = []   # stab_idx[t][j] = absolute index of round-t stab j
    for t in range(rounds):
        c.append("DEPOLARIZE1", data, p)
        idx = []
        for sup in checks:
            targets = []
            for q in sup:
                targets.append(stim.target_z(q))
                targets.append(stim.target_combiner())
            targets.pop()
            c.append("MPP", targets, p)
            idx.append(nmeas)
            nmeas += 1
        stab_idx.append(idx)

        def rec(a, _N=nmeas):
            return stim.target_rec(-(_N - a))
        if t == 0:
            for j in range(m):     # |0> init: Z stabs deterministically +1
                c.append("DETECTOR", [rec(idx[j])])
        else:
            prev = stab_idx[t - 1]
            for j in range(m):
                c.append("DETECTOR", [rec(idx[j]), rec(prev[j])])
        c.append("TICK")

    # Final perfect (noiseless) Z readout of all data.
    c.append("M", data)
    data_idx = [nmeas + q for q in range(n)]
    nmeas += n

    def rec(a):
        return stim.target_rec(-(nmeas - a))
    last = stab_idx[-1]
    for j in range(m):
        c.append("DETECTOR",
                 [rec(last[j])] + [rec(data_idx[q]) for q in checks[j]])
    for li, sup in enumerate(sups):
        c.append("OBSERVABLE_INCLUDE", [rec(data_idx[q]) for q in sup], li)
    return c


def _bposd_decode(circuit, shots, seed, max_iter=40, osd_order=10):
    dem = circuit.detector_error_model(decompose_errors=False)
    H, L, priors = dem_to_matrices(dem)
    dec = BpOsdDecoder(H, channel_probs=list(priors), max_iter=max_iter,
                       bp_method="product_sum", osd_method="osd_cs",
                       osd_order=osd_order)
    sampler = circuit.compile_detector_sampler(seed=seed)
    det, obs = sampler.sample(shots=shots, separate_observables=True)
    fails = 0
    Lc = L.tocsr()
    for i in range(shots):
        corr = dec.decode(det[i].astype(np.uint8))
        pred = np.asarray((Lc @ corr) % 2).ravel()
        if np.any(pred != obs[i]):
            fails += 1
    return fails / shots


def memory_ler(HX, HZ, p, rounds=None, shots=4000, seed=0, all_logicals=True):
    """Phenomenological Z-memory logical error rate. With all_logicals, includes
    one observable per logical Z and reports block + per-logical LER (matching
    the code-capacity track's fair metric). rounds defaults to 4."""
    HX = (np.asarray(HX) % 2).astype(np.uint8)
    HZ = (np.asarray(HZ) % 2).astype(np.uint8)
    basis = find_logical_z_basis(HX, HZ)
    k = len(basis)
    sups = basis if all_logicals else basis[:1]
    if rounds is None:
        rounds = 4
    circ = build_z_memory(HZ, sups, p, rounds)
    block = _bposd_decode(circ, shots, seed)
    per_logical = 1.0 - (1.0 - block) ** (1.0 / max(k, 1)) if all_logicals else block
    return {"block_ler": block, "per_logical_ler": per_logical, "k": k,
            "rounds": rounds}
