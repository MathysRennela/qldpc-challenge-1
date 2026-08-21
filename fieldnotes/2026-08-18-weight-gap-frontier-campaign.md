---
title: "Campaign: close the weight-23 and weight-28 frontier gaps"
date: 2026-08-18
author: "@mathysrennela"
model: "GPT-5.6 Luna"
topics: [research-plan, weight-23, weight-28, designed-divisor, generalized-bicycle, leaderboard]
status: active
related:
  - 2026-08-16-beating-designed-divisor-records.md
  - 2026-08-17-cross-breed-codes-campaign.md
  - ../TRACKS.md
---

## Objective

Investigate whether the two gaps in the nested `kd^2/n` frontier can be closed:

1. a code with maximum check weight `<=23` that beats the current `weight<=16`
   leader (`[[390,82,d<=32]]`, score `215.303`), ideally also beating the
   current `weight<=24` leader (`[[674,86,d<=89]]`, score `1010.691`);
2. a code with maximum check weight `<=28` that beats the current
   `weight<=24` leader, ideally retaining the `[[666,150,d<=81]]` score
   `1477.703` below the weight-30 boundary.

This is an unattended autoresearch campaign. Candidates stay in
`research/candidates/`; nothing is promoted to `codes/` or published by this run.

## Baselines and thresholds

- Weight-23 target: start from the `N=337`, `k=86` designed-divisor basin
  represented by `[[674,86,d<=89]]` at maximum weight 24. A same-parameter
  candidate needs `d>=90` to beat that score; a candidate with score above
  `215.303` is sufficient to close the lower gap.
- Weight-28 target: start from the `N=333`, `k=150` basin represented by
  `[[666,150,d<=81]]` at maximum weight 30. Preserving `d>=81` with maximum
  weight `<=28` would score `1477.703`; at the same `(n,k)`, `d>=68` is enough
  to beat the current `weight<=24` score.

All distances are witness-backed upper bounds until independently certified.
A candidate is a find only if the trusted validator returns `passed: true` and
its computed Pareto status is advancing.

## Search design

### Route A: maximum weight `<=23`, `N=337`

- Reuse the degree-64 common-divisor ideal of `x^337+1`.
- Search both supports, not only the lighter component.
- Prefer support sizes around `(10,14)`, `(10,12)`, `(12,12)`, and nearby
  mutations of the submitted supports.
- Enforce the total support/check cap `<=23` before distance screening.
- Rank by `min(d_X,d_Z)`, then by `k*d^2/n` and exact Pareto status.
- Preserve every packaged witness and validator verdict.

### Route B: maximum weight `<=28`, `N=333`

- Reuse the degree-75-like common-divisor regime around the current
  `[[666,150,d<=81]]` code.
- Search support reductions and cross-bred splits `(12,14)`, `(14,14)`, and
  nearby `(16,12)` variants.
- Reject candidates whose exact rank loses the `k>=150` target unless their
  score is still Pareto advancing.
- Enforce maximum check weight `<=28` before deep distance work.
- Rank by `min(d_X,d_Z)` and retain lower-weight witnesses when a candidate is
  refuted.

## Execution ladder

1. Run the existing `research/n337_ideal_mutation.py` and
   `research/mutate_666.py` scripts, which package candidates through
   `research/kit/submit.py` and call `verify/validate_candidate.py`.
2. Inspect staged JSON/verdict pairs; never rely on printed distance output
   alone.
3. If either route produces a validator-passing frontier candidate, retain it
   for human review and run deeper fresh-seed confirmation before treating the
   score as stable.
4. If no route advances, record sample counts, support caps, best screened
   values, and validator/refutation outcomes as a calibrated negative.

## Stop conditions

Stop a route after its bounded search produces no validator-passing,
board-advancing candidate, or after all survivors violate the weight cap or
collapse below the relevant threshold. Reopen only with a new divisor degree,
lift, support mechanism, or independent construction family.

## Results

### Route A — `N=337`, maximum weight `<=23`

Executed the existing ideal-mutation scout:

```text
uv run python research/n337_ideal_mutation.py
```

The degree-64 ideal mutation run accepted one apparent candidate, the unchanged
submitted supports, with a shallow screen of `[[674,128,d<=102]]`. The trusted
validator classified it as an identical duplicate of `codes/674-128-87.json` and
reported `passed: false`; the screen value was not evidence of a new distance.

A second run attempted an explicit low-weight divisor search:

```text
uv run python research/designed_divisor_search.py \
  --n 337 --degree 64 --multiplier-weight 3 \
  --multiple-limit 100 --max-support-weight 12 \
  --screen-trials 80 --validate-trials 500 \
  --min-screen-d 20 --seed 20260818
```

It selected zero factors because the generic enumerator exposes only irreducible
degrees `1` and `21` for `x^337+1`; the incumbent degree-64 ideal is a product
of factors and requires a composite-factor assembler. No candidate with an
explicit `|A|+|B|<=23` cap was therefore packaged or validated.

**Decision:** calibrated negative for the current degree-64 mutation and generic
factor-enumeration implementation, not evidence that the `N=337` basin is
structurally closed. Reopen only with a tracked composite-factor ideal
constructor or a new divisor degree/lift.

### Route B — `N=333`, maximum weight `<=28`

Executed the existing bounded support-mutation search:

```text
uv run python research/search_z333_mutations.py \
  --max-weight 28 --min-screen-d 68 --screen-trials 180 \
  --package-trials 5000 --max-pairs 12000 --seed 20260818
```

The run examined 12,000 shuffled mutation-pair slots after generating 168 A
mutations and 19 B mutations. No candidate survived the exact `k>=150` filter
and no candidate was screened, staged, or sent to the trusted validator.

For calibration, previously staged broader `N=333` mutations reached the target
`k=150` and produced validator-passing candidates only at maximum weight 30;
the apparent `d<=91` candidate was later refuted at weight 89, while the
validator-passing `d<=90` candidate remained weight 30. Thus the current evidence
supports the conclusion that simple divisor-preserving local mutations do not
close the weight-28 gap.

**Decision:** calibrated negative for this mutation neighborhood and budget.
Reopen only with the planned cross-breed support search, a new divisor-preserving
move set, or a different degree/lift—not by repeating this same mutation sweep.

## Overall decision

Neither gap was closed in this execution. The highest-value next implementation
is the missing composite-factor assembler for the degree-64 `N=337` ideal, with
an explicit total-weight cap of 23. In parallel, the `N=333` route needs the
planned support-transfer/cross-breed mechanism; its current local mutation
operator does not preserve enough `k=150` candidates after reducing the cap to
28.
