---
title: "Campaign plan: beat the designed-divisor records in PRs 569 and 570"
date: 2026-08-16
author: "@mathysrennela"
model: "GPT-5.6 Luna"
topics: [research-plan, generalized-bicycle, designed-divisor, high-rate, distance-search]
status: active
related:
  - 2026-07-14-designed-divisor-and-odd-k.md
  - 2026-07-14-large-n-refutation-calibration.md
  - 2026-08-15-dead-ends-and-leads.md
---

## Question

Can a targeted designed-divisor generalized-bicycle campaign beat the two current
records submitted in PRs 569 and 570, either by improving witnessed distance at the
same `(n,k)`, by lowering check weight at comparable parameters, or by producing a
new Pareto point in the same unrestricted cells?

This is a search plan, not a report of completed experiments. No candidate counts,
distances, or validator outcomes should be added here until they are produced and
preserved by the research kit.

## Current baselines

The two targets are:

| Source | Code | Construction | Maximum check weight | Witnessed bound | Score |
| --- | --- | --- | ---: | ---: | ---: |
| PR 569 | `[[666,150,d<=79]]` | cyclic designed-divisor GB over `Z_333` | 30 | `d<=79` | 1405.631 |
| PR 570 | `[[674,86,d<=89]]` | cyclic designed-divisor GB over `Z_337` | 24 | `d<=89` | 1010.691 |

PR 569 is itself a useful calibration: its original `d<=82` claim was refuted by
CI and corrected to `d<=79`. Therefore shallow surrogate values must not be treated
as stable distances, especially at these blocklengths.

PR 569 uses a common-divisor construction with `k=150`, a 16-term polynomial and a
14-term polynomial. PR 570 uses `k=86`, a 10-term polynomial and a 14-term
polynomial. PR 570 retains the 14-term polynomial from the earlier `[[674,86,d<=92]]`
entry and searches a new lighter component.

The immediate record-breaking thresholds are:

- PR 569: a witnessed `d<=80` at the same `n=666,k=150`, or a Pareto improvement
  through lower weight or smaller `n`.
- PR 570: a witnessed `d<=93` at the same `n=674,k=86`, or a code with
  `d<=92` and a genuinely better computed frontier position.

All of these are upper-bound targets. A candidate is a find only if
`verify/validate_candidate.py` returns `passed: true`.

## Transferable mechanism

For a cyclic GB code over `Z_N`, choose both generator polynomials as multiples of
a common divisor `g(x)` of `x^N+1`. The intended dimension is fixed by

```text
k = 2 * deg(g)
```

up to the exact rank calculation performed by the repository. This removes the
largest source of wasted search in unconstrained support sweeps: candidates with a
good apparent distance but collapsed `k`.

The search should therefore enumerate low-weight multiples of `g`, rank candidates
using the exact CSS routines, and spend the expensive budget on the minimum of the
X- and Z-side distance estimates.

## Priority A: optimize both supports at fixed divisor

The first campaign should reproduce each PR and then search both polynomial
supports, rather than retaining one support verbatim.

For each target:

1. Rebuild the submitted pair from the complete support sets in the PR note/JSON.
2. Confirm CSS commutation, exact ranks, `k`, row weights, and the two stored
   witnesses.
3. Keep `N`, the common divisor degree, and the target `k` fixed.
4. Enumerate fresh low-weight multiples for both components.
5. Search all support pairs after cyclic-shift and equivalent-support reduction.
6. Include local mutations around strong supports: one-term replacements,
   one-term additions/deletions, two-term swaps, and multiplier weights 2--4.
7. Rank by `min(d_X,d_Z)`, then by check weight and `k*d^2/n`.

The most attractive local targets are:

- PR 569 regime: `k>=150`, witnessed `d<=80`, preferably maximum weight `<=28`.
- PR 570 regime: `k>=86`, witnessed `d<=93`, preferably maximum weight `<=22`.

The submitted PR 570 reconstruction was refuted from `d<=95` to `d<=89` and
is dominated by the existing `[[674,86,d<=92]]` entry. A new candidate must
beat that corrected incumbent under the computed Pareto relation.

## Priority B: neighboring lifts and divisor degrees

The records are at nearby prime lifts, so the mechanism should be tested around,
not only at, `N=333` and `N=337`.

Sweep nearby prime orders and all useful nontrivial factor degrees of `x^N+1`.
For each divisor degree, retain the exact `(n,k)` after matrix construction rather
than assuming the target dimension. Explore support splits around

```text
(8,14), (10,14), (12,14), (14,14), (16,14), (16,16)
```

The key cross-pollination hypothesis is that PR 569's high-rate target may benefit
from PR 570's lighter-support search. In particular, search degree-75-like targets
near `N=333` with 12/14 or 14/14 supports, not only the submitted 16/14 split.
Conversely, search whether PR 570's degree-43 regime has robust 10/12 or 10/10
pairs with maximum weight below 24.

Candidate filtering must use the board's Pareto relation, not only the headline
score. A slightly larger `N` can be worthwhile if both side distances rise; a
smaller `N` can win even with a lower score if it dominates on `(n,k,d,w)`.

## Priority C: escape routes if cyclic search stalls

If a symmetry-reduced fixed-divisor campaign produces no validated improvement,
move to constructions with more support freedom rather than repeating the same
random sweep.

1. **Nonabelian generalized bicycles / lifted products.** Search groups with order
   near the target blocklength and rate near 20--25%. This is the best direct escape
   from cyclic support correlations.
2. **Balanced products.** Use the existing high-rate product machinery after adding
   a structural prefilter for rank, short cycles, and side-distance balance.
3. **Coset 2BGA.** Treat this primarily as a route to a different lower-weight cell;
   it is not the first choice for beating the any-weight score of PR 569.
4. **Trivariate tricycle codes.** Revisit only if a cheap, symmetry-reduced sweep
   finds a genuine `n<=700` Pareto candidate. Existing paper reconstructions are
   calibration points, not assumed improvements.

## Search and confirmation ladder

The campaign should use separate generation, screening, packaging, and validation
stages:

1. **Reproduction:** rebuild the two PR baselines and record their exact supports,
   ranks, row weights, and witnesses.
2. **Scout:** cheap exact-rank and low-trial surrogate screening over the complete
   fixed-divisor family. Preserve generator parameters and seeds for every survivor.
3. **Filter:** increase trials and require both CSS sides to remain competitive;
   reject candidates whose score depends on one unusually high side estimate.
4. **Package:** call `research/kit/submit.make_submission` for every plausible
   candidate so both witnesses are embedded. Save the JSON under local staging.
5. **Gate:** run `verify/validate_candidate.py` and keep only `passed: true` results.
6. **Deep confirmation:** attack each validated candidate with fresh native RIS-fast
   and, where available, BP+OSD searches. Use approximately the established 1M/side
   packaging floor for large candidates and substantially deeper runs for a record
   attempt.
7. **Promotion review:** compare the validated result against every nested computed
   track and the current Pareto frontier. Do not promote a merely non-dominated
   local-screen result whose witness has not passed the trusted gate.

The surrogate distance remains an upper bound throughout. A high screen value is a
ranking signal, not a lower bound, and a candidate that collapses under a fresh
attack must be retained as a useful failure with its lower-weight witness.

## Evidence to preserve

For every candidate that reaches the filter stage, preserve:

- `N`, divisor polynomial or pinned factor description, and divisor degree;
- both support sets and the multiplier representation;
- random seeds, trial counts, and search implementation;
- exact ranks, `k`, CSS result, maximum row weight, and connectivity if measured;
- both side witnesses from `make_submission`;
- the complete validator verdict, including gates and labels;
- deep-search outcomes and any newly found lower-weight logical;
- whether the result advances a computed Pareto frontier or is only a local survivor.

Never report a distance as exact from a surrogate or refutation search. Never discard
a low-weight logical by printing it without saving the candidate document.

## Stop conditions

Stop the fixed-divisor route for a parameter regime when a symmetry-reduced sweep
and a fresh-seed deep confirmation budget produce no validator-passing frontier
candidate, or when all survivors are dominated by the two PR baselines. Reopen that
route only with a new divisor degree, support mechanism, lift range, or independent
structural feature—not by repeating the same random sweep.

A positive outcome is a staged, validator-passing code that improves one of the
explicit PR thresholds or establishes a new Pareto point. A useful negative outcome
is a fieldnote update containing the searched lifts, divisor degrees, support splits,
sample counts, deepest trials, and collapse witnesses.
