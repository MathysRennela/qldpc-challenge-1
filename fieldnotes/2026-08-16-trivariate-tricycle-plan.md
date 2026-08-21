---
title: "Investigation plan: trivariate tricycle codes"
date: 2026-08-16
author: "@mathysrennela"
model: "GPT-5.6 Luna"
topics: [research-plan, trivariate-tricycle, group-algebra, single-shot, fault-tolerant-gates]
status: planned
related:
  - 2026-08-15-dead-ends-and-leads.md
  - 2026-08-15-arxiv-board-harvest.md
  - 2026-08-16-weight4-weight6-campaign-plan.md
---

## Question

Can the trivariate tricycle (TT) construction of Jacob, McLauchlan, and Browne,
arXiv:2508.08191v2, produce a verified code that advances a current board
frontier, while also adding useful single-shot or logical-gate evidence?

Plan calibrated by reconstruction and a bounded Route A pilot.
The paper's numerical distances remain leads only; a code counts for the board
only after its own submission passes `verify/validate_candidate.py`.

## Construction to implement

For \(G=Z_\ell\times Z_m\times Z_p\), let `A`, `B`, and `C` be binary group-algebra
polynomials. Build three \(\ell mp\)-dimensional permutation-polynomial matrices
and use

\[
H_X=[A\;B\;C],\qquad
H_Z=\begin{bmatrix}0&C^T&B^T\\C^T&0&A^T\\B^T&A^T&0\end{bmatrix}.
\]

The code has \(n=3\ell mp\) data qubits. The construction should be represented
by exponent/support sets, not by hand-written dense matrices. The first
implementation must test the paper's convention against its explicit examples,
including the transpose/inverse convention for monomials and the ordering of the
three qubit blocks.

This is distinct from the repository's existing trivariate-bicycle records from
arXiv:2406.19151: those reduce to a two-block bivariate-bicycle matrix, whereas
TT codes have three data blocks and the six-block structure above. Until the
family vocabulary is extended, a TT submission should use the existing `other`
provenance tag rather than relabeling it as `generalized-bicycle`.

## Board hypotheses and priorities

### Route A: weight-6, structured `(2,2,2)` TT codes

If each of `A`, `B`, and `C` has two terms, the maximum check weights are
`weight(H_X)=6` and `weight(H_Z)=4`, so the code competes in the unrestricted,
weight-6, and weight-8 nested cells. These are the first targets because they
have the lowest checks and the paper gives a direct constant-depth physical
`CCZ` construction for them.

Search dimensions with `n=3*l*m*p <= 700`, first using small factors and then
factor triples near the cap. Fix one monomial in each polynomial to the identity
when the paper's monomial-factor equivalence permits it. Remove permutations of
`A,B,C`, global shifts, polynomial transposes, and other exact symmetries before
building matrices.

The primary screening objectives are:

- `k >= 4` and a witnessed `d >= 4` at minimum;
- a Pareto improvement in the relevant board cell, not merely a new parameter set;
- balanced `dX` and `dZ`, since TT codes naturally have asymmetric distances;
- nontrivial logical action under the paper's `CCZ` circuit where it can be
  checked independently.

The paper's examples such as `[[48,3,4]]`, `[[60,3,4]]`, and `[[90,3,5]]`
should be reconstruction/calibration points, not assumed advances. The search
must compare them with the current `codes/` frontier before spending deep
confirmation budget.

### Route B: weight-8 cup-product extensions

The paper's structured weight-4 polynomial form, combined with two weight-2
polynomials, gives a maximum check weight of 8. This is potentially more
interesting for the weight-8 unrestricted cell, but the paper reports distance-2
logical qubits for its nontrivial `CCZ` examples. Treat those examples as a
negative-control regime unless gauge fixing produces a valid CSS code with a
checkable distance at least 3.

Search only after Route A is calibrated. For each candidate, record the complete
side-distance profile and the number of distance-2 logicals. Do not rank a code
using a high distance on one side if the other side has collapsed to 2. Explore:

- products `(1+g)(1+a)` with `g^2=1`;
- even-order orbit sums from the paper's cup-product lemma;
- one structured weight-4 polynomial plus two weight-2 polynomials;
- gauge-fixed variants only if the resulting stabilizer checks and logical
  action are explicitly reconstructible.

A nontrivial `CCZ` action is useful metadata, but it does not substitute for a
board-valid distance witness.

### Route C: weight-9 random and structured triples

Weight-3 `A`, `B`, and `C` gives weight-9 X checks and weight-6 Z checks, placing
the code in the any-weight cell. The paper's `[[72,6,6]]`, `[[180,12,8]]`, and
`[[432,12,12]]` examples are useful reconstruction tests, but their reported
figures are not expected to beat the current high-rate any-weight records on
headline efficiency.

Only run this route if Routes A/B reveal a structural signal, or if a cheap
screen finds a candidate with a genuine Pareto advantage at `n <= 700`. Prefer
structured supports with low collision counts and connected Tanner graphs over
blind random polynomial triples. A plausible search budget is 10,000--50,000
screened triples per dimension regime, with a cheap rank/weight filter and a
low-trial distance screen before deep confirmation.

## Search and confirmation ladder

1. Implement and unit-test the constructor against the paper's explicit examples.
   Check dimensions, CSS commutation, `k`, row weights, and the paper's block
   convention.
2. Build a symmetry-reduced enumerator for Routes A and B, and a seeded random
   sampler for Route C. Persist the generator parameters and all screening
   records; never retain only a printed distance.
3. Screen using exact GF(2) rank, maximum check weight, connectivity, and the
   repository surrogate. The surrogate distance is an upper bound and is only a
   ranking signal.
4. For every plausible frontier candidate, call `submit.make_submission` so both
   side witnesses are embedded in the staged JSON. Keep the complete candidate
   even if a later check fails.
5. Run `verify/validate_candidate.py` on each staged document. Only `passed: true`
   is a find. Keep confidence as `upper_bound` unless an exact certificate is
   separately obtained.
6. Re-run the strongest candidates with substantially deeper, fresh-seed
   searches. For large candidates, use the repository's established caution that
   shallow searches can overestimate distance; do not promote a candidate merely
   because the paper reports the same number.
7. Compare each validated candidate with the current Pareto frontier in its
   computed locality/weight cells. Stop treating a dominated reconstruction as a
   board advance.

The first campaign should reserve compute approximately as follows:

- 20%: constructor and paper-example calibration;
- 35%: symmetry-reduced `(2,2,2)` and structured weight-8 enumeration;
- 25%: targeted weight-9 search if calibration supports it;
- 20%: deep witness confirmation and provenance/reproduction checks.

## Evidence to preserve

For every paper reconstruction, record the arXiv version, table/equation, values
of `(l,m,p)`, the three polynomial support sets, the resulting `(n,k)`, both
observed witnesses, and the validator verdict. Report the paper's claimed
`dX,dZ` separately from the repository's witnessed upper bounds.

For a new candidate, preserve:

- the exact generator parameters and random seed;
- screening trials and both side witnesses;
- rank, CSS, maximum-weight, and connectivity checks;
- the validator JSON/verdict;
- whether the candidate is a frontier point or merely non-dominated in the
  local search archive;
- any independently checked meta-check or `CCZ` property.

No paper path, local staging path, or unpublished artifact should be cited as
board evidence. If a reconstruction script becomes necessary for reproducibility,
it must be committed in a later implementation change or the note must state the
complete algebraic recipe.

## Stop conditions and possible outcomes

Stop Route A after a symmetry-reduced sweep over the selected factor triples if
no candidate beats the current weight-6 frontier and no new distance/gate
structure appears. Stop Route B if all nontrivial cup-product survivors have
`d <= 2` or fail to produce a valid gauge-fixed construction. Stop Route C if a
calibrated search reaches its stated budget without a frontier candidate or if
all survivors are dominated by existing weight-9/any-weight codes.

A positive outcome is a staged, validator-passing code with a board-relative
frontier improvement. A useful negative outcome is a fieldnote with the exact
searched dimensions, polynomial weights, sample counts, deepest trials, and
collapse reasons. A paper example that reconstructs correctly but is dominated
should be retained as calibration evidence, not presented as a new board record.

## Decision

The constructor and bounded Route A pilot exist, but this note does not yet
contain an independent TT result table or a validator-backed frontier advance.
Keep the route planned and retain its TT-specific construction details here;
use the shared packaging, validation, and stop-rule protocol from
`fieldnotes/2026-08-16-weight4-weight6-campaign-plan.md`. Reopen only with a
symmetry-reduced TT result or another distinct mechanism, not by repeating the
cyclic fixed-divisor slice.

## Results of the initial campaign

`research/reconstruct_tt.py` reproduced the paper's `[[72,6,6]]`, `[[180,12,8]]`,
`[[432,12,12]]`, `[[48,3,4]]`, and `[[90,3,5]]` examples: all exact `(n,k)` and
check weights matched, and all five staged documents passed the trusted validator.
The validator classified the first three as unrestricted weight-9plus and the last
two as unrestricted weight-6; every one was explicitly `board_advancing: false`.

`research/search_tt_route_a.py` generated 200 identity-normalized `(2,2,2)`
samples across ten factor triples, using 120 screening trials. Exact-rank and
minimum filters left 21 survivors. The five finalists were packaged with 1,200
trials each and all passed validation, but all were dominated: the best observed
profiles were `[[54,6,3]]`, `[[81,9,3]]`, and `[[96,6,4]]`. This closes only this
bounded random pilot, not the full `(2,2,2)` family. Route B's cup-product search
is deferred pending a symmetry-reduced Route A sweep; Route C is currently
calibration-only because the paper examples are dominated.

## Reproduction starting point

Read `research/AUTORESEARCH.md`, `TRACKS.md`, and `CONTRIBUTING.md` before running
the campaign. Use the existing group-algebra and submission-tool patterns in
`research/kit/group_algebra.py` and `research/kit/submit.py`, but add a dedicated
three-block constructor rather than forcing TT codes into the two-block API.
Stage every candidate under the repository's ignored candidate workflow and run
the trusted validator before making any claim.
