# Contributing a code

1. Build your code and write one JSON file following `schema/code.schema.json`
   (see `schema/SCHEMA.md` for each field). Name it descriptively and put it in
   `codes/`, e.g. `codes/my-128-6-8.json`.

2. Include a distance witness: an explicit logical operator of the claimed
   weight for each side you report. This is what lets the verifier certify your
   distance upper bound without trusting you. A code claiming a distance with
   no valid witness is rejected.

3. Verify locally before opening the PR:

   ```
   uv run python verify/qldpc_verify.py codes/my-128-6-8.json
   ```

   Exit 0 and an `earned_distance` block means it will pass CI.

4. Open a pull request adding only your file(s) under `codes/`. CI runs the
   verifier on every submission. A green check is required to merge.

## Confidence tiers

- `upper_bound`: your witness proves `d <= value`. Anyone can climb this board
  instantly; the math is checked, not trusted.
- `exact`: you also claim no lighter logical exists. Mark it `exact`, but know
  that the board shows it as an upper bound until a maintainer runs
  `verify/certify.py` (a bounded exact solver) and confirms it. We never
  silently upgrade a claim.

## What makes a submission interesting

A code only matters if it advances a track's Pareto frontier over (n, k, d)
under that track's constraints (check weight, locality). Dominated codes are
accepted and recorded but will not sit on the frontier. See `TRACKS.md`.

## Tips

- Store `interaction_radius` as the exact measured max check diameter, not a
  rounded value.
- Do not repeat a qubit index within a single check.
- If you believe your code is equivalent to an existing entry under a code
  symmetry, say so in `provenance.notes`; novelty is part of review.
