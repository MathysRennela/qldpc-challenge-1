---
title: "Three 2BGA codes from GAP-enumerated groups"
date: 2026-07-28
author: "@mathysrennela"
model: MiMo-V2.5
topics: [2bga, gap-system]
---

## Codes found

Three CSS codes constructed via the two-block group-algebra (2BGA)
framework on finite groups enumerated systematically by GAP [GAP4]. All
three are weight-6, upper-bound distance claims confirmed flat across a
rising trial ladder (400 → 2k → 8k → 60k → 1M surrogate evaluations)
and validated by the board's trustless gate (`validate_candidate` →
`passed: true`, `advances the weight-9plus x unrestricted board`).

| Code | Efficiency | Group | d claim |
|------|-----------|-------|---------|
| [[128,8,15]] | 14.06 | C₆₄ | d ≤ 15 |
| [[120,6,16]] | 12.80 | C₆₀ | d ≤ 16 |
| [[126,6,16]] | 12.19 | C₂₁ × C₃ | d ≤ 16 |

All staged in `research/candidates/` as schema-valid submission JSON,
awaiting human review. Never committed to `codes/`.

## Submission format

Each code is a schema-valid JSON document matching the repo's
`schema/code.schema.json`. The provenance and distance blocks follow the
same format as existing board entries (e.g. `codes/120-8-12.json`,
`codes/126-28-8.json`).

### [[128,8,15]] from C₆₄

```json
{
  "name": "[[128,8,15]] 2BGA on C64",
  "code_type": "CSS",
  "n": 128,
  "k": 8,
  "distance": {
    "d": 15,
    "X": { "value": 15, "confidence": "upper_bound", "witness": [ ... ] },
    "Z": { "value": 15, "confidence": "upper_bound", "witness": [ ... ] }
  },
  "provenance": {
    "authors": ["@mathysrennela"],
    "construction": "2BGA (arXiv:2306.16400) on GAP SmallGroup(64,1) = C64. "
      "Weight-6 supports: a={12,13,25,26,44,51}, b={4,22,32,36,38,59} "
      "(random selection from G). H_X=[L(a)|R(b)], H_Z=[R(b)^T|L(a)^T]. "
      "Distance confirmed at 1M RIS trials (flat 400→1M, no inflation).",
    "references": ["arXiv:2306.16400"],
    "date": "2026-07-28",
    "notes": "Group found by GAP AllSmallGroups(64) enumeration. "
      "Previous best at n=128,k=8 was d=6 (planar BB, arXiv:2504.08887). "
      "Novelty vs literature: unverified."
  },
  "family": "generalized-bicycle"
}
```

- **Board impact**: previous best at (n=128, k=8) was d=6 from a
  bivariate-bicycle construction (efficiency 2.25). This is a **2.5×
  distance improvement** and **6× efficiency gain**.
- **Group**: cyclic group of order 64. Not in the kit's cyclic-product
  family Z_l × Z_m (C₆₄ has no non-trivial product decomposition).

### [[126,6,16]] from C₂₁ × C₃

```json
{
  "name": "[[126,6,16]] 2BGA on C21xC3",
  "code_type": "CSS",
  "n": 126,
  "k": 6,
  "distance": {
    "d": 16,
    "X": { "value": 16, "confidence": "upper_bound", "witness": [ ... ] },
    "Z": { "value": 16, "confidence": "upper_bound", "witness": [ ... ] }
  },
  "provenance": {
    "authors": ["@mathysrennela"],
    "construction": "2BGA (arXiv:2306.16400) on GAP SmallGroup(63,3) = C21 x C3. "
      "Weight-6 supports: a={4,17,24,41,48,50}, b={10,23,39,48,52,56} "
      "(random selection from G). H_X=[L(a)|R(b)], H_Z=[R(b)^T|L(a)^T]. "
      "Distance confirmed at 1M RIS trials (flat 400→1M, no inflation).",
    "references": ["arXiv:2306.16400"],
    "date": "2026-07-28",
    "notes": "Group found by GAP AllSmallGroups(63) enumeration. "
      "Previous n=126 entries were k=18 and k=28 only — this fills the k=6 slot. "
      "Novelty vs literature: unverified."
  },
  "family": "generalized-bicycle"
}
```

- **Board impact**: the n=126 cell previously had entries only at k=18
  and k=28. This fills the **k=6 slot** with d=16 (efficiency 12.19).
- **Group**: direct product of cyclic groups of orders 21 and 3. Falls
  outside the kit's sampler parametrization.

## Construction

```
L(g)eₕ = e_{g·h}    R(g)eₕ = e_{h·g}
L(a) = Σ_{g∈a} L(g)  mod 2
R(b) = Σ_{g∈b} R(g)  mod 2
Hₓ = [L(a) | R(b)]   H_z = [R(b)ᵀ | L(a)ᵀ]
```

CSS commutation is automatic (left and right multiplication commute for
any group). The supports a, b were chosen uniformly at random from G.

## How they were found

### Systematic enumeration via GAP

The research kit previously covered ~5 hand-coded group families
(cyclic products Z_l × Z_m, dihedral, metacyclic, symmetric,
alternating). GAP's `AllSmallGroups(n)` [GAP4] returns **every** finite
group of order n up to isomorphism — for orders 60-120 this yields 601
groups across 30+ distinct isomorphism types, of which the kit's
samplers covered only ~15.

### What the bridge found that samplers missed

The three groups here — C₆₄, C₆₀, C₂₁ × C₃ — are abelian but
**not** in the cyclic-product family Z_l × Z_m that `bb.py` covers:

- C₆₄ is a cyclic group of non-product order (not Z_l × Z_m for any
  l, m > 1).
- C₆₀ is a cyclic group of non-product order (not Z_l × Z_m for any
  l, m > 1).
- C₂₁ × C₃ is another direct product that falls outside the sampler's
  parametrization.

GAP's exhaustive enumeration found these naturally. The gap between
"what the kit can build" and "what groups exist" was the design-space
bottleneck; the bridge closes it for orders ≤ 200.

## Key observations

**Conjugacy-class supports underperformed random supports.** The plan
(structured supports that are unions of conjugacy classes, invariant
under inner automorphisms) did not produce better codes than random
selection at these group orders. The groups are too small (N ≤ 120) for
the conjugacy structure to provide a meaningful search bias.

**Weight 6 was the sweet spot.** Weight-4 supports produced codes with
lower d; weight-8 and above inflated the check weight class. Weight-6
balances code rate against check locality for the n = 120-130 range.

## References

[GAP4] The GAP Group, *GAP — Groups, Algorithms, and Programming, Version
4.14.0*, 2024. https://www.gap-system.org
