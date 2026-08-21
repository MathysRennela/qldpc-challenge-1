---
title: "How to read the board: Pareto frontiers and board-worthy codes"
date: 2026-08-18
author: "@mathysrennela"
model: "GPT-5.6 Luna"
topics: [leaderboard, pareto-frontier, board-worthiness, submission-guidance]
status: reference
related:
  - ../TRACKS.md
  - ../CONTRIBUTING.md
---

## The short version

A code is on the **Pareto frontier** when no other code in the same board cell is
at least as good in every tracked quantity and strictly better in one. A code is
**board worthy** when it is verified, evidence-backed, and adds a new
non-dominated point to at least one applicable cell.

This is deliberately different from choosing one global winner. Quantum codes
trade physical size, rate, distance, check weight, and locality, so a single
score would hide useful tradeoffs.

## What is compared

Within a cell, the board compares:

- `n`, the number of physical qubits: lower is better;
- `k`, the number of logical qubits: higher is better;
- `d`, the distance: higher is better; and
- `w`, the maximum check weight: lower is better.

Code A is dominated by code B if

```text
n_B <= n_A
k_B >= k_A
d_B >= d_A
w_B <= w_A
```

and at least one inequality is strict. A code is a frontier point when no code
in that cell dominates it. There can be many co-leaders: for example, a smaller
code and a larger, higher-rate code can both be frontier points when neither
wins on every axis.

The commonly displayed `kd^2/n` value is a useful sortable headline, but it does
not replace the frontier or make a cell have only one winner. It is especially
not a global score: its interpretation depends on the cell and on code size.

## Which cell is being considered?

Cells are determined by the verifier, not selected by the submitter. They are
the product of a locality class and a maximum check-weight class. The locality
class comes from the submitted layout and measured interaction radius; the
weight class comes from the largest row weight in `H_X` and `H_Z`.

The classes are nested. A weight-4 code also competes on the weight-6, weight-8,
and any-weight boards. Likewise, a single-layer 2D-local code also competes on
the bilayer and unrestricted boards. Therefore one code may advance several
frontiers, while another may be useful only in an unrestricted or higher-weight
cell.

The frontier is board-relative. Leading a cell means beating the entries
currently seeded in this repository; it does not establish that no unseeded
published code would match or beat the result.

## What counts as an advance?

Examples of a possible frontier advance include:

- the same `(n, k)` with a larger witnessed distance;
- the same `(k, d)` with fewer physical qubits;
- the same `(n, d)` with more logical qubits;
- comparable parameters at a lower maximum check weight; or
- a locality-qualified point that is not dominated in its local cell.

A candidate need not be the best code on every axis. It only needs to survive
the dominance test in one applicable cell. Conversely, a candidate with a good
headline `kd^2/n` can still be dominated if another entry is no worse in all
four tracked quantities.

## Evidence matters

A frontier claim is meaningful only after the trusted checks establish the code's
parameters, CSS commutation, check weights, and any claimed locality. A distance
witness establishes a genuine nontrivial logical operator and therefore an upper
bound, written `d<=`. It does not prove that no lighter logical exists.

Exact distance claims require a certification that rules out every lighter
logical. Large codes commonly remain witness-backed upper bounds even after
independent refutation searches fail to find a lighter operator. That is honest
and useful evidence, but it must not be described as an exact distance.

Thus, “board worthy” does not mean merely “interesting construction” or “large
`kd^2/n`.” It means:

1. the verifier accepts the submission;
2. the reported distance and locality claims have the right confidence level;
3. the code is not dominated by the current entries in at least one cell; and
4. the provenance and evidence are recorded so another researcher can audit the
   comparison.

Dominated codes may still be accepted and recorded for provenance or completeness,
but they do not advance the active frontier. The practical question before a
deep search is therefore: **which cell and which existing point does this
candidate beat, and on which axis or tradeoff?**
