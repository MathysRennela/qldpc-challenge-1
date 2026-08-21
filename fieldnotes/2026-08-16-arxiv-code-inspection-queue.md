---
title: "ArXiv code reconstruction queue: explicit qLDPC rows"
date: 2026-08-16
author: "@mathysrennela"
model: "GPT-5.6 Luna"
topics: [literature-mining, arxiv, reconstruction, validation, bicycle, balanced-product]
status: review-needed
related:
  - 2026-08-15-arxiv-board-harvest.md
  - ../research/literature/README.md
---

## Purpose

Inspect and reconstruct the explicit code rows recovered from the HTML of
arXiv:2608.09115v1 and arXiv:2608.08996v1. The goal is not to copy paper
parameters into `codes/`: every row must be rebuilt, deduplicated against the
board, passed through the repository submission builder, and accepted by
`verify/validate_candidate.py` before it is a find.

Do not promote anything to `codes/` or open a PR without human review. Local
staging output is working data, not durable evidence; the reconstruction script,
paper version, table/section location, and validator receipt are the audit trail.

The upstream paper-inspection queue has been consolidated into this note. Its
metadata-first rule remains in force: inspect HTML and linked public artifacts
before PDFs or source archives, record the exact artifact and version, and stop
when a paper has no explicit finite construction, no public artifact, or only
board duplicates. The durable metadata harvest is recorded in
`research/literature/README.md` and its append-only records.

## Current evidence

One row has completed the first reconstruction pass:

- **arXiv:2608.09115v1**, Table II/III and Example 11:
  `[[66,20,7]]`, cyclic `l=33`,
  `supp(a)=[1,2,3,5,10,27,32]`,
  `supp(b)=[0,1,3,4,5,7,13,15,22,24,30,32]`.
  `research/reconstruct_2608_09115.py` rebuilds the checks and packages the
  witnesses. The trusted validator returned `passed: true`, with max check
  weight 19, no duplicate, and a witness-backed `d <= 7` on both sides. The
  paper reports exact `d=7`; the repository record remains an upper bound until
  an exact repository certificate exists.

This is a gate-fresh literature reconstruction, not yet a board submission.

## Queue A: arXiv:2608.09115v1

The paper gives cyclic support data in Tables II/III. Reconstruct rows in this
order, applying cheap matrix/rank/weight checks before witness searches:

1. `[[66,20,7]]` — complete; retain as the reference implementation.
2. `[[90,18,8]]`, `[[90,20,7]]`, `[[170,32,14]]` — highest likely board value,
   but check raw max check weight and existing-board dominance first.
3. `[[42,16,6]]`, `[[42,14,6]]`, `[[70,16,7]]`, `[[54,16,6]]` — moderate-size
   rows that may fit sparse cells.
4. `[[170,18,8]]`, `[[170,18,7]]`, `[[170,16,7]]`, `[[170,10,8]]`,
   `[[170,10,6]]`, `[[170,10,7]]` — larger rows; prioritize only if their
   checks remain within the repository cap and they are not dominated.
5. The remaining Table I/II/V rows: `[[46,2,8]]`, `[[66,2,9]]`,
   `[[66,4,8]]`, `[[66,6,8]]`, `[[90,16,6]]`, `[[90,18,6]]`,
   `[[42,12,4]]`, `[[62,12,4]]`, `[[50,2,9]]`, `[[54,2,9]]`,
   `[[70,2,10]]`, `[[78,2,9]]`, and `[[90,2,10]]`.

For each row, preserve whether the paper's distance is exact, a bound, or a
search result. Do not convert the paper's exact claim into the repository's
`exact` confidence without the repository certification path.

## Queue B: arXiv:2608.08996v1

The HTML Supplementary Information gives host group, subgroup, protograph, and
local-term data. Reconstruct only after confirming the group-action convention
and the repository's qubit/check ordering. Prioritize:

1. `[[288,18,18]]` — likely strongest direct weight-9-plus comparison.
2. `[[234,28,18]]` — high rate and moderate size.
3. `[[368,18,16]]` — genuine non-normal subgroup action.
4. `[[288,16,18]]` and `[[224,22,16]]`.
5. `[[256,18,16]]`, `[[384,32,16]]`, and `[[248,12,18]]`.
6. Upper-bound rows only after exact/witness feasibility is understood:
   `[[336,12,20]]`, `[[400,16,<=22]]`, `[[384,16,<=24]]`,
   `[[336,24,<=24]]`, `[[378,18,<=27]]`, `[[336,28,<=20]]`,
   `[[384,18,<=28]]`, `[[384,14,<=28]]`, `[[390,32,<=32]]`,
   `[[390,36,<=30]]`, `[[396,8,<=32]]`, and `[[306,8,<=25]]`.

The paper's overall-weight convention is not automatically the repository's
raw maximum check weight. Recompute both X/Z row supports and all claimed
parameters directly from the assembled matrices.

## Per-row checklist

- Pin arXiv identifier and version, plus Table/Example/Supplementary location.
- Record the paper's `(n,k,d)` and distinguish exact distance from upper bounds.
- Rebuild checks using a tracked script or an explicit finite-group recipe.
- Assert CSS commutation, recomputed `n/k`, row-weight cap, and index convention.
- Deduplicate against `codes/*.json` before witness work.
- Use `research/kit/submit.make_submission`; never run an unpersisted witness
  search. Save local working output before validation.
- Run `uv run python verify/validate_candidate.py <staged-file>`.
- Write a submission note only for a gate-fresh improvement, citing the pinned
  paper and tracked reconstruction script.

## Stop condition

Stop this queue when every explicit row in both papers is either reconstructed
and classified against the board, or has a recorded concrete blocker such as
ambiguous group-action convention, unsupported matrix artifact, excessive
resource cost, or board duplication. Do not spend distance-confirmation budget
on rows already dominated after normalization.

## Reconstruction results (2026-08-16)

The tracked scripts `research/reconstruct_2608_09115_batch.py` and
`research/reconstruct_2608_08996_234.py` implement the first reproducible
batch. All staged documents below were built with `research/kit/submit.py` and
accepted by `verify/validate_candidate.py`; paper distances are kept separate
from repository witness-backed upper bounds.

### Gate-passing, board-advancing

- arXiv:2608.09115v1, Table III: `[[90,20,7]]` (max check weight 31),
  `[[42,16,6]]` (22), `[[42,14,6]]` (24), and `[[54,16,6]]` (18).
  Each had no exact or WL-equivalent duplicate and the validator reported
  `board_advancing: true`.
- arXiv:2608.09115v1, Table III: `[[66,20,7]]` remains the reference
  reconstruction from `research/reconstruct_2608_09115.py`, also validator
  passing and board advancing.
- arXiv:2608.08996v1, Supplementary Information: `[[234,28,18]]` over
  `Z_13 x Z_9`, max check weight 10. It had no duplicate and the validator
  reported `board_advancing: true`.

Staged paths are local working output under `research/candidates/`; they are
not board submissions or durable prose evidence.

### Classified blockers and dominated rows

- `[[90,18,8]]` and `[[70,16,7]]` reconstruct with max check weight 38;
  `[[170,18,8]]` reconstructs with max check weight 56. These exceed the
  repository cap of 32 and were not sent through witness validation.
- The reconstructed `[[170,18,7]]`, `[[170,16,7]]`, `[[170,18,6]]`,
  `[[170,10,8]]`, and `[[170,10,6]]` rows all passed the validator but were
  reported as dominated by existing board entries. They are retained only as
  classification evidence; no further confirmation budget is justified.
- The final `[[170,10,7]]` staging attempt exceeded the bounded 180-second
  reconstruction run during witness generation. It has not been classified.
- arXiv:2608.08996v1 rows requiring non-normal subgroup actions (`[[368,18,16]]`,
  `[[336,12,<=24]]`, `[[248,12,18]]`, `[[396,8,<=32]]`, and
  `[[306,8,<=25]]`) remain blocked because the current research kit has no
  tracked balanced-product/coset assembler for the supplied group-action data.
  The already represented `[[288,16,18]]` row is not duplicated.

No candidate has been promoted to `codes/` or submitted for review. The
explicit-row queue is now complete for the first reconstruction tranche; the
remaining rows are either classified blockers, dominated entries, or require a
new assembler. Reopen this note only when a pinned artifact or new construction
mechanism changes one of those classifications.
