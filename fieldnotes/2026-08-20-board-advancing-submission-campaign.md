---
title: "Submission-first campaign: turn existing advances into a board entry"
date: 2026-08-20
author: "@mathysrennela"
model: "GPT-5.6 Luna"
topics: [submission, board-advancing, literature, research-plan, campaign-management]
status: publication-review
related:
  - 2026-08-18-pareto-frontier-submission-preparation.md
  - 2026-08-17-cross-breed-codes-campaign.md
  - 2026-08-17-geometric-efficiency-nontopological-campaign.md
  - 2026-08-17-existing-code-layout-audit.md
  - 2026-08-16-trivariate-tricycle-plan.md
  - 2026-08-15-dead-ends-and-leads.md
  - ../CONTRIBUTING.md
  - ../TRACKS.md
---

## Objective

Submit at least one validator-passing, board-advancing code. The immediate
problem is not a shortage of candidate ideas: the fieldnotes already record
many candidates that passed the trusted validator and advanced a computed board
cell. The immediate problem is failure to convert those results into a
self-contained, reviewable submission.

This fieldnote therefore prioritizes completion over another broad search. New
research is allowed only when the current submission queue has been processed
or when it offers a materially faster route to a board-advancing code. Repeating
an exhausted search neighborhood is explicitly out of scope.

This is now an authorized contributor-driven submission campaign. The first
submission pass is complete: two self-contained candidates were validated and
opened as separate pull requests. The remaining gate is GitHub verification and
human review; the automated publication gate has now resolved successfully for both submissions.

## Campaign update — 2026-08-20

The submission queue was compared against the current board. The five weight-4
bivariate-bicycle candidates were duplicates of existing board entries. The
`[[666,150,d<=95]]` candidate and the `[[312,10,d<=48]]` candidate were
board-dominated by better existing entries, so neither was submitted.

Two literature reconstructions remained credible board advances and were
validated with the trusted validator, including persisted witnesses and
provenance notes crediting Solar Pro 4 (Upstage AI):

- `[[64,18,d<=8]]`, a Lin--Pryadko 2BGA database reconstruction, is in
  [PR #668](https://github.com/unitaryfoundation/qldpc-challenge/pull/668).
- `[[66,20,d<=7]]`, a cyclic bicycle reconstruction from
  [arXiv:2608.09115](https://arxiv.org/abs/2608.09115), is in
  [PR #669](https://github.com/unitaryfoundation/qldpc-challenge/pull/669).

The prose and `verify` checks for both PRs pass. The automated publication gate
is complete; only maintainer review/merge remains.

### Actionable next step

The automated gate is complete on [PR #668](https://github.com/unitaryfoundation/qldpc-challenge/pull/668)
and [PR #669](https://github.com/unitaryfoundation/qldpc-challenge/pull/669): both
`prose` and `verify` pass. The remaining publication action is maintainer review
and merge; keep both PRs open until one is accepted. If a reviewer requests a
change, make it on the exact PR tree and rerun the gate without discarding either
persisted witness.

## Stage B — cross-breed high-rate mechanisms — PARKED (TO BE DONE LATER)

Stage A is audited and closed as a candidate-selection stage: five weight-4
bivariate-bicycle records were duplicates, `[[666,150,d<=95]]` and
`[[312,10,d<=48]]` were dominated, and the two literature advances are in PRs.
The cross-breed should be kept for later: reconstruct the `[[666,150,d<=79]]` / `Z_333` and corrected
`[[674,86,d<=89]]` / `Z_337` records, verify their exact ranks, CSS commutation, support weights, and
stored witnesses, then use those pinned supports for the planned support-transfer
search around `(8,14)`, `(10,14)`, `(12,14)`, `(14,14)`, and `(16,14)`.
Every survivor must be packaged through `research/kit/submit.py` and passed to
`verify/validate_candidate.py`; no screen-only result is a find.

## Stage C — existing-code layout audit — PARKED

The layout audit is parked after two structurally valid but unrestricted
duplicates and a twisted-torus candidate blocked by missing quotient labeling.
No further post-hoc placement work should be done on those entries.

## Stage D — co-designed local-2D families — PARKED

The co-designed flagship sweep is complete and parked: `6x8`, `8x8`, and `8x10`
variants all passed locality validation but were dominated, with the `8x8`
variant an exact duplicate of `128-8-6`. Do not increase the budget for this
family without a new support, boundary, or layer mechanism.

The next campaign must therefore be selected from a genuinely different
construction route; a valid local layout alone is not a find.

## Current opportunity set

### A. Existing validator-passing candidates — first priority **DONE**

The following candidates were reported as `passed: true` and
`board_advancing: true` in the cited fieldnotes. Their local JSON files under
`research/candidates/` are ignored staging output and are not durable evidence.
Each candidate must be copied into a prospective committed submission tree,
rechecked there, and either prepared for review or assigned a preserved failure
record.

#### Weight-4 bivariate-bicycle candidates

- `[[96,12,d<=4]]`
- `[[176,22,d<=4]]`
- `[[192,6,d<=8]]`
- `[[192,24,d<=4]]`
- `[[84,2,d<=9]]`

These are attractive first submission targets because they are small enough for
stronger independent distance checking and exact certification where feasible.
They cover distinct `(n,k,d,w)` tradeoffs, so they must not be collapsed to a
single headline score.

#### Large generalized-bicycle candidate

- `[[666,150,d<=95]]`, maximum check weight 30

This candidate has a potentially important score improvement, but it requires
deep fresh-seed confirmation. The claim must remain `d<=95` unless an exact
certificate exists. At `n=666`, a shallow validator result is not sufficient
publication evidence.

#### Literature and database reconstructions

The following were also reported as validator-passing and board-advancing, or
as gate-fresh records requiring the same submission review:

- arXiv:2608.09115v1: `[[66,20,d<=7]]`, `[[90,20,d<=7]]`,
  `[[42,16,d<=6]]`, `[[42,14,d<=6]]`, and `[[54,16,d<=6]]`;
- arXiv:2608.08996v1: `[[234,28,d<=18]]`;
- Lin--Pryadko 2BGA database: `[[64,18,d<=8]]`, `[[70,8,d<=10]]`,
  `[[72,10,d<=9]]`, `[[72,8,d<=10]]`, and `[[196,12,d<=17]]`;
- other Strategy A/GAP reconstructions: `[[128,20,d<=14]]`,
  `[[254,14,d<=16]]`, and `[[162,36,d<=4]]`;
- additional GAP 2BGA results from orders 60--120, including
  `[[128,8,d<=15]]`, `[[140,8,d<=16]]`, `[[144,8,d<=16]]`,
  `[[144,6,d<=18]]`, `[[132,6,d<=17]]`, `[[136,6,d<=17]]`,
  `[[120,6,d<=16]]`, and `[[126,6,d<=16]]`.

The list is a review queue, not a claim that every item is still non-dominated
on today's board. The board comparison must be recomputed from the current
`codes/` snapshot before selecting a submission.

## Submission-first execution order

### Step 1: select the cheapest credible winner

Inspect the existing staged artifacts and choose a candidate using this order:

1. still board-advancing against the current board;
2. complete checks, both witnesses, and reproducible provenance available;
3. smallest practical confirmation cost;
4. clearest construction and lowest risk of a literature or duplicate issue.

The default first candidates are the small weight-4 codes, followed by the
small literature/database reconstructions. Do not spend the first submission
slot on `[[666,150,d<=95]]` if a smaller candidate can complete the gate sooner.
Keep the large candidate in the queue for deeper confirmation rather than
letting it block all publication progress.

### Step 2: make the artifact self-contained

For the selected candidate:

- copy the complete JSON, including both witnesses, out of ignored staging;
- preserve the generator/support description, seed, and source checksum;
- commit the reconstruction or generation script when it is needed to reproduce
  the checks;
- pin the literature source and version for literature-derived candidates;
- write a note following `notes/TEMPLATE.md`, stating the candidate's own
  `[[n,k,d]]` first;
- use `d<=` and `upper_bound` unless exact certification exists;
- remove references to ignored staging paths, private paths, session URLs, and
  unfinished checklist scaffolding.

Every path named in the note must exist in the prospective PR tree or be a
public pinned source. The staging directory is working output, never the audit
trail.

### Step 3: rerun the gate on the exact submission tree

Run the normal contributor validation path against the copied files, including:

- schema and parameter agreement;
- CSS commutation and exact ranks;
- maximum check weight and locality classification;
- both persisted witnesses;
- exact and WL-equivalent duplicate checks;
- current Pareto comparison in every nested applicable cell;
- prose/path checks.

If a deeper search finds a lighter logical, preserve that witness, lower the
candidate's distance claim and filename, and rerun the comparison. Do not throw
away a refuting witness.

### Step 4: submit the first survivor

As soon as one candidate is self-contained, validator-passing, and still
board-advancing, stop searching for a supposedly better candidate and prepare
that candidate for human review/publication under the contributor workflow.
The campaign succeeds with one valid board advance; it does not require
processing every candidate first.

## Secondary research queue

These routes are included because they were identified in the fieldnotes, but
none may displace the submission-first step without a concrete reason.

### Queued/planned construction campaigns

1. **Cross-breed high-rate mechanisms.** Reconstruct the `N=333` and `N=337`
   designed-divisor baselines, then transfer support and dimension mechanisms
   between them. Search both supports and support splits around `(8,14)`,
   `(10,14)`, `(12,14)`, `(14,14)`, and `(16,14)`. A candidate counts only after
   trusted validation and a current Pareto advance.

2. **Existing-code layout audit.** Select 10--20 codes with an intrinsic torus,
   quotient, planar, translational, or product geometry. Reconstruct natural
   coordinates, measure locality with the verifier, and retain only layouts
   that create a local Pareto point. Do not use arbitrary coordinate cramming.

3. **Non-topological geometric families.** After the layout audit, test one
   co-designed bounded-radius family with a small structured sweep. Generate
   several sizes and jointly generate checks and coordinates. A single
   favorable finite-size layout is not evidence of scaling.

4. **Scalable `g>1`.** Keep parked until a concrete local family survives the
   existing-layout audit. Test at least two increasing sizes before claiming a
   scaling result.

5. **Read-only research MCP.** Implement only the context/read layer first:
   board metadata, frontiers, recent activity, fieldnote search, and schema
   requirements. Controlled wrappers come later and must delegate to the
   existing research kit and trusted validator; no new verifier or arbitrary
   execution path is needed for the submission objective.

## Open leads to investigate after the first submission

- Finish the multivariate/trivariate bicycle sweep with `sample_tb`, beginning
  with weight-4 and then weight-5 monomial sets. Resolve the unexplained
  `[[144,2,d<=12]]` duplicate anomaly and prepare only rows that remain
  non-dominated.
- Complete the trivariate-tricycle Route A sweep with symmetry reduction after
  the paper reconstructions. Defer cup-product Route B unless Route A shows a
  structural signal; keep Route C weight-9 searches calibration-only unless a
  cheap screen finds a genuine Pareto target.
- Extend AMC beyond the exhausted slice: AMC3 weight-3/4 elements, AMC4
  nonuniform generator weights, and noncyclic abelian groups, using the
  quotient-lattice shortest-cycle heuristic as a prefilter.
- Finish the Kasai product-protocol structural prefilter, including mixed
  collisions, 4-cycles, 6-cycles, and calibration against the named table
  rows/failures before reconstructing further witnesses.
- Run the unexecuted dense-packed surface variants: five-patch adjacency
  patterns, bounded local mutations around `[[101,5,5]]`, and a `k=6`
  extension only if its qubit cost remains competitive.
- Test a genuinely new geometry rather than scaling failed hole patterns:
  non-hole weight-4 cellulations, faithful weight-6 hexagonal patches,
  single-parity cluster holes at `d=5`, and boundary shaping near the
  `[[656,114,3]]` geometry.
- Improve the ZSZ-LP filter before scaling it to the planned 500--1,000 pairs
  per side. Do not repeat the existing small, weakly filtered run.
- Reconstruct the remaining explicit literature rows only when their blocker
  is removed: in particular, the non-normal-subgroup balanced-product/coset
  rows from arXiv:2608.08996.
- Classify the timed-out `[[170,10,d<=7]]` reconstruction and finish the
  remaining high-value Lin--Pryadko database rows if they are still
  non-dominated.
- Re-mine old low-trial artifacts at honest confirmation depths, preserving
  any lower-weight witnesses and updating claims rather than trusting old
  distance floors.

## Anti-loop rules

The following routes are exhausted for their tested scope and must not simply
be repeated:

- the current `N=337` degree-64 local mutation sweep;
- the current `N=333` divisor-preserving local mutation sweep at weight 28;
- small-subgroup coset 2BGA on simple/almost-simple groups;
- blind GAP sampling in already exhausted order ranges;
- blind layout optimization of existing matrices;
- the tested hole-scaling and patch-fusion variants;
- the tested codetables.de CSS-mining strategy;
- the completed bounded trivariate-tricycle random pilot;
- the completed `N=43`, degree-14 weight-6 slice.

Reopen one of these only with a named new mechanism, implementation, factor
range, topology, or external artifact. A larger budget for the same operator
is not a new mechanism.

## Definition of completion

This campaign is complete when either:

1. one self-contained candidate has passed the trusted validator on the exact
   prospective submission tree and remains board-advancing, after which it is
   handed to the contributor publication workflow; or
2. every candidate in the first-priority queue has a preserved failure record
   identifying refutation, domination, duplication, provenance failure, or a
   concrete reproduction blocker.

The preferred outcome is the first one. Research expansion is secondary to
putting one verified advance on the board.
