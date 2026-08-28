---
title: "GALA reconstruction: 2 gate-passing board advances from arXiv:2608.07431"
date: 2026-08-24
author: "@mathysrennela"
model: "ox-alpha (Zed agent)"
topics: [gala, quasi-cyclic, literature-mining, weight-12, high-rate]
status: staged
related:
  - 2026-08-23-univariate-bicycle-sweep.md
  - 2026-08-15-dead-ends-and-leads.md
---

## Summary

Reconstructed the abelian-bottom GALA rows of arXiv:2608.07431 (Yang,
Duckering, Dua — QuEra) from the paper's explicit group-ring generator tables
(Table S5). All eight reconstructible rows reproduce the paper's n and k
exactly; **three advance their board cell and two passed the trusted gate**
(the third is a duplicate of an existing board entry):

- **[[136,34,12]]** — C17 bottom, L=8, J=3; kd²/n ≈ 36.0. Gate: passed.
- **[[192,40,12]]** — C16 bottom, L=12, J=5; kd²/n ≈ 30.0. Gate: passed.
- [[132,30,12]] and [[672,336,12]] — already on the board verbatim (seeded
  2026-08-07 from the same paper, authored by Yang/Duckering/Dua); our
  reconstructions are parameter-identical and correctly flagged as duplicates.

All distances are witness-backed upper bounds agreeing with the paper's
exactly certified values; a maintainer can re-certify with
`verify/certify.py`. The two advancing rows were subsequently promoted to
`codes/` with full notes and the complete reconstruction recipe embedded in
each: see `notes/136-34-12.md` (Reproduction section) and
`notes/192-40-12.md`.

## What worked

- The paper publishes complete machine-recoverable generators for every
  certified instance (Tables S3–S5), including group products, sector
  involutions, and shift lists — the same "explicit table" property that made
  the UB sweep cheap.
- The construction reduces, for trivial/abelian non-abelian factors, to plain
  block-circulant quasi-cyclic codes over F₂[Z_{L/2} × C_m]: buildable with
  ~40 lines on top of the kit's numpy core. No new algebra needed.
- Convention check that saved the campaign: block-circulant row i is
  `roll(base, +i)` (not −i). With the wrong sign the parents are not
  orthogonal and CSS fails loudly — a fast false-negative test.

## What did not

- The other five abelian rows ([[136,36,8]], [[228,46,12]], [[248,62,12]],
  [[280,70,12]], [[328,82,12]]) are dominated by existing board entries
  ([[136,38,8]], [[228,82,12]], [[232,62,12]], [[276,98,14]]).
- The flagship non-abelian rows ([[480,240,10]], [[1752,880,14]],
  [[2232,1120,16]] from Tables S3/S4) need semidirect / direct product lifts
  with non-trivial S3/S4 tops. First attempt at [[480,240,10]] from its
  Table S3 generator row produced a valid CSS code with matching n,k but
  girth 4 instead of the paper's ≥6 (d ≤ 4 vs certified 10) — all 576 block
  orderings of the published monomial multisets were tried. The per-row
  active set Γ is NOT specified in the tables; for trivial tops it is
  irrelevant (all commutators vanish — which is why [[672,336,12]]
  reconstructs perfectly), but for S3 tops the ansatz depends on Γ.
  [[1752,880,14]] and [[2232,1120,16]] exceed the n ≤ 700 verifier cap;
  not runnable here regardless of construction fidelity.

## Reopen conditions

Implement DPG lifts with NON-TRIVIAL tops: enumerate S3-top ansatzes per
Lemma 4 of the paper (exhaustive at k=3), sample bottoms greedily for
girth ≥ 6, screen with the fast RIS backend. Two blockers to resolve first:
(1) obtain the paper's per-row active sets Γ or their search code (a
provisional patent is filed; code availability unclear) — without Γ the S3
ansatz is underdetermined and our [[480]] attempt shows the naive reading
fails; (2) verify our top-permutation direction convention against a
known-good non-abelian instance. The prize is [[480,240,10]] (eff ≈ 50,
under cap). Stop if no faithful reconstruction of any certified non-abelian
row can be produced after exhausting the Lemma-4 ansatz space.
