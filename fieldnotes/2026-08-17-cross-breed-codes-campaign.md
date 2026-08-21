---
title: "Campaign plan: cross-breed high-rate board mechanisms"
date: 2026-08-17
author: "@mathysrennela"
model: "GPT-5.6 Luna"
topics: [research-plan, cross-breeding, designed-divisor, high-rate, weight-9plus]
status: active
related:
  - 2026-08-16-beating-designed-divisor-records.md
  - 2026-08-16-weight4-weight6-campaign-plan.md
  - 2026-08-15-dead-ends-and-leads.md
---

## Objective

Test whether mechanisms that have succeeded independently on the board can be
combined to produce a validated Pareto improvement. The first target is not an
arbitrary matrix hybrid: it is a controlled transfer of support and dimension
mechanisms between the two strongest cyclic designed-divisor records.

Current immediate targets are `[[666,150,d<=79]]` and the corrected
`[[674,86,d<=89]]`, as documented in
`fieldnotes/2026-08-16-beating-designed-divisor-records.md`.

## Hypothesis

The high-rate dimension control of the designed-divisor construction can be
retained while importing lighter-support choices from the neighboring record.
A better balance between the two polynomial supports may improve one or both
side distances, reduce maximum check weight, or create a smaller Pareto point.

A secondary route is to transfer the rank, short-cycle, and side-balance
filters from designed-divisor search into nonabelian lifted-product or
balanced-product generation. This route starts only after the cyclic test has
been independently measured.

## First experiment

1. Reconstruct both submitted baselines and verify exact ranks, CSS
   commutation, supports, row weights, and stored witnesses.
2. Hold the lift and common-divisor degree fixed for each baseline.
3. Enumerate both support polynomials rather than preserving one submitted
   support verbatim.
4. Search support splits around `(8,14)`, `(10,14)`, `(12,14)`, `(14,14)`,
   and `(16,14)`, including multiplier weights 2--4 and cyclic-equivalence
   reduction.
5. Rank by the weaker of the two side-distance estimates, then by check
   weight, `k*d^2/n`, and Pareto status.
6. Package every plausible survivor with `research/kit/submit.py`, preserve
   both witnesses, and run `verify/validate_candidate.py`.
7. Use fresh-seed and deep confirmation before treating a large candidate as
   stable; the surrogate value remains an upper bound.

## Success criteria

A result is worth promotion only if it passes the trusted validator and is
board-advancing. Priority outcomes are:

- `n=666, k>=150, d<=80`, preferably with maximum check weight below 30;
- `n=674, k>=86, d<=93`, preferably with maximum check weight below 24;
- a smaller-`n` or lower-weight code that is non-dominated under the computed
  Pareto relation;
- a validated nonabelian or balanced-product candidate showing a measurable
  gain from the transferred filters.

A higher screen score alone is not a success.

## Stop conditions

Stop the fixed-divisor slice if no validator-passing candidate is
board-advancing, if all candidates collapse to the submitted fingerprints, or
if improvements disappear under fresh-seed confirmation. Reopen only with a
new divisor degree, lift range, support mechanism, or independently justified
nonabelian transfer.

## Evidence to preserve

For every filtered candidate preserve the lift, divisor description and degree,
both complete supports, multiplier representation, seed, sample counts, exact
ranks, `k`, CSS result, row weights, both witnesses, and the complete validator
verdict. Failed or refuted candidates should remain useful calibration records;
do not discard their lower-weight witnesses.

## Decision

Stage A of the submission-first campaign is complete, so this campaign is now
active. No cross-bred candidate or negative result has been produced yet. The
first action is to reconstruct and record the exact `Z_333` and `Z_337` baselines
(`[[666,150,d<=79]]` and `[[674,86,d<=89]]`) before searching. The subsequent
support-transfer experiment must use a distinct mechanism from the exhausted
local mutation slices, preserve all witnesses, and stop at the trusted
validator/Pareto gate.
