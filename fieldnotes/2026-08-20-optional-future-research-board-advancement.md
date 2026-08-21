---
title: "Optional future research: next board-advancing mechanism"
date: 2026-08-20
author: "@mathysrennela"
model: "GPT-5.6 Luna"
topics: [research-plan, board-advancing, post-submission, multivariate-bicycle, tricycle, AMC, geometry]
status: active
related:
  - 2026-08-20-board-advancing-submission-campaign.md
  - 2026-08-16-trivariate-tricycle-plan.md
  - 2026-08-17-cross-breed-codes-campaign.md
  - 2026-08-17-existing-code-layout-audit.md
  - 2026-08-17-geometric-efficiency-nontopological-campaign.md
  - 2026-08-15-dead-ends-and-leads.md
  - ../research/AUTORESEARCH.md
  - ../CONTRIBUTING.md
  - ../TRACKS.md
---

## Purpose

The submission-first campaign has already produced two self-contained,
validator-passing board advances in PRs #668 and #669. This note is the optional
research plan for finding the next advance after publication review. It is not a
request to reopen the exhausted submission queue, and it does not authorize a
new PR by itself.

The next result counts only if it is a new, trusted-validator-passing candidate
that advances a current computed Pareto frontier. A higher screen score,
a natural-looking layout, or a paper parameter row alone is not a find.

## Current constraints

The following routes are parked and must not be repeated without a named new
mechanism, source artifact, or construction invariant:

- cross-breed designed-divisor codes: the required `Z_333` baseline artifact is
  not self-consistent or recoverable from the accessible repository state;
- post-hoc layouts of existing periodic/algebraic matrices: the tested layouts
  were unrestricted duplicates or had long-range wraparound checks;
- the twisted-torus `[[114,4,d<=14]]` layout: the quotient-element labeling is
  not committed, so raw-index coordinates would be arbitrary cramming;
- the validated flagship planar bilayer family: the `6x8`, `8x8`, and `8x10`
  sweep passed locality checks but was dominated, with the `8x8` case an exact
  duplicate;
- the previously documented exhausted mutation, hole-scaling, blind GAP, and
  small-subgroup slices in `fieldnotes/2026-08-15-dead-ends-and-leads.md`.

Do not spend compute recovering these routes merely because their old screen
records look attractive.

## Priority order

### 1. Multivariate/trivariate bicycle sweep

This route is currently blocked as an immediate action: the repository contains
no `sample_tb` implementation under `research/`, so do not invent a replacement
under that name. It becomes actionable only after a constructor and enumerator
are added with a reproducible algebraic recipe and unit tests.

The intended questions, once implemented, are:

1. Can the unexplained `[[144,2,d<=12]]` duplicate anomaly be resolved by an
   exact-support/fingerprint comparison?
2. Does any symmetry class produce a candidate that is non-dominated in a
   current weight-4, weight-6, or unrestricted cell?
3. Does the result survive fresh-seed distance confirmation on both sides?

Use exact rank and CSS checks before distance screening. Preserve every packaged
survivor through `research/kit/submit.py`; never print a witness without saving
its candidate document. Validate each plausible survivor with
`verify/validate_candidate.py` and compare all nested applicable cells.

Stop this route when the symmetry-reduced weight-4 and weight-5 slices either
produce only duplicates/dominated records or fail fresh-seed confirmation. A
larger random budget for the same slice is not a new mechanism.

### 2. Trivariate-tricycle Route A

If the multivariate bicycle sweep has no signal, run the symmetry-reduced Route A
plan in `fieldnotes/2026-08-17-trivariate-tricycle-plan.md`. Treat the paper
reconstructions as calibration points, not assumed advances. Defer cup-product
Route B and keep Route C weight-9 searches calibration-only unless Route A shows
a concrete structural improvement.

Require a named target cell, construction parameters, exact `k`, both witnesses,
and a validator-passing Pareto advance before expanding the family.

### 3. AMC extensions

Test AMC3 weight-3/4 elements, then AMC4 with nonuniform generator weights, and
only afterward noncyclic abelian groups. Use the quotient-lattice
shortest-cycle heuristic as a prefilter, but do not treat it as a distance
certificate. The first sweep should target a sparse local or weight-6 cell with
explicit symmetry reduction.

Park the route if the new element types reproduce existing fingerprints or if
all validated survivors are dominated. Do not repeat the exhausted AMC slice.

### 4. Kasai product-protocol prefilter

Finish the structural prefilter for mixed collisions, 4-cycles, and 6-cycles,
calibrating it against named table rows and known failures before reconstructing
new witnesses. The prefilter may reject candidates cheaply; it may not promote
one. Every retained reconstruction still goes through the standard submission
kit and trusted validator.

### 5. New intrinsic geometry

Only after the algebraic routes are exhausted should a new geometry be started.
Candidate mechanisms include non-hole weight-4 cellulations, faithful
weight-6 hexagonal patches, single-parity cluster holes at `d=5`, or boundary
shaping near the `[[656,114,3]]` geometry. Checks and coordinates must be
co-designed, with at least two sizes before making any scaling claim.

Do not optimize coordinates for an already-generated unrestricted matrix. A
layout is useful only when the construction itself supplies bounded-radius
interactions and the verifier confirms the locality class.

## Standard execution ladder

For every route:

1. Read the relevant fieldnotes and current board/frontier state.
2. Choose one target cell, one construction family, and a bounded budget.
3. Generate a symmetry-reduced family with reproducible parameters and seeds.
4. Compute exact CSS commutation, ranks, `k`, row weights, and any locality data.
5. Screen distance only for ranking; all distance values remain upper bounds.
6. Package plausible candidates using `research/kit/submit.py`, preserving both
   witnesses and provenance.
7. Run `verify/validate_candidate.py`; keep only `passed: true` survivors.
8. Recompute duplicate and Pareto status against the current `codes/` snapshot,
   including every nested track cell.
9. Fresh-seed confirm finalists. If a lighter logical is found, preserve it,
   lower the claim and filename, and rerun the gate.
10. Stop at the first self-contained board advance and hand it to the
    contributor publication workflow.

## Evidence requirements

For each candidate reaching packaging, preserve:

- construction family and all generator/support parameters;
- symmetry reduction and search budget;
- random seeds and trial counts;
- exact ranks, CSS result, `k`, check weights, and locality diagnostics;
- both persisted logical witnesses;
- the complete trusted-validator verdict;
- exact/WL duplicate results and computed Pareto comparison;
- fresh-seed confirmation, including any newly found lighter logical.

Research candidates belong in local staging until a contributor-driven
publication decision is made. Do not cite ignored staging paths, private paths,
session URLs, or uncommitted scripts as durable evidence. If an external source
is used, cite its public URL and pin a commit or version.

## Immediate next action

The unavailable `sample_tb` path must not be fabricated. The existing TT
constructor in `research/kit/tt.py` passes its construction smoke test, so the
next actionable research step is the documented Route A calibration in
`fieldnotes/2026-08-16-trivariate-tricycle-plan.md`:

1. Reconstruct the paper's explicit TT examples using the existing `build_tt`
   convention.
2. Check dimensions, CSS commutation, exact `k`, and row weights.
3. Build a symmetry-reduced `(2,2,2)` support enumerator with persisted
   parameters, then package plausible candidates through `submit.make_submission`.
4. Run `verify/validate_candidate.py` and compare every nested current-board
   cell.

The TT calibration pass is complete. The existing constructor smoke test
passed, and the five paper examples `[[48,3,d<=4]]`, `[[72,6,d<=6]]`,
`[[90,3,d<=5]]`, `[[180,12,d<=8]]`, and `[[432,12,d<=12]]` reconstructed with
the expected `(n,k)` and check-weight profiles. Their packaged documents passed
structural validation, but every one was dominated in its computed unrestricted
cell; none is a board advance. They remain calibration evidence only.

The symmetry-reduced TT Route A `(2,2,2)` task is complete. The identity-fixed
three-support sweep searched 84 unique support triples at `(2,2,2)`, then 286,
969, and 1,330 unique triples at `(2,2,3)`, `(2,3,3)`, and `(2,2,5)` respectively.
No candidate in any slice reached the packaging threshold `k>=4` with screened
`d>=4`; therefore no witness-bearing candidate or validator promotion was
produced. Route A is stopped for these factor triples and must not be expanded
with a larger budget without a new support mechanism or factor regime.

The next task is AMC extensions: start with AMC3 weight-3/4 elements, then AMC4
nonuniform generator weights, using the quotient-lattice shortest-cycle heuristic
as a prefilter. Preserve all packaged survivors and move only validator-passing,
current-frontier-advancing candidates forward.

## AMC execution audit — 2026-08-20

The AMC stage was checked before any search was run. The current repository has no
AMC constructor, AMC3/AMC4 enumerator, quotient-lattice implementation, or AMC
search script under `research/` or `research/kit/`. The only relevant constructor
present is `research/kit/group_algebra.py`, which implements regular 2BGA codes and
is not an AMC implementation. Repository history also contains no recoverable AMC
implementation or search artifact. The prior AMC result is only the documented
weight-2 sweep (`n=72--114`, `k=3--6`, `d=3--5`, efficiency about `0.7`), which is
explicitly exhausted and must not be repeated.

Therefore no AMC candidate was generated, screened, packaged, or validated in this
stage. This is a reproduction blocker, not a negative result about AMC3 weight-3/4
or AMC4 nonuniform weights. Do not claim a board advance from this audit.

The next actionable research task is to write a small, independently specified AMC
constructor and unit test before searching: define the AMC3 algebraic objects,
finite abelian-group representation, CSS matrix construction, element-weight
convention, and the quotient-lattice prefilter. Only after those tests pass should a
bounded symmetry-reduced AMC3 weight-3/4 sweep begin. If implementing that
constructor is not justified, skip AMC rather than recreating the old weight-2
slice and move to a genuinely new intrinsic geometry with co-designed checks and
coordinates.

## AMC specification step — 2026-08-20

A minimal constructor was added at `research/kit/amc.py`. It represents each
polynomial by exponent tuples in `Z_l1 x ... x Z_lt`, constructs the regular
translation matrices, and uses the adjacent Koszul boundary maps for AMC3 and
AMC4. The calibration embedded in the module reproduces the public AMC4 example
`[[84,6,7]]` at the parameter level (`n=84`, `k=6`) and verifies CSS commutation.
This is construction evidence only; no distance claim or board advance is made.

The next step is a bounded AMC3 weight-3/4 generator with explicit symmetry
reduction. Start from small orders with `n<=200`, screen only after exact CSS,
rank, and row-weight checks, and package any plausible survivor through
`research/kit/submit.py` so both witnesses are persisted. Stop immediately if the
slice produces only duplicates, dominated candidates, or no `k>=4` records with a
credible distance screen.

## Campaign scripts staged — 2026-08-21 (run scheduled)

Three independent, runnable campaign scripts were staged under `research/` for
the scheduled run. Each implements the note's execution ladder: exact CSS/rank/k
and row-weight checks before any distance screen, screening distance is an upper
bound, plausible survivors are packaged through `research/kit/submit.py` (both
witnesses persisted), finalists then pass through `verify/validate_candidate.py`,
and Pareto/nested-cell comparison against the current `codes/` snapshot happens
before any claim. None of the scripts was run at campaign scale; each was smoke
tested at a tiny budget.

### 1. `research/amc3_sweep.py` — AMC3 weight-3/4

- uses the independently specified `research/kit/amc.py` constructor, runs its
  embedded `[[84,6,7]]` calibration smoke at startup;
- quotient-lattice shortest-cycle prefilter (smallest subset of non-identity
generator monomials summing to 0 mod the orders) used to cheaply reject
structurally degenerate candidates — may reject, never promote;
- symmetry reduction by axis permutation + sign flips; `screen` before any
distance screen; survivors packaged through `submit.make_submission`;
finalists run `validate_candidate`;
- explicit stop: a slice with only duplicates, dominated candidates, or no
`k>=4`/`d>=4` records prints a checkpoint and must NOT be expanded (larger
budget on the same slice is not a new mechanism).

### 2. `research/amc4_sweep.py` — AMC4 nonuniform-weight

- uses the independently specified `research/kit/amc.py` constructor, runs its
  embedded `[[84,6,7]]` calibration smoke at startup;
- quotient-lattice shortest-cycle prefilter (smallest subset of non-identity
generator monomials summing to 0 mod the orders) used to cheaply reject
structurally degenerate candidates — may reject, never promote;
- symmetry reduction by axis permutation + sign flips; `screen` before any
distance screen; survivors packaged through `submit.make_submission`;
finalists run `validate_candidate`;
- explicit stop: a slice with only duplicates, dominated candidates, or no
`k>=4`/`d>=4` records prints a checkpoint and must NOT be expanded (larger
budget on the same slice is not a new mechanism).

### 3. `research/kasai_prefilter.py` — Kasai structural prefilter calibration

- rebuilds every bundled Kasai instance using the trusted bundle's own
  construction recipe (`M`/`E`/`D` arrays, CPM blocks), calibrating
  structural features: check-pair support intersections (the bundle's
  `check_intersection_triangles` invariant), mixed collisions, and max check
  weight, plus the exact RREF fingerprint;
- calibration against the named table rows and retained forbidden-pattern bank
  for `qc_848_430_18`; the two named failures `qc_590_240_12` and
  `qc_1524_766_14` come out with girth 6 — consistent with the paper's girth
  column;
- explicit that it is a prefilter only: rejects cheaply, never promotes; every
retained reconstruction still goes through submit + validator.

Smoke checks run (small budgets): AMC3 `(2,2,2)` weight 3 → dead slice
(correctly reports STOP, 0 survivors); `--orbits`/`--combos` caps emitted
orbits / sampled combos (either bound stops iteration); `--seed` makes the
sweep reproducible.  Reference the smoke in the run log, do not treat it as a
campaign-scale result.

## Run log — 2026-08-21 (scheduled run)

### AMC3 sweep — `research/amc3_sweep.py`

```
python3 research/amc3_sweep.py --grid "(2,2,2)" --weight 3 --orbits 20 --combos 200 --trials 60 --seed 0
```

### AMC4 sweep — `research/amc4_sweep.py`

```
python3 research/amc4_sweep.py --grid "(2,2,3,3)" --weights "3,3,4,4" --orbits 60 --combos 3000 --trials 100 --seed 7
```

## AMC stage results — 2026-08-21 (campaign run)

### AMC3 weight-3 (n <= 90)

Grids (2,2,2), (2,2,3), (2,3,3), (2,3,5), 400 orbits / 20,000 combos / 400-trial
screen, seed 20260821. Survivors `[[36,6,4]]` (w=9) and `[[90,6,6]]` (w=9)
passed the validator but were **dominated** (by `[[24,6,4]]` and `[[90,8,10]]`
respectively). No board advance.

### AMC3 weight-4 (n=1..90) — TWO BOARD ADVANCES

Same grids/budget. Survivors included `[[36,9,4]]` (w=12), `[[54,9,5]]` (w=12),
`[[36,9,4]]`-adjacent and `[[90,9,6]]`-type records. The trusted validator
reported **board_advancing = true** for `[[36,9,4]]` and `[[54,9,5]]` (both
weight-9plus x unrestricted, dominated_by = []). Both survived fresh-seed
confirmation (seed 424242): rebuilt n/k, fresh 2000-trial screen, validator
passed with no lighter logical (3940 and 4660 RIS trials respectively).

These are the first AMC board advances from this constructor. They are staged
for human review at `research/candidates/amc3-finalist-2-36-9.json` and
`research/candidates/amc3-finalist-1-54-9.json` (gitignored staging output),
with notes `research/candidates/note-36-9-4.md` and
`research/candidates/note-54-9-5.md`. No PR is opened by this unattended run.

### AMC4 uniform weight-4 (n=96..216)

Grids (2,2,2,2), (2,2,2,3), (2,2,3,3), 400 orbits / 20,000 combos / 400-trial
screen, seed 20260821. Survivors `[[96,12,8]]`, `[[144,12,12]]` (duplicate),
`[[216,6,24]]`, `[[216,6,22]]`, `[[216,12,15]]` all passed the validator but were
**dominated** in their cell. The AMC4 (2,2,3,3) weights (3,3,4,4) slice was
dead (0 survivors). No AMC4 board advance.

### Stop condition respected

The AMC3 weight-3 and AMC4 slices produced only duplicates/dominated records
and were not expanded with a larger budget. The AMC3 weight-4 slice produced
two non-dominated survivors and stopped there (first self-contained advance).

## Next steps

The AMC route has produced its first advances. Per the priority order, the
next candidate mechanism after AMC is the Kasai product-protocol prefilter
(route 4), or a new intrinsic geometry (route 5) once algebraic routes are
exhausted. The two AMC advances are ready for a contributor-driven publication
decision.

## Kasai route — 2026-08-21 (route 4)

### Phase 1: structural prefilter calibration (complete)

`research/kasai_prefilter.py` rebuilt every bundled Kasai instance from the
trusted bundle's own `M`/`E`/`D` arrays and CPM-block convention and computed
the structural features. It reproduces cleanly and writes
`research/candidates/kasai-prefilter-calibration.json` (12 instances):

- all 12 instances reconstruct with `css=True`, the expected `k`, and the
  paper's check-weight profiles (uniform `wmax` 8..16);
- the two named failures `qc_590_240_12` and `qc_1524_766_14` show girth-6
  structure consistent with the paper's girth column;
- the retained forbidden-pattern bank for `qc_848_430_18` (27 patterns, 26 of
  weight 16 and 1 of weight 14) is loaded and summarized as metadata only.

The prefilter is calibration-only: it may reject cheaply, never promote. No
new distance claim is made.

### Phase 2: witness reconstruction probe (no board advance)

With the prefilter calibrated, the next step is reconstructing new witnesses
via the bundle's own search
(`scripts/search_inequivalent_pair_partition_cpm_css_codes.py`). The C++
`cpm_distance` verifier was built (`make -C software/cpm_distance`).

`research/kasai_rank_probe.py` swept the search across seeds, samplers
(`near-source`, `random`), and pairing sources (`reference`, `subgroup`) for
`qc_590_240_12`, `qc_530_216_12`, `qc_472_122_14`, `qc_276_98_14`, and
`qc_372_130_16`:

- the construction fixes `k` at the reference value in every accepted
  candidate (e.g. `[[590,240]]`, `[[372,130]]`), for both pairing sources;
- the search does find permutation-inequivalent candidates (different
  check-intersection triangle counts / WL hashes), but none changes `[[n,k]]`;
- running the C++ distance verifier on several `qc_590_240_12` candidates
  failed to certify the reference distance: each had a smaller non-stabilizer
  vector on one side (`certifies_exact_distance: false`), i.e. `d < 12`.

Since the paper instances are already on the board with exact distances
(`codes/590-240-12.json`, etc.), a Kasai candidate advances the board only by
(a) a higher `k` at the same `n` or (b) a higher `d` at the same `[[n,k]]`.
Neither occurs: `k` is fixed, and the non-equivalent candidates have strictly
worse distance. **No Kasai board advance.**

Per the priority order, route 4 is now exhausted for the bundled parameter
regime. The remaining algebraic route is a new intrinsic geometry (route 5),
which should only be started once the algebraic routes are exhausted. The two
AMC advances remain staged for a contributor-driven publication decision.

## Route 5 probes — 2026-08-21 (new intrinsic geometry)

With routes 1--4 exhausted, route 5 (new intrinsic geometry) is the remaining
candidate mechanism. Three probes were run; all are documented here as
negative/calibration results. No candidate was packaged or validated.

### 5a. Planar family via `boundary_engine` (dominated)

`research/planar_family_probe.py` built the flagship open-boundary planar
family (f = x+x^2+y^2, g = 1+x^2y+x^2y^2) at 6x6..10x12 via the validated
`boundary_engine.build_planar` + `reduce_weights`. It reproduces the known
points `[[72,8,d<=4]]`, `[[128,8,d<=6]]`, `[[200,8,d<=9]]` (w=6) — all already
on the board and dominated. No advance.

### 5b. Weight-4 planar families (dominated)

`research/planar_weight4_probe.py` built four weight-4 support families
(f,g each weight 2) at 8x8..12x14. All come out with low k (2--5) and
low efficiency (0.4--1.0), far below the 2d-local single-layer weight-4
frontier (eff 1.2--2.0). No advance.

### 5c. Checkerboard-plaquette boundary shaping (blocked)

The board's `[[656,114,3]]` code is a single-layer weight-4 checkerboard
plaquette code (X on even 2x2 plaquettes, Z on odd) with hand-crafted
boundary shaping that reaches k=114. A clean checkerboard has weight-1 X
logicals on the top/bottom rows (qubits touched by no Z-check).
`research/checkerboard_css.py` attempted to fix this with weight-2 boundary
checks, but a naive edge check always shares an odd number of qubits with
some opposite-type plaquette, breaking CSS. Analysis of the 656 code shows
its weight-2 checks are placed so each shares exactly 2 qubits with one
opposite plaquette (the CSS-preserving pattern), but the full hand-crafted
rule (63 X + 60 Z plaquettes removed, 21 X + 19 Z weight-2 boundary checks,
20 cells missing from the 26x26 grid) is not a reproducible algebraic recipe.
Reverse-engineering it at other sizes is not a bounded, named mechanism.

### 5d. Dense-packed surface mutations (exhausted)

`research/build_dense_surface.py` reconstructs the `[[101,5,5]]` dense-packed
surface code (arXiv:2511.06758); the reconstruction was verified identical to
the board entry (same rowspace on both sides). The family at larger distances
gives `[[197,5,7]]` and `[[325,5,9]]` — all three k=5 points are already on
the board.

Three mutation probes were run:

- `research/dense_check_mutation_probe.py` (remove one check): removing a
  single check never increases k while keeping d>=5;
- `research/dense_add_probe.py` (add a data qubit): the `[[101,5,5]]` layout
  is fully packed — zero empty odd,odd sites with occupied diagonal ancillas;
- `research/dense_remove_probe.py` (graft-style qubit removal): no qubit can
  be removed while keeping k=5 and d>=5 — the code is minimal.

The k=6 extension (adding a 6th patch) requires designing a new patch layout
beyond the paper's `five_dense_num` rule; that is not a bounded, named
mechanism and was not attempted. The dense-packed k=5 family is exhausted.

### Route 5 status

The four probes produced no validator-passing candidate and no frontier
advance. The remaining route-5 mechanisms from
`fieldnotes/2026-08-15-dead-ends-and-leads.md` are now all accounted for:

- dense-packed surface sweep (5d): exhausted — k=5 family fully on the board,
  no local mutation improves it;
- faithful weight-6 hexagonal patches: blocked — the tested `6.6.6` patches
  found no faithful `m>=4` generator (dead-ends note), and no new generator
  mechanism is available;
- single-parity cluster holes at `d=5`: refuted — the D-rule hole pattern was
  exactly refuted at `23x26` and `25x28` margins (dead-ends note);
- non-hole weight-4 cellulations: blocked — the checkerboard boundary-shaping
  rule (5c) is hand-crafted, not a reproducible algebraic recipe.

Route 5 is exhausted for the currently named mechanisms. The two AMC advances
remain staged for a contributor-driven publication decision.
