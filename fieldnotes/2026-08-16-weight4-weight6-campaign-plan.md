---
title: "Campaign plan: advance weight-4, then weight-6"
date: 2026-08-16
author: "@mathysrennela"
model: "GPT-5.6 Luna"
topics: [research-plan, weight-4, weight-6, multivariate-bicycle, designed-divisor]
status: calibrated-negative
---

## Objective

Run two bounded, reproducible campaigns aimed at the next board-relative Pareto
advance, without modifying `verify/` or promoting anything into `codes/`.
Every plausible result is packaged through `research/kit/submit.py`, staged under
`research/candidates/`, and sent through `verify/validate_candidate.py`.

## Campaign 1: unrestricted x weight-4

**Hypothesis.** Multivariate/trivariate bicycle supports restricted to the three
families `{x^a, y^b, (xy)^c}` can improve the sparse `w <= 4` cell by adding
rank/dimension structure without increasing the two-term-per-polynomial check
weight.

**Search.** Enumerate identity-normalized two-term supports on small and medium
`Z_l x Z_m` tori, with both supports drawn from the x/y/diagonal families.
Deduplicate by stabilizer fingerprint, screen exact CSS/rank and a low-trial
surrogate, retain the top five, package both side witnesses, and validate.

**Target.** Prefer a new point at `w <= 4` with `n <= 150, k >= 8, d >= 6`, or
`n <= 150, k >= 2, d >= 12`. A paper reconstruction or a dominated candidate is
calibration only.

**Stop rule.** This bounded run is exploratory. Reopen only with a new support
family, factor range, or symmetry reduction; do not repeat the same random sweep.

## Campaign 2: unrestricted x weight-6

**Hypothesis.** A common divisor of `x^N + 1` fixes the dimension regime for a
cyclic generalized bicycle. Enumerating low-weight multiples of that divisor is
more productive than unconstrained support mutation.

**Search.** Use the existing `research/designed_divisor_search.py` pilot on
nearby prime orders, divisor degrees corresponding to moderate/high rate, and
resulting support weights at most six. Screen candidates, preserve complete
supports and witnesses, validate every finalist, and compare against the current
weight-6 Pareto frontier.

**Target.** Prefer same `(n,k)` with higher witnessed distance, or a new point
with lower check weight / smaller `n`. Do not treat a surrogate distance as exact.

**Stop rule.** Stop this parameter slice if no validator-passing candidate is
non-dominated, or if all survivors collapse below the screen threshold. Reopen
only with a new divisor degree, lift range, or support mechanism.

## Evidence requirements

For each campaign preserve the generator specification, seed, sample counts,
rank/CSS/weight data, both witnesses, staged JSON, and complete validator
verdict. `research/candidates/` is local staging output and must not be cited as
durable board evidence. Only a validator-passing, board-advancing result is a
find; all other outcomes belong in the results section below.

## Results

### Campaign 1 — completed

Command:

```text
uv run python research/campaign_weight4.py
```

The run generated 480 structured candidates. The screen archive recorded 337
survivors, 108 distance-threshold failures, and 35 duplicate stabilizer codes.
The top five were packaged with 1,600-trial witnesses and all five passed the
trusted validator. The strongest staged points were:

- `[[96,12,4]]`, `w=4`, validator: `passed: true`, `board_advancing: true`;
- `[[176,22,4]]`, `w=4`, validator: `passed: true`, `board_advancing: true`;
- `[[192,6,4]]`, `w=4`, validator: `passed: true`;
- `[[192,24,4]]`, `w=4`, validator: `passed: true`;
- `[[84,2,9]]`, `w=4`, validator: `passed: true`, `board_advancing: true`.

The repository labels these as witness-backed upper bounds, not exact distances,
and literature novelty remains unverified. Staged JSON and verdicts are under
local ignored output in `research/candidates/`; they are not board submissions.

### Campaign 2 — corrected bounded slice

The first requested degree slice (`N=31,37,43` with degrees `6,8,10`) was
empty because those degrees do not occur in the factorizations of `x^N+1`.
A follow-up `N=31, degree=5` run exposed a parameter basin: many distinct
support pairs repeatedly produced `[[62,12,4]]` and consumed validation budget.
The runner was corrected to vary the distance seed by code fingerprint, retain
one representative per screened `(n,k,d)`, and include the code fingerprint in
staging filenames so witnesses cannot be overwritten.

The meaningful rerun was:

```text
uv run python research/designed_divisor_search.py \
  --n 43 --degree 14 --multiplier-weight 2 --multiple-limit 20 \
  --max-support-weight 6 --screen-trials 120 --validate-trials 600 \
  --min-screen-d 4 --seed 20260816
```

It found two low-weight multiples and staged one representative:
`[[86,30,4]]`, maximum check weight 6, validator `passed: true`, but
`board_advancing: false`. This is a calibrated negative for this lift/divisor
slice only, not evidence against designed-divisor GB in general.

## Decision

Campaign 1 produced validator-passing calibration points, including several
board-advancing staged candidates, but no promotion is authorized by this note.
Campaign 2 is parked at the tested `N=43`, degree-14 slice because its
representative was valid but dominated. Reopen only with a new divisor degree,
lift range, or support mechanism. The reusable campaign bookkeeping and
backend changes are recorded in `research/kit/campaign.py`,
`research/kit/search.py`, and `research/kit/surrogate.py`.
