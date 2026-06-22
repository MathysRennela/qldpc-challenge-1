# Decoding track

Ranks codes by how well they actually protect information under noise, a
separate axis from the static (n, k, d) parameters. The number is computed here
(fixed decoder, noise, seed, shot budget), not claimed by the submitter, so the
ranking cannot be gamed.

## Protocol (v1, code-capacity)

- Noise: independent code-capacity noise (each data qubit takes an X error
  with probability p, and independently a Z error; the two sides are decoded
  separately). The ranking uses p = 0.04; results.json also records a second
  point at p = 0.02 so the leaderboard can show how each code's LER scales as
  noise drops.
- Decoder: pinned BP+OSD (`ldpc.BpOsdDecoder`, `osd_method="osd_cs"`,
  `osd_order=10`, `max_iter=30`). X errors are decoded with H_Z, Z with H_X.
- Failure: a residual error (input XOR correction) is a logical failure if it
  lies outside the rowspace of the opposite checks, i.e. it is a nontrivial
  logical, not a stabilizer.
- Metric: per-logical-qubit logical error rate. Block LER unfairly penalizes
  high-k codes (more logical operators that can fail), so we report
  `per_logical = 1 - (1 - block_LER)^(1/k)`. Lower is better.
- Reproducibility: fixed seed and shot budget (see `run_leaderboard.py`).

This is code-capacity, not circuit-level; it measures the code, not a full
syndrome-extraction circuit. Treat it as the encoding-side decoding axis, not a
fault-tolerance threshold.

## Protocol (phenomenological, multi-round)

A step up from code-capacity that adds the time dimension and measurement
faults. It is reported as a second table under the same Decoding section.

- Experiment: Z-memory. Data initialised in |0>^n; over T rounds each data
  qubit is depolarized with probability p and every Z stabilizer is measured
  with its outcome flipped with probability p; then a final perfect transversal
  Z readout. Detectors compare each stabilizer round to round (and to the
  deterministic init / perfect final readout).
- Rounds: a fixed T for every code (see `run_phenom.py`), so the time exposure
  is comparable across distances.
- Decoder: BP+OSD over the circuit's detector error model. The
  detector/observable matrices are built directly from the (undecomposed) DEM,
  so hyperedge error mechanisms are kept as single columns; an edge-only
  (matching) converter cannot handle a general qLDPC circuit.
- Metric: one observable per logical Z, same per-logical-qubit LER as above.
- Still not circuit-level: there is no gate-by-gate syndrome-extraction
  schedule, which for a general code is construction-dependent and easy to get
  misleadingly wrong. This sits between code-capacity and circuit-level.

Validated against the toric code (`validate_phenom.py`): the d=3,5,7 curves
cross near the known phenomenological threshold, and the general BP+OSD path
agrees with exact pymatching on the same circuit.

## Protocol (circuit-level, single-basis Z-memory)

Noise on every gate of an explicit syndrome-extraction circuit, the closest of
the three to a real device. Reported as a third table under the Decoding
section.

- Single-basis: this is a Z-basis memory experiment, so only the X-type data
  errors that can flip the Z logical matter, and the Z stabilizers detect
  exactly those. Only the Z stabilizers are extracted; the X-stabilizer
  extraction is omitted because it would only inject CX noise into the data
  without aiding the decode. This is the standard single-basis benchmark; it
  does not include the X-extraction depth a real device also pays for two-basis
  protection.
- Circuit: one ancilla per Z stabilizer, CX (data control, ancilla target)
  scheduled into conflict-free layers by a greedy edge colouring. Because the
  data qubits are controls, a CX fault spreads to the ancilla, not across data,
  so there are no harmful X-hook errors and the schedule does not reduce the
  effective Z-distance (verified: the high-rate [[72,12,6]] gives per-logical
  ~0.003 here, in line with low-rate codes, not the ~0.08 the two-basis circuit
  produced).
- Noise: depolarizing on every CX (DEPOLARIZE2), flip noise after each reset and
  on each measurement outcome, and idle depolarizing on data qubits not engaged
  in the current CX layer. T rounds, then a perfect transversal Z readout.
- Decoder: BP+OSD over the (undecomposed) circuit detector error model, same as
  the phenomenological path. One observable per logical Z.

Validated against the toric code (`validate_circuit.py`): the d=3,5,7 curves
cross near the threshold (~0.01 here) and the general BP+OSD path agrees with
exact pymatching on the same circuit.

## Files

- `eval.py` — the evaluator. `logical_error_rate(HX, HZ, p, shots, seed)`
  returns block and per-logical LER. CLI: `python eval.py codes/foo.json p shots`.
- `validate_surface.py` — sanity check: surface-code LER curves (d=5,7,9) cross
  at the known ~10% threshold, confirming the evaluator captures threshold
  behavior.
- `run_leaderboard.py` — evaluates every board code under the pinned protocol
  and writes `results.json`, which the site reads to render the Decoding
  leaderboard.
- `eval_phenom.py` — the phenomenological evaluator (multi-round Z-memory
  circuit + BP+OSD over the DEM). `memory_ler(HX, HZ, p, rounds, shots, seed)`.
- `validate_phenom.py` — toric-code validation of the phenomenological circuit
  and decoder (threshold crossing; BP+OSD vs pymatching agreement).
- `run_phenom.py` — runs the board under the phenomenological protocol and
  writes `phenom_results.json`.
- `eval_circuit.py` — the circuit-level evaluator (explicit Z-memory
  syndrome-extraction circuit + BP+OSD over the DEM). `memory_ler(HX, HZ, p,
  rounds, shots, seed, z_only=True)`.
- `validate_circuit.py` — toric-code validation of the circuit-level model
  (threshold crossing; BP+OSD vs pymatching agreement).
- `run_circuit.py` — runs the board under the circuit-level protocol and writes
  `circuit_results.json`.

## Regenerating the leaderboard

Offline tooling (needs `ldpc`); kept out of the cheap CI verifier. After adding
or changing codes:

```
uv run --with ldpc --with numpy python decode/run_leaderboard.py
uv run --with stim --with ldpc --with scipy --with numpy python decode/run_phenom.py
uv run --with stim --with ldpc --with scipy --with numpy python decode/run_circuit.py
uv run python site/build.py
```

Then commit `decode/results.json`, `decode/phenom_results.json`,
`decode/circuit_results.json`, and the rebuilt `docs/`.

## Planned

- Two-basis circuit-level noise with per-code distance-preserving schedules
  (the single-basis Z-memory here omits X-extraction).
- A sandboxed submitted-decoder competition for a fixed code.
