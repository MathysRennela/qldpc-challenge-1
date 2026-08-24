---
title: "Univariate bicycle (UB) sweep: 2 board advances from arXiv:2605.14173"
date: 2026-08-23
author: "@mathysrennela"
model: "ox-alpha (Zed agent)"
topics: [generalized-bicycle, univariate-bicycle, literature-mining, weight-8]
status: staged
related:
  - 2026-08-15-dead-ends-and-leads.md
  - 2026-08-15-arxiv-board-harvest.md
---

## Summary

Reconstructed all nine under-cap rows of the univariate bicycle (UB) Table I
of arXiv:2605.14173v1 (Rabeti–Mahdavifar) — a GB subclass with the Frobenius
coupling `b(x) = a(x^(2^ℓ)) mod (x^n−1)`. Every row reproduced the paper's k
and witnessed distance exactly (9/9), all nine passed the trusted validator,
and **two advance the `weight-8 × unrestricted` board**:

- **[[124,14,11]]** — a(x)=1+x+x⁴+x⁷ over R₆₂, ℓ=3; kd²/n ≈ 13.6
- **[[178,24,13]]** — a(x)=1+x⁹+x¹⁰+x¹² over R₈₉, ℓ=5; kd²/n ≈ 23.9

Both are witness-backed upper bounds (gate refutation at ~8k RIS trials found
nothing lighter); no exact or WL-equivalent duplicates. Staged under
`research/candidates/ub-*` with verdicts; reconstruction script committed at
`research/ub_sweep.py`. Not promoted to `codes/`, no PR — human review decides.

## What worked

- The resumable arXiv metadata harvester (`research/literature/`) caught this
  paper on its first incremental run after a 7-day gap; the abstract's
  "single-polynomial search" framing plus an explicit Table I with exact
  supports made it a cheap, high-confidence reconstruction target.
- Pre-screening dominance *before* validation (same-(n,k) board check, then
  full Pareto at the row's weight class) correctly predicted 7 of 7
  dominated rows and both advances, so no validation budget was wasted.

## What did not

- The UB family's weight-6 rows ([[252,12,14]], [[254,14,14]], [[372,14,12]],
  [[378,12,22]]) all lose to existing board weight-6 GB records — the board's
  weight-6 cell is deep. Its high-rate weight-8 rows ([[146,20,8]],
  [[204,36,8]], [[234,26,14]]) lose to designed-divisor GB points.
- The [[1022,56,21]] flagship exceeds the n ≤ 700 verifier cap; not runnable
  here.

## Calibration note

The paper's distances (computed with external distance libraries) matched our
surrogate witnesses at 4k–12k trials on all nine rows, including d=22 at
n=378. That is consistent with the trial-depth floors fieldnote: mid-size
(n ≤ 400) balanced-weight GB-family codes are far easier to witness honestly
than the large-n BB codes that needed ~1M trials.

## Reopen conditions

The UB restriction is a 1-parameter slice of GB space. A natural follow-up is
a symmetry-reduced sweep *around* the two advancing rows (same n, ℓ, and
nearby a(x) supports) to see whether the paper's rows are locally optimal or
just first found — the same mutation playbook that produced the [[666,150,95]]
advance. Stop if a bounded local sweep (≤ a few thousand supports) finds only
dominated variants.
