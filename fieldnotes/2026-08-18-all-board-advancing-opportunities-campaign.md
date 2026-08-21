---
title: "Campaign: pursue every Pareto-frontier opportunity"
date: 2026-08-18
author: "@mathysrennela"
model: "GPT-5.6 Luna"
topics: [research-plan, board-advancing, pareto-frontier, leaderboard, campaign-management]
status: planned
related:
  - 2026-08-18-pareto-frontier-and-board-worthiness.md
  - 2026-08-18-pareto-frontier-submission-preparation.md
  - 2026-08-18-weight-gap-frontier-campaign.md
  - ../research/AUTORESEARCH.md
  - ../TRACKS.md
---

## Mission

Run a standing campaign to pursue **every possible way to advance the current
Pareto frontiers**. The campaign is not trying to produce one global winner or
optimize one headline metric. Every point that is non-dominated in at least one
applicable board cell is a legitimate target, whether it is a small code, a
higher-rate tradeoff, a higher-distance tradeoff, a lower-weight point, or a
locality-qualified point.

The campaign may use whichever method is necessary: known code families,
parameter searches, algebraic constructions, geometric layouts, code
transforms, cross-breeding, literature reconstruction, new search algorithms,
or genuinely new constructions. No method is excluded because it differs from
previous work. If several independent candidates advance different tradeoffs,
all of them are successful results; none must be number 1 on a leaderboard.

“All possible” is the standing research mandate, not a claim that one finite
run can prove the mathematical universe exhausted. A campaign round makes the
mandate actionable by mapping every currently identifiable opening, pursuing
it with known and exploratory methods, and recording unresolved openings for
continued work.

## Eligibility

Use the definition in
`fieldnotes/2026-08-18-pareto-frontier-and-board-worthiness.md`. A candidate is
eligible for the campaign result set only when:

1. the trusted verifier returns `passed: true`;
2. CSS commutation, ranks, parameters, check weights, locality, and evidence
   pass the applicable gates;
3. the candidate is not dominated in at least one applicable cell; and
4. its provenance and witnesses are retained for audit.

Evaluate every nested weight and locality cell defined by the verifier. One
code may advance several cells. Record every advancing cell and the incumbent
point or tradeoff against which it is non-dominated. `kd^2/n` is context, not a
replacement for the four-axis comparison. Distances remain witness-backed
upper bounds unless an exact certificate exists.

## Opportunity records

The unit of work is an opportunity record, not a construction family. At the
start of every round, create or update one record for every identifiable
frontier opening. Each record should contain:

```text
opportunity_id
board snapshot and applicable cell(s)
current frontier/incumbent points
minimum target inequalities in n, k, d, w, and locality
known routes and unexplored discovery questions
current status and next action
search budget and last search result
evidence and validation requirements
```

The opportunity map must cover every cell and every open tradeoff direction:
lower `n`, higher `k`, higher `d`, lower `w`, and more restrictive locality.
Do not collapse it to one score, one cell, one family, or one preferred route.

The map has two parallel tracks:

- **Exploitation:** pursue every known family, parameter basin, mutation,
  cross-breed, layout, and published construction that could reach an opening.
- **Exploration:** actively look for mechanisms outside the existing route list,
  including new representations, transformations, search operators,
  mathematical structures, and literature or external-code audits.

A scheduling choice may use expected progress, compute cost, or method
readiness, but scheduling priority must never make an eligible opportunity
ineligible or remove it from the map.

## Campaign round

Run the following procedure against a frozen board snapshot:

1. **Map the frontier.** Compute the non-dominated points in every applicable
   cell and create or update all opportunity records.
2. **Set targets.** For each record, state the incumbent tradeoff, the axis or
   axes to improve, and the minimum parameters needed for a non-dominated point.
3. **Assign methods.** Give each opening at least one known route and, where
   needed, an exploratory discovery question.
4. **Search in increments.** Screen cheaply, preserve search counts and seeds,
   and maintain a next action for every active record.
5. **Escalate methods.** When a route stalls, change family, representation,
   layout, algebraic construction, optimization method, reconstruction method,
   or search tooling. Develop a missing method when no existing route can reach
   the target.
6. **Persist witnesses.** Use the research kit's submission path so both CSS
   directions, provenance, and the lowest logical found are saved. Never keep
   only printed distance output.
7. **Trusted-validate survivors.** Only `verify/validate_candidate.py` returning
   `passed: true` establishes a campaign find.
8. **Compare globally.** Recompute dominance and locality placement from each
   validated artifact in every applicable cell.
9. **Retain every advance.** Keep all eligible candidates, including
   co-frontier points and candidates that lose on `kd^2/n` but win another
   tradeoff.
10. **Update the map.** Record results, evidence, next actions, and unresolved
    discovery questions before starting the next route.

A failed route is calibration for that route, not a negative result for the
opportunity. Record its family, parameter range, trials, seeds, filters, and
best result. Mark the route exhausted only for its tested method and scope;
reopen the opportunity with a new method or hand it to another route.

## Opportunity statuses

Use these statuses so the campaign can distinguish progress from abandonment:

- `mapped`: identified but not yet searched;
- `active`: has a current search or discovery action;
- `advanced`: produced a validated, evidence-backed frontier candidate;
- `blocked`: requires a missing artifact, tool, theorem, or implementation;
- `exhausted-for-current-method`: the declared route and budget are complete;
- `superseded`: a board update removed the opening; or
- `reopened`: a new board state or method made the opening relevant again.

No opportunity is permanently closed merely because one familiar family failed.
A later board update can supersede an old target and create new openings, so
frontier mapping must be rebuilt rather than resumed unchanged.

## Evidence and preparation

For every retained candidate, preserve the committed artifact location,
generator or reconstruction method, checksum or seed where available, trusted
verdict, witnesses for both CSS directions, distance confidence, applicable
cells, and exact dominance comparison. Local ignored staging output is not
durable evidence and must not be cited as if it were in a future PR.

Before promotion, rerun the trusted checks on the exact artifacts intended for
the PR. If a witness search lowers a distance, preserve the corrected witness,
update the candidate's claim and filename, and rerun the frontier comparison.
Accepted but dominated candidates may remain for provenance, but they are not
campaign advances unless a later board snapshot makes them non-dominated.

## Round completion and repetition

A round is complete when:

- every current cell has been inspected;
- every identifiable frontier opening has an opportunity record and status;
- every active or blocked record has a documented next action or unblocker;
- all promising witnesses have been persisted;
- every validator-passing advancement has been retained; and
- unresolved methods and discovery questions are recorded for the next round.

The recurring loop is:

```text
freeze board -> map all frontier openings -> assign known and exploratory methods
       -> search and escalate -> persist witnesses -> trusted-validate
       -> compare every cell -> retain every advance -> update statuses
       -> rebuild after the board changes
```

The campaign continues indefinitely. A new board entry can remove an opening,
create new nested-cell opportunities, or make a previously dominated candidate
relevant. Historical negative results bound only the methods and regions they
actually examined; they do not justify ignoring a new route or opportunity.

Success is therefore measured by coverage of the opportunity map and the
completeness of the evidence trail—not by finding the best code, the highest
score, or the most prominent leaderboard position.
