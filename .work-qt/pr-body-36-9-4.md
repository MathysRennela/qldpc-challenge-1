## Code submission

- Parameters: [[n, k, d]] = [[36,9,4]]
- Tracks: unrestricted / weight-9plus (computed by the verifier from H and the layout)
- Distance confidence: X: upper_bound, Z: upper_bound

Family tag: other (a self-declared filter, never used for ranking).

### Checklist
- [x] One JSON file under `codes/`, conforming to `schema/code.schema.json`
- [x] Distance witness(es) included for each reported side
- [x] `python verify/qldpc_verify.py codes/36-9-4.json` passes locally
- [x] Construction and references filled in under `provenance`
- [x] If this may be equivalent to an existing entry, noted in `provenance.notes` (validator: not an exact duplicate, not WL-equivalent)

### What frontier does this advance?
- **unrestricted / any weight**: on the Pareto frontier

Score kd^2/n = 4.0, max check weight 12, locality class unrestricted.

Construction: AMC3 on Z_2 x Z_2 x Z_3; Koszul polynomials A=[(0,0,0),(0,0,1),(1,0,1),(1,1,0)], B=[(0,0,0),(0,0,1),(0,1,0),(1,0,1)], C=[(0,0,0),(0,0,1),(1,0,0),(1,1,1)]; identity-fixed, symmetry-reduced by axis permutations and sign flips; screened with the research surrogate.

Research note: `notes/36-9-4.md`