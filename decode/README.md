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

## Protocol (circuit-level)

Noise on every gate of an explicit syndrome-extraction circuit, the closest of
the three to a real device. Implemented and validated as tooling
(`eval_circuit.py`), runnable per code, but not run as a board-wide ranking; see
"Why no board ranking" below.

- Circuit: one ancilla per stabilizer. The two stabilizer types are extracted
  in separate phases per round (they commute for a CSS code, so sequential
  extraction keeps every syndrome bit deterministic; a single interleaved
  schedule does not). The CX gates are scheduled into conflict-free layers by a
  greedy edge colouring of the Tanner graph.
- Noise: depolarizing on every CX (DEPOLARIZE2), flip noise after each reset and
  on each measurement outcome, and idle depolarizing on data qubits not engaged
  in the current CX layer. T rounds, then a perfect transversal readout.
- Decoder: BP+OSD over the (undecomposed) circuit detector error model, same as
  the phenomenological path.
- Schedule caveat: a greedy colouring is conflict-free but not distance-optimal.
  A bad CX order creates hook errors that lower the effective circuit distance,
  so for a general code these numbers are a conservative read of what a tuned
  schedule could reach, not the best achievable. Stated on the site too.

Validated against the toric code (`validate_circuit.py`): the d=3,5,7 curves
cross in the known circuit-level threshold region and the general BP+OSD path
agrees with exact pymatching on the same circuit.

### Why no board ranking

A fair cross-code ranking needs each code's syndrome-extraction schedule to
preserve its distance. The greedy colouring here does not, and the effect is
large and uneven: on the toric code it costs only a small factor, but on a
high-rate bivariate-bicycle code like [[72,12,6]] the circuit per-logical LER at
p=0.004 is ~0.08 (near threshold), versus ~0.001 at code-capacity. So a board
ranking would mostly measure how well the naive schedule happens to handle each
code, and would bury exactly the high-rate codes the challenge is about, which
would be misleading. Distance ordering does hold where the schedule behaves
(toric, and the low-rate board codes: [[81,1,9]] 0.012 vs [[25,1,5]] 0.043 at
p=0.004), so the evaluator is correct; what is missing is per-code schedule
optimization, which is its own piece of work. Until then circuit-level stays a
per-code tool, not a leaderboard.

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

## Regenerating the leaderboard

Offline tooling (needs `ldpc`); kept out of the cheap CI verifier. After adding
or changing codes:

```
uv run --with ldpc --with numpy python decode/run_leaderboard.py
uv run --with stim --with ldpc --with scipy --with numpy python decode/run_phenom.py
uv run python site/build.py
```

Then commit `decode/results.json`, `decode/phenom_results.json`, and the
rebuilt `docs/`.

## Planned

- Circuit-level noise (needs syndrome-extraction circuit construction per code).
- A sandboxed submitted-decoder competition for a fixed code.
