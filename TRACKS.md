# Tracks and leaderboards

A quantum code is not a single number. You trade physical qubits n, logical
qubits k, distance d, stabilizer check weight, and geometric locality against
each other, and separately you care how the code decodes under noise. So there
is no one leaderboard.

The categories below are organized into **three layers**, kept deliberately
separate because they answer different questions:

```
LAYER 1 — PRIMARY TRACKS   the leaderboards: hard hardware constraints
          locality-class × check-weight-class
          membership is COMPUTED by the verifier (not self-declared)
          ranked on the (n, k, d) Pareto frontier + the kd^2/n figure

LAYER 2 — FAMILY TAGS      provenance: how the code was built. Filter/browse
          only; never ranked, because family is not checkable from H.

LAYER 3 — VERIFIED FLAGS   machine-checked badges: exact-d, css, the locality
          flags. Only things the verifier can prove.

SEPARATE EVALUATED AXES    decoding LER (server-computed) and claimed
          fault-tolerance properties (unverified). Never primary tracks.
```

Why the separation: a single code is typically a weight-6, 2D-bilayer,
bivariate-bicycle, exactly-certified code all at once. Mixing "how heavy are the
checks" (a hardware fact the verifier measures) with "what family is it" (a
provenance label it cannot measure) into one flat list of tracks makes
membership a self-declared, gameable, double-counting field. Layering fixes
that: you compete on constraints, you are *tagged* by family, you are *badged*
by proven properties.

## Layer 1 — Primary tracks

A primary track is a cell in a grid of two **nested hardware-constraint axes**.
The verifier already measures both quantities from the submission, so **track
membership is derived, not trusted** — you do not pick your tracks, the checker
computes them.

### Axis 1: geometric locality class

Single-layer is stricter than bilayer is stricter than unrestricted; a code that
meets a stricter class automatically qualifies for the looser ones.

| Class | Verifier predicate |
|---|---|
| `local-2d-single` | a `locality` block with `layers == 1`; every qubit placed; all checks within the stated interaction radius |
| `local-2d-bilayer` | a `locality` block with `layers <= 2` (the flip-chip regime); checks within radius |
| `unrestricted` | no layout constraint (the any-connectivity qLDPC regime) |

Geometric locality is a genuine hardware constraint, not a soft preference: a
naive 2D-local layout of a high-rate qLDPC code carries prohibitive overhead, so
the single-layer / bilayer / unrestricted classes are physically distinct
regimes (arXiv:2404.17676 = PRX Quantum 6 010306; arXiv:2308.07915). The
interaction radius is recomputed by the verifier as the maximum check diameter
against the stated coordinates, so the class is machine-checkable.

### Axis 2: stabilizer check-weight class

Weight-4 is stricter than weight-6 is stricter than weight-8; nesting works the
same way.

| Class | Verifier predicate |
|---|---|
| `weight-4` | max row weight of H_X and H_Z <= 4 |
| `weight-6` | <= 6 (the canonical bivariate-bicycle threshold) |
| `weight-8` | <= 8 (the natural relaxation across planar and tile codes) |

LDPC membership is exactly "the Hamming weight of each row and column of H_X and
H_Z is bounded by a constant" (Breuckmann-Eberhardt, PRX Quantum 2 040101) — a
trivial GF(2) scan. Thresholds 4 / 6 / 8 are the literature's natural cut points:
the surface code is weight-4, the gross code is weight-6 (arXiv:2308.07915), and
planar / tile codes reach weight-8 (arXiv:2504.08887, arXiv:2504.09171), with
real seed codes at each.

### How membership and nesting work

A submission **auto-populates every cell whose constraints it satisfies**.
Because both axes are nested, a strong `local-2d-single` `weight-4` code also
appears on (and can top) the bilayer, unrestricted, weight-6 and weight-8 boards
— as it should, having met a strictly harder bar. A code with no `locality`
block competes only on the `unrestricted` boards. This is the code-tables
"cell view": a grid keyed by constraints, each populated cell a board.

### Ranking within a track

Two views of the same data:

- **Frontier view**: the Pareto-optimal codes over (n, k, d). A code is on the
  frontier if no other in the track dominates it (no other has n' <= n, k' >= k,
  d' >= d with at least one strict). There can be many co-leaders.
- **Cell view**: a grid keyed by (k, d); each cell holds the smallest known n,
  with a challenger history. This is the view people usually screenshot.

`kd^2/n` is a sortable column and a reasonable per-track headline number, but it
never collapses the frontier into one rank. It is the literature-sanctioned
figure of merit precisely because it is tied to a proven bound — the
Bravyi-Poulin-Terhal result that any 2D-local stabilizer code satisfies
`kd^2 = O(n)` (arXiv:0909.5200, PRL 104 050503; restated arXiv:2409.15203;
generalized to `kd^(2/(D-1)) = O(n)` in PRX Quantum 2 040101). The planar-BB
work uses the same `kd^2/n` figure to claim an order-of-magnitude edge over the
surface code (arXiv:2504.08887). For the `local-2d-bilayer` class the current
best known efficiency is `kd^2/n ~ 9.75`, the `[[323,14,15]]` tile code
(arXiv:2606.19482), a concrete bar to beat.

Two conventions matter:

- **Distance confidence is orthogonal to the track**: `d<=` (a self-certified
  upper bound from an explicit logical-operator witness) versus `d=` (a
  server-certified exact value). An exact record outranks an equal upper bound.
- **n is the code length** (number of data qubits). The gross code is
  `[[144,12,12]]`, i.e. n = 144, even though a syndrome-extraction layout uses
  288 physical qubits including ancillas. Ancilla overhead is a separate,
  simulation-level concern; the `kd^2/n` figure uses the code length.

### The track grid, with seed codes

These cells have verified seed codes from the literature. (Several seed
distances are construction/search results, not certified exact — they are
carried as `d<=` until a certificate is supplied; see the flags below.)

| Cell (locality × weight) | Seed codes | Source |
|---|---|---|
| `unrestricted` × `weight-6` | gross code `[[144,12,12]]`, `[[72,12,6]]`; generalized-bicycle codes | arXiv:2308.07915; arXiv:2203.17216 |
| `unrestricted` × `weight-8` | coset two-block (2BGA) codes | arXiv:2606.17268 |
| `local-2d-bilayer` × `weight-6` | gross code `[[144,12,12]]` as a flip-chip bilayer | arXiv:2308.07915 |
| `local-2d-single` × `weight-6` | planar BB `[[78,6,6]]`, `[[107,7,7]]`, `[[268,8,12]]`; tile `[[288,8,12]]` | arXiv:2504.08887; arXiv:2504.09171 |
| `local-2d-single` × `weight-8` | planar BB `[[282,12,14]]`; tile `[[288,8,14]]`, `[[512,18,19]]` | arXiv:2504.08887; arXiv:2504.09171 |
| `local-2d-single` × `weight-4` | surface / toric codes (baseline) | standard |

Heavier-than-8 codes and asymptotically-good qLDPC families (k = Theta(n),
d = Theta(n); arXiv:2111.03654) live on the `unrestricted` boards if someone
submits a concrete instance; they are not given their own hard track, since "n
regime" cuts are arbitrary and good-code families have essentially no small
submittable instances today.

## Layer 2 — Family tags

Construction family is **self-declared provenance** and cannot be recovered from
the parity-check matrix, which is exactly why it is a tag and not a track:
tagging confers no ranking advantage, so there is nothing to game. Tags are
filterable across every primary track. The Error Correction Zoo
(errorcorrectionzoo.org) is the precedent: it keeps the family hierarchy
(parent / child / cousin) in the browse layer, not in any ranking.

Tag vocabulary: `bivariate-bicycle`, `generalized-bicycle`, `2bga-coset`,
`hypergraph-product`, `lifted-product`, `balanced-product`, `quantum-tanner`,
`tile`, `topological` (`surface` / `toric` / `color`), `other`.

(Family-specific [[n,k,d]] regime claims for the lifted-product and
hypergraph-product families did not survive source verification during the
research behind this scheme; pin those to a primary source before baking them
into seed metadata.)

## Layer 3 — Verified flags

Badges the verifier can prove from H, the layout, or a certificate — nothing
self-reported:

- `exact-d`: the distance is certified exact (MILP/SAT, the `d=` tier), versus
  an `upper_bound` witness (`d<=`). This is the codetables.de lower/upper-bound
  convention: distance is shown as a bound, and the certified-exact case is
  marked distinctly.
- `css`: CSS commutation H_X H_Z^T = 0 holds (always true in schema v0.1).
- `local-2d-single` / `local-2d-bilayer`: the geometric-locality flags, derived
  from the checked layout (these double as the Axis-1 track membership).

Note: abelian-vs-non-abelian construction structure is **not** a verified flag —
it cannot be read off H and must come from provenance — so it lives in Layer 2
as part of the family tag, not here.

## Separate evaluated axes (not primary tracks)

Some properties matter enormously but cannot be cheaply, trustlessly verified,
so they are kept off the primary boards:

- **Decoding (LER)** under code-capacity / phenomenological / circuit-level
  noise. This is *server-computed* by the evaluator, not claimed by the
  submitter, so it cannot be gamed — which is why it can be an evaluated axis
  without being a self-declared track. See `decode/`.
- **Fault-tolerance / application properties**: single-shot decoding,
  transversal and fold-transversal logical gates, magic-state cost,
  circuit-level threshold, logical clock speed. These need simulation or proof,
  so under a verifiable-now scope they are surfaced only as **unverified, cited
  claims** in `provenance.notes`, clearly badged as such — never as ranked
  tracks. (The headline "gross code uses ~288 vs ~3000 surface-code qubits" is
  itself a circuit-level *simulation* result, arXiv:2308.07915 — the clearest
  illustration of why this whole class stays off the primary boards.)

## What this scheme avoids

1. **Double-counting / relabel-gaming** — family is a tag, not a board, so you
   cannot enter many leaderboards by renaming your construction.
2. **Self-report gaming** — primary membership is computed from H and the
   layout, not declared.
3. **Single-winner brittleness** — Pareto frontier plus a bound-tied efficiency
   figure, never one collapsed headline number.
4. **Overclaimed distance** — certified `exact-d` is distinct from a witness
   `upper_bound`.
5. **Untrustworthy FT claims** — simulation/proof properties are relegated to
   clearly-unverified axes.

## Open questions to settle

1. **Locality predicate, precisely**: what formally separates `single-layer`
   from `bilayer` (BB's criterion is "a degree-6 graph that is two edge-disjoint
   planar subgraphs"), and how many long-range edges, if any, a class tolerates.
2. **Exact-d certificate format and resource bound** the verifier will accept,
   plus an audit of which seed distances are already certified vs upper bounds.
3. **Where to pin** the generalized-bicycle / 2BGA-coset / balanced-product /
   quantum-Tanner parameter regimes, given the failed lifted/hypergraph-product
   formula checks.

## Baselines and provenance

The boards are seeded with published codes attributed to their authors — the
gross code and its relatives (arXiv:2308.07915), the planar BB codes of Liang,
Eberhardt, Chen (arXiv:2504.08887), and the tile codes (arXiv:2504.09171) —
so every new submission is measured against the published state of the art
rather than an empty board.

---

## Appendix: sources

This scheme was synthesized from a multi-source literature review (25 sources
fetched, 110 claims extracted, 25 adversarially verified — 23 confirmed, 2
refuted). Sources are grouped by the research angle they informed. Primary
arXiv papers are preferred; where a title is not given the source is referenced
by ID and role.

### Construction-family taxonomy and parameter regimes

- arXiv:2308.07915 — Bravyi, Cross, Gambetta, Maslov, Rall, Yoder,
  "High-threshold and low-overhead fault-tolerant quantum memory" (the
  bivariate-bicycle "gross code" family).
- arXiv:2111.03654 — Panteleev, Kalachev, "Asymptotically Good Quantum and
  Locally Testable Classical LDPC Codes" (STOC 2022).
- PRX Quantum 2, 040101 — Breuckmann, Eberhardt, "Quantum Low-Density
  Parity-Check Codes" (review; the LDPC and kd^alpha bound definitions).
- errorcorrectionzoo.org/c/qcga — Error Correction Zoo, quantum
  group-algebra / two-block code family page.
- errorcorrectionzoo.org/c/balanced_product — Error Correction Zoo, balanced
  product code family page.

### 2D-local hardware constraints and efficiency bounds

- arXiv:0909.5200 — Bravyi, Poulin, Terhal, "Tradeoffs for reliable quantum
  information storage in 2D systems" (PRL 104, 050503; the kd^2 = O(n) bound).
- arXiv:2409.15203 — bound on 2D-local [[n,k,d]] stabilizer codes (restates
  kd^2 <= O(n)).
- arXiv:2404.17676 — geometric locality of qLDPC codes (PRX Quantum 6, 010306).
- arXiv:2504.08887 — Liang, Eberhardt, Chen, planar open-boundary
  bivariate-bicycle codes (the kd^2/n efficiency figure; weight-6 and weight-8
  families).
- arXiv:2504.09171 — tile codes (2D-local planar construction; weight-6 and
  weight-8 seed codes).

### Code tables and leaderboard design practice

- codetables.de — Grassl, "Bounds on the minimum distance of linear codes and
  quantum codes" (the lower/upper-bound distance convention).
- errorcorrectionzoo.org/about — Error Correction Zoo design (domain → kingdom →
  code hierarchy; the code graph of relations).
- PRX Quantum 6, 010306 — published version of the geometric-locality review
  above.

### Cheap machine-verification of CSS codes / distance certificates

- arXiv:2606.12445
- arXiv:2408.10743
- arXiv:2509.21469
- arXiv:2203.04262
- arXiv:2404.17703
- arXiv:2208.05353

### Fault-tolerance properties (the non-cheaply-verifiable axis)

- arXiv:2508.08191
- arXiv:2407.03973
- arXiv:2202.06647
- arXiv:1805.09271
- arXiv:2409.18175
- arXiv:2504.13043

### Additional references cited above (from the existing baselines / kit)

- arXiv:2203.17216 — Panteleev, Kalachev, generalized / quasi-cyclic bicycle
  (generalized-bicycle) codes.
- arXiv:2606.17268 — Aydin, Tamo, Barg, coset two-block (2BGA) codes.
- arXiv:2606.19482 — tile code `[[323,14,15]]` (the `local-2d-bilayer`
  efficiency bar, kd^2/n ~ 9.75).

### Refuted during verification (NOT relied on)

- That asymptotically-good qLDPC codes come specifically from lifted product
  over non-abelian groups (1-2 vote against).
- The exact hypergraph-product parameter formula
  `[[n1*n2 + r1*r2, k1*k2, min(d1,d2)]]` (1-2 vote against).

Both are excluded from the seed metadata; family-specific parameter claims for
the lifted-product and hypergraph-product families should be re-sourced before
use.
