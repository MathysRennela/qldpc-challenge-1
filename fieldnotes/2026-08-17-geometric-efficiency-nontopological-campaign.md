---
title: "Campaign plan: geometric efficiency in non-topological families"
date: 2026-08-17
author: "@mathysrennela"
model: "GPT-5.6 Luna"
topics: [research-plan, geometric-efficiency, locality, non-topological]
status: parked-dominated
related:
  - 2026-08-15-dead-ends-and-leads.md
  - 2026-07-01-open-directions-snapshot.md
  - ../TRACKS.md
---

## Objective

Find a non-topological qLDPC construction whose checks and qubit placement are
co-designed well enough to earn a useful local-2D track and geometric
efficiency. This is not a post-hoc attempt to place an arbitrary unrestricted
matrix on a grid.

## Board context

The board has many unrestricted algebraic and product codes but relatively few
honest layouts. Prior experiments found that layout-only reoptimization
produced duplicates and that tested algebraic weight-8 layouts had very small
geometric efficiency. Those results rule out blind placement searches, not a
construction with an intrinsic bounded-radius embedding.

## Hypothesis

Twisted/periodic algebraic families, bilayer lifted products, or quotient-based
products may retain algebraic distance benefits while keeping interaction
radius bounded. The useful target is a new local Pareto point, especially in
weight-4 or weight-6, rather than a high-rate code with a long-range layout.

## First experiment

1. Select one family with an explicit translation, quotient, or product
   geometry; do not mix unrelated families in the first round.
2. Generate checks and coordinates jointly, including single-layer and
   two-layer embeddings where the construction supports them.
3. Require one coordinate per qubit, honest site spacing, and no layer
   over-capacity.
4. Measure locality with the repository's submission builder and verifier;
   do not infer the class from a visual embedding.
5. Rank by computed locality class, `g`, check weight, and Pareto status.
6. Deduplicate against existing checks and WL-equivalent records before deep
   confirmation.
7. Package and validate every candidate that might advance a local cell.

The first budget should be a small structured sweep, not a large random
search: roughly 100--300 construction/layout variants with a fixed family and
an explicit symmetry reduction.

## Success criteria

A candidate must pass the trusted validator and improve a computed local-2D
frontier. A promising exploratory threshold is a validator-passing `w<=6`
code with a materially improved `g` over the relevant local baseline at
comparable `n`; a merely valid layout for an already dominated unrestricted
code is not enough.

Any claim based on witnessed distance must remain an upper-bound claim.

## Stop conditions

Stop the route if the best layouts exceed the locality caps, if all accepted
layouts are duplicates, or if geometric efficiency remains far below the local
frontier after the bounded sweep. Reopen only with a new intrinsic geometry,
cellulation, layer mechanism, or construction family—not another placement
optimization of the same matrices.

## Evidence to preserve

Preserve the construction parameters, coordinate-generation rule, layer count,
minimum site spacing, measured interaction radius, bounding box, density,
check-weight data, exact ranks, both witnesses, seeds, deduplication results,
and the full validator verdict. Coordinates must be part of the candidate
artifact whenever they are cited as evidence.

## Decision

The existing-layout audit produced two unrestricted duplicates and one
unresolved indexing blocker, so this co-designed route is now active. The first
flagship calibration probe used the repository's validated bilayer planar
builder at `L=6` and produced `[[72,8,d<=4]]`: trusted validation passed with
`local-2d-bilayer`, but the candidate was not board-advancing and was dominated
by `[[60,8,d<=6]]`, `[[62,10,d<=6]]`, and `[[72,12,d<=6]]`. This confirms the
co-designed locality pipeline but not a useful frontier point.

The first structured sweep is complete and is parked under the campaign stop
condition. The validated flagship family was generated with joint bilayer
coordinates at three sizes:

- `6x8`: `[[96,8,d<=4]]`, local-2D bilayer, no frontier advance;
- `8x8`: `[[128,8,d<=6]]`, local-2D bilayer, exact duplicate of `128-8-6`;
- `8x10`: `[[160,8,d<=6]]`, local-2D bilayer, no frontier advance.

All three passed structural and locality validation, but existing local entries
dominated every result. The family therefore does not justify a larger budget
without a new support, boundary, or layer mechanism. Do not expand this sweep or
revisit it as a placement optimization.
