# Submission format (v0.1)

A submission is one JSON file describing one CSS qLDPC code, placed under
`codes/`. The formal contract is `schema/code.schema.json`; this page explains
the fields and, more importantly, what the verifier actually checks.

## Why this shape

Two principles drive the format:

1. Everything cheap and trustless is mandatory and machine-checked. n, k,
   CSS commutation, check weight, and the distance upper bound are all hard
   arithmetic facts that the verifier confirms in milliseconds. You cannot
   submit a code whose claimed k is wrong, or whose checks do not commute.

2. Distance is split into a self-certifying upper bound and a separately
   earned exact tier. Computing a code's distance is NP-hard, so we do not
   ask the submitter to prove it from scratch. Instead you attach a witness:
   an explicit logical operator of the claimed weight. The verifier checks
   the witness is a real nontrivial logical, which certifies `d <= value`
   with no trust required. Claiming `d = value` exactly additionally requires
   server certification (a bounded exact solver or a verifiable certificate);
   until that lands, an exact claim is shown as an upper bound.

## Fields

- `schema_version`: `"0.1"` or `"0.2"` (0.2 added the optional
  `witness_provenance` block; 0.1 files remain valid unchanged).
- `name`: human-readable, e.g. `"[[72,6,6]] generalized weight-6 planar BB code"`.
- `code_type`: `"CSS"` (the only type in v0.1).
- `n`: physical qubit count. Must match the qubit indices used in `checks`.
- `k`: claimed logical qubit count. The verifier recomputes
  `k = n - rank(H_X) - rank(H_Z)` over GF(2) and requires an exact match.
- `checks.X`, `checks.Z`: the parity checks as sparse supports. Each is a list
  of checks; each check is the sorted list of distinct qubit indices (0-based,
  `< n`) it acts on. So `H_X` has `len(checks.X)` rows.
- `distance.d`: claimed code distance, must equal the minimum over the
  earned X and Z side distances.
- `distance.X`, `distance.Z` (both required):
  - `value`: claimed minimum weight of a nontrivial logical of that type.
  - `confidence`: `"upper_bound"` or `"exact"`.
  - `witness`: support of a logical operator of that Pauli type and weight
    `value`. An X-witness must lie in `ker(H_Z)` and outside `rowspace(H_X)`;
    the Z-witness mirrors it. This is what makes the upper bound trustless.
  - `witness_provenance` (optional, schema 0.2, issue #611): who found this
    witness, when, and at what budget — `found_by` (list of `@handles`),
    `date`, `samples` (total search trials), optional `tool` and `seeds`.
    Refutation credit lives here, attached to the operator contributed,
    rather than in `provenance.authors`, which stays reserved for the code's
    constructors. `samples` is the load-bearing number: a bound that has
    survived 10^9 trials is materially stronger evidence than the same value
    backed by 10^6, and it tells the next refuter the budget to beat.
- `locality` (optional): provide a layout and the verifier derives the locality
  class (`local-2d-single`, `local-2d-bilayer`, or `unrestricted`); omit it and
  the code is `unrestricted`.
  - `coordinates`: one `[x, y]` per qubit, indexed `0..n-1`.
  - `layers`: physical layers (2 for a flip-chip bilayer, for example).
  - `interaction_radius`: claimed max check diameter in the layout; the
    verifier recomputes the true max check diameter and requires
    `measured <= claim`.
- `provenance`: `authors`, `construction` (how it was built), optional
  `references`, `date`, `notes`, `model`.
  - `origin`: `"baseline"` for a literature seed or `"submission"` for a code
    contributed through the challenge. This is provenance, not a novelty claim.
  - `novelty`: optional literature status for submissions:
    `"unknown"` (not audited), `"known_parameters"` (the `[[n,k,d]]` parameter
    set exists in the literature, though this entry may improve weight, layout,
    or construction details), or `"new_parameters"` (claimed novel after review;
    not a verifier-proved fact).
- `family` (optional): the construction family, a Layer-2 tag from a fixed
  vocabulary (`bivariate-bicycle`, `generalized-bicycle`, `2bga-coset`,
  `hypergraph-product`, `lifted-product`, `balanced-product`, `quantum-tanner`,
  `tile`, `topological`, `other`). It cannot be recovered from `H`, so it is a
  filter only, never a ranking. See `../TRACKS.md`.
- `tracks`: deprecated and ignored for ranking. Track membership (the locality
  and weight classes) is computed by the verifier from `H` and the layout; this
  self-declared field is kept only for backward compatibility. See `../TRACKS.md`.

## What the verifier reports

`python verify/qldpc_verify.py codes/your-code.json` prints a JSON report:
per-check pass/fail, the computed `n, k, ranks, max_check_weight,
interaction_radius`, and an `earned_distance` block giving the tier each side
actually earned (an `exact` claim shows as `upper_bound` here and is flagged
for server certification). Exit code 0 iff every required check passes.

## Public CI limits

The public submission path has generous resource limits so malformed or hostile
JSON cannot force unbounded dense-matrix allocation in CI. Current automatic
limits are:

- JSON file size: 5 MB.
- `n <= 700` (the verification-budget cap, issue #249; raise-only).
- At most 10000 X-checks and 10000 Z-checks.
- Max check weight 32 (issue #249: beyond this, validating a claim is not practical, and weight 32 is already beyond near-term hardware).
- At most 200000 total support entries across all checks.
- At most 600 locality coordinate entries.
- Dense verifier intermediates capped at 50000000 cells.

These are far above the current board entries. A larger code should be handled
through a maintainer-run path until the verifier is sparse end-to-end.

## Conventions and gotchas

- A repeated qubit index within a single check is rejected (it would XOR
  away and silently change the code).
- Store `interaction_radius` as the exact measured value, not a rounded one;
  a value rounded down below the true diameter will fail the `<=` check.
- Both distance sides are required. The verifier earns the global `d` only when
  both witnesses validate and `distance.d = min(dX, dZ)`.
