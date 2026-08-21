---
title: "Campaign plan: scalable geometric efficiency above one"
date: 2026-08-17
author: "@mathysrennela"
model: "GPT-5.6 Luna"
topics: [research-plan, geometric-efficiency, scaling, topology]
status: parked
related:
  - 2026-08-15-dead-ends-and-leads.md
  - 2026-08-17-geometric-efficiency-nontopological-campaign.md
  - ../TRACKS.md
---

## Objective

Test whether a genuinely scalable family can maintain geometric efficiency
`g > 1`, rather than finding one favorable small-distance packing. This is a
follow-up research direction, not a license for broad searches over arbitrary
layouts.

## Board context

The current board contains small and moderate local constructions with useful
geometric scores, including `d=3` holey surface entries. However, the existing
records do not establish that `g>1` persists as the family grows. Naive hole
scaling and larger patch fusion have already failed to improve geometric
efficiency in the tested models.

## Hypothesis

A new topology or cellulation—not a larger copy of an existing hole pattern—may
improve the density-versus-distance tradeoff. Candidate mechanisms include a
non-hole weight-4 cellulation, a faithful hexagonal construction, single-parity
cluster holes at higher distance, or boundary shaping around an existing dense
geometry.

## First experiment

1. Choose one topology with a clear size parameter and an explicit generator.
2. Generate at least three sizes, not just one optimized instance.
3. Compute the exact CSS parameters and package both witnesses for every
   candidate.
4. Supply honest single-layer or bilayer coordinates and run the verifier's
   locality diagnostics.
5. Track `g`, `k*d^2/n`, radius, layer count, and check weight at each size.
6. Use exact certification only where it is computationally realistic; label
   larger distances as upper bounds.
7. Compare the sequence against existing local Pareto records, looking for
   improvement with size rather than an isolated finite-size spike.

An initial bounded budget should be one topology, 3--6 sizes, and a small
number of local mutations or boundary variants around each size.

## Success criteria

A route becomes promising only if:

- at least two increasing sizes pass the trusted validator;
- both retain honest locality and `g > 1` under the verifier's formula;
- the score does not rely solely on `d=2` or `d=3` finite-size behavior;
- the family produces a non-dominated local point or a clear positive scaling
  trend.

A single `g>1` candidate is evidence for further testing, not evidence of a
scalable family.

## Stop conditions

Park the route if `g` decreases with size, if the construction saturates at
`d=3` without a density improvement, if larger variants fail CSS, or if all
survivors are dominated by existing local codes. Reopen only with a different
cellulation, boundary mechanism, or scaling invariant.

## Evidence to preserve

Preserve the generator, topology parameters, complete checks and coordinates,
layer and spacing diagnostics, measured interaction radius, exact ranks, both
witnesses, validator verdicts, and the full size-by-size score table. Record
negative results as calibration rather than silently dropping them. Any prose
Any prose claim about scaling must point to artifacts present in the submitted tree.

## Decision

Park this follow-up until a concrete local family survives the existing-layout
audit and produces at least one honest `g > 1` candidate. No scaling result is
available, and a single finite-size layout would not justify reopening this
route.
