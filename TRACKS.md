# Tracks and leaderboards

A quantum code is not a single number. You trade physical qubits n, logical
qubits k, distance d, check weight, and geometric locality against each other,
and separately you care how the code decodes under noise. So there is no one
leaderboard. Instead there are tracks (hard-constraint categories), and within
each track the ranking is a Pareto frontier, not a single winner.

## How ranking works inside a track

Two views of the same data:

- Frontier view: the set of Pareto-optimal codes over (n, k, d). A code is on
  the frontier if no other code in the track dominates it (no other has n' <=
  n, k' >= k, d' >= d with at least one strict). There can be many co-leaders.
- Cell view (the code-tables style): a grid keyed by (k, d); each cell holds
  the smallest known n, with a challenger history. This is the view people
  usually screenshot.

`kd^2/n` (the encoding-efficiency figure the 2D-locality literature uses) is a
sortable column and a reasonable per-track headline number, but it never
collapses the frontier into one rank.

Every entry also carries a distance-confidence label, orthogonal to the track:
`d<=` (self-certified upper bound) or `d=` (server-certified exact). They are
shown distinctly; an exact record outranks an equal upper-bound one.

## Initial tracks

These are where we have data and verification today. More can be proposed by PR.

- `weight-6`: CSS codes with all stabilizer checks of weight <= 6, any
  connectivity. The headline frontier. Sub-thresholds `weight-4`, `weight-8`
  exist as separate tracks.
- `2d-local-bilayer`: geometrically 2D-local on up to 2 physical layers
  (the flip-chip regime of the bivariate-bicycle planar codes), with a stated
  `locality` block. Ranked within a maximum interaction radius.
- `bivariate bicycle (periodic)`: bivariate bicycle codes on a torus
  (periodic boundary conditions), no 2D-local layout. Seeded with the
  canonical codes of Bravyi et al (arXiv:2308.07915).
- `2d-local-single`: 2D-local on a single layer (surface-code-like
  connectivity). Stricter; mostly a baseline track.
- `decoding` (planned): a fixed code or an open submission ranked by logical
  error rate / threshold under a server-fixed circuit-level noise model. The
  server runs the simulation so the result cannot be gamed; this track needs
  decoder sandboxing and lands after the parameter tracks.

A code may enter multiple tracks (list them all in `tracks`). It only appears
on a track's board if it satisfies that track's constraints, which the
verifier checks (for example, `weight-6` requires measured max check weight
<= 6; `2d-local-bilayer` requires a `locality` block with `layers <= 2`).

## Baselines and provenance

The boards are seeded with the codes from Liang, Eberhardt, Chen
(arXiv:2504.08887) as the reference baseline, attributed as theirs, so every
new submission is measured against the published state of the art rather than
an empty board.
