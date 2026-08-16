---
title: "Research campaign: dead ends and actionable leads"
date: 2026-08-15
author: "@mathysrennela"
model: "GPT-5.6 Luna"
topics: [negative-results, research-plan, 2bga, bicycle, geometric-efficiency, database-mining]
status: active
related:
  - 2026-07-01-confirmation-is-the-bottleneck.md
---

## TL;DR

The main lesson is to stop broad random searches in tested families and spend the
next budget on targeted constructions, already gate-fresh candidates, and new
geometric topology. Here, a *gate-fresh* candidate has passed the repository's
trusted validator, but its distance may still be only a witnessed upper bound.
Negative results below are bounded by the stated family and search depth; they are
not universal impossibility results.

## Dead ends and boundaries

- **Distance estimates are unsafe at large `n`.** Examples such as
  `[[392,6,32]] -> 26`, `[[294,8,20]] -> 19`, `[[400,8,50]] -> 44`, and
  `[[336,12,36]] -> 24` were refuted by deeper searches. At `n=1008`, estimates
  flat through 16k trials later fell 17--34% at 60k. Use roughly 1M trials/side
  as the packaging floor for large candidates, and call a witnessed distance an
  upper bound unless it is certified. See
  `fieldnotes/2026-07-01-trial-depth-floors.md`.

- **Small-subgroup coset 2BGA plateaued.** Ten tested `(G,H)` families
  (including PSL(2,7)/C2, PSL(2,8)/C3, PSL(2,11)/C3, A6/C3, and S6/C4), about
  730k k-filtered samples, annealing, and 252 local restarts produced typical
  `d=2`, maximum `d=6`. The `[[180,20,14]]` point was locally exhausted through
  all 1-element and 447,859 correlated 2-element moves. Reopen only with a
  different subgroup scale or construction mechanism.

- **The original GAP coset criteria and random prime-order 2BGA search were
  weak filters.** The `|N_G(H)/H| >= 6` campaign ran about seven hours without a
  competitive code; the targeted `|N/H|=84` route mostly selected `|H|=1`
  degeneracies. Random supports at prime orders 251--347, weights 8--14, found
  no survivor even after relaxing to `k>=4,d>=20`. This closes only the tested
  random-support strategy.

- **Blind GAP sweeps have diminishing returns.** Orders 120--124 produced 1,235
  candidates and 371 with `eff>15`, but none advanced after 10k trials and none
  beat the `eff~38`, `n=240` bar. The older order-60--120 work produced eight
  advances; more blind sampling in the same regime is low value.

- **Several simple geometric families are closed in their tested models.** The
  tested `6.6.6` patches found no faithful `m>=4` generator; single-layer
  weight-8 planar/`4.8.8` builds either failed to tile or had `d<=2`; algebraic
  weight-8 single-layer survivors had `g~0.013--0.020`; random weight-4
  hypergraph-product screening gave `g_screen~0.002`; and layout-only
  reoptimization produced duplicates. These results do not rule out a new
  topology or cellulation.

- **The current holey/dense surface routes do not scale naively.** The D-rule
  `d=5` hole pattern was exactly refuted, including tested `23x26` and `25x28`
  margins. The corrected dense `d=3` search collapsed 129 holes to a locally
  maximal 103-hole construction (`[[676,110,3]]`); fusing beyond the existing
  five-patch ladder failed CSS or did not improve `g`. At `r=sqrt(2), rho=1`,
  beating `g=1.564` requires `k*d^2/n > 1.564`. The tested weight-4 hole family
  has `k/n<=0.08`; recorded weight-6/8 packing floors are useful barriers but
  not proofs.

- **The codetables.de CSS mine is negative in the sampled region.** After fixing
  the codetables parser, 200 detail pages with `n=12..25,k=4..9`
  parsed as non-CSS; a further live sample through `n=110` was 0/8 CSS. The
  source appears to contain additive GF(4) stabilizer codes. Stop broad CT-0b
  fetching unless a CSS-aware extraction mechanism is added.

- **Harvest audits removed most low-value candidates.** The remaining clear
  Strategy A survivors are `[[162,36,4]]`, `[[128,20,14]]`, and `[[254,14,16]]`;
  `[[684,8,100]]` duplicates the board's `[[684,8,85]]`. QECDB records
  `[[85,53,5]]` and `[[89,67,4]]` exceed the schema check-weight cap (40--44
  versus 32), so they cannot be submitted unchanged. The mirror did find useful
  material, but broad database fetching is no longer the bottleneck.

- **Low-weight AMC3 and incomplete Kasai reconstruction are not immediate wins.**
  AMC3's initial weight-2 sweep produced only `n=72--114`, `k=3--6`, `d=3--5`,
  with efficiency around `0.7`; AMC4 mostly reproduced known paper-scale
  points. Kasai PP reconstructions beyond `[[516,178,20]]` lack usable published
  witnesses for several records, so they should not be packaged from distance
  claims alone.

## Leads worth exploring

1. **Finish the multivariate/trivariate bicycle sweep first.**
   A validated `build_tb` implementation reconstructs all 14 Table 2 rows from
   arXiv:2406.19151 using `{x^a,y^b,z^c}` with `z=xy`. The three gate-fresh
   literature reconstructions are `[[112,2,10]]`, `[[112,8,5]]`, and
   `[[144,2,12]]`; they contain witnesses but are upper bounds and need notes,
   provenance review, and a standalone recheck of the `[[144,2,12]]` duplicate
   anomaly. Add a `sample_tb` search path, sweep weight-4 then weight-5 monomial
   sets, and stop when the weight-4 frontier stagnates. Do not spend deep
   confirmation on dominated weight-6/7 rows.

2. **Package the gate-fresh Strategy A survivors before discovering more.**
   Recheck stored witnesses and provenance, then write notes and PRs for
   `[[128,20,14]]` (weight-8 2BGA, unrestricted, efficiency `30.625`) and
   `[[254,14,16]]` (weight-6 cyclic generalized bicycle over `Z_127`, efficiency
   `14.110`). `[[162,36,4]]` (BB over `Z9xZ9`, weight 6, efficiency `3.556`)
   is already staged. Keep each distance claim labeled as an upper bound unless
   the trusted verifier provides certification.

3. **Extend AMC outside the exhausted slice.** Use a validated AMC constructor for
   AMC3 weight-3/4 elements, AMC4 nonuniform generator weights, and noncyclic
   abelian groups. Add a quotient-lattice shortest-cycle heuristic as a cheap
   RIS prefilter. Keep exact certification focused on `n<=200`.

4. **Finish the Kasai PP structural prefilter.** Add mixed-collision, 4-cycle,
   and 6-cycle
   hyperplane deduplication plus distance-obstruction templates. Calibrate
   against Kasai's table, including the expected `20/26` structural pass rate
   and named failures `qc_590_240_12` and `qc_1524_766_14`; then reconstruct
   witnesses before claiming additional records.

5. **Change geometric topology, not merely scale existing layouts.** Run the
   unexecuted dense-packed surface sweep: 100--300 five-patch adjacency variants
   (chain, `3+2`, `2+2+1`), up to 500 local mutations around `[[101,5,5]]`, and
   a `k=6` extension if the marginal qubit cost stays below about 20. Every
   survivor must pass the repository's submission builder and trusted validator.
   Explicit stop conditions are important because naive larger fusion already
   failed to improve `g`.

6. **Keep three geometry routes alive, with narrow tests.** Build a genuinely
   non-hole weight-4 cellulation; revisit weight-6 hexagonal patches only with a
   faithful `m>=4` generator; test single-parity cluster holes at `d=5`; and
   try boundary shaping on the `[[656,114,3]]`-style `26x26` geometry while
   recomputing locality radius with the verifier. These are unexecuted leads,
   not positive evidence.

7. **Scale ZSZ-LP only after improving its filter.** A meaningful next run is
   500--1,000 pairs per side, `ell1` up to 31, `ell2` up to 5, group orders
   coprime to 6, and `ell1 >> ell2`; send only survivors to BP+OSD or MILP.
   Do not scale the current 30-pair, 50-classical/100-quantum-trial regime
   unchanged.

8. **Use static features and GPU work as infrastructure, not as a new search
   family.** Candidate spectral gap, Fiedler localization, short-cycle counts,
   rank profiles, degree distributions, and group invariants can prioritize
   confirmation. GPU effort is most justified for batched `distance_rand`, tiered
   confirmation, and feature extraction; small graph filters and MILP are not
   expected to benefit materially.
