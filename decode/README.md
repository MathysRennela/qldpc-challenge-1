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
