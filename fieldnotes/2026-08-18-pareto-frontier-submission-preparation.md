---
title: "Pareto-frontier candidates and board-worthy submission plan"
date: 2026-08-18
author: "@mathysrennela"
model: "GPT-5.6 Luna"
topics: [pareto-frontier, board-worthiness, submission-preparation, weight-4, generalized-bicycle]
status: planned
related:
  - 2026-08-18-pareto-frontier-and-board-worthiness.md
  - 2026-08-18-weight-gap-frontier-campaign.md
  - ../TRACKS.md
  - ../CONTRIBUTING.md
---

## Purpose

Record all currently identified validator-passing candidates that are not
reported as dominated in at least one computed board cell, and define one
common preparation plan for making each of them board-worthy. This note is
intentionally **not prioritized**: every candidate below is part of the same
preparation set.

The candidates were found in local autoresearch output. The files under
`research/candidates/` are ignored staging artifacts and are **not durable
evidence**
for a future pull request. Before any candidate can be cited in submission
prose, its complete JSON, witnesses, provenance, and any required reconstruction
script must be copied into the candidate's committed PR tree and rechecked
there.

## What qualifies as a candidate here

The trusted validator already reported all candidates below as:

- `passed: true`;
- CSS, rank, parameter, and check-weight gates passing;
- no exact duplicate or WL-equivalent duplicate in the board snapshot used by
  the validator; and
- `board_advancing: true` in at least one unrestricted cell.

Distances remain witness-backed upper bounds. They are written `d<=` below and
must not be described as exact without server certification.

The frontier comparison is board-relative and must be rerun immediately before
submission because newer codes may dominate a candidate.

## Candidate set

### A. `[[666,150,d<=95]]`, maximum check weight 30

Local staging artifacts:

- `research/candidates/mutated-666-150-95-67275d626f0a1342.json`
- `research/candidates/mutated-666-150-95-67275d626f0a1342.verdict.json`

Computed parameters:

```text
n = 666
k = 150
d <= 95
w = 30
k*d^2/n = 2032.658
family = generalized-bicycle
locality = unrestricted
```

The validator reported no lighter logical in 8,000 RIS trials, no exact or WL
duplicate, and `board_advancing: true`. At the same `(n,k,w)`, this improves on
the committed `[[666,150,d<=81]]` entry. The candidate remains an upper-bound
claim and needs fresh confirmation before publication.

### B. `[[96,12,d<=4]]`, maximum check weight 4

Local staging artifacts:

- `research/candidates/weight4-mvb-finalist-1-96-12.json`
- `research/candidates/weight4-mvb-finalist-1-96-12.verdict.json`

Computed parameters:

```text
n = 96
k = 12
d <= 4
w = 4
k*d^2/n = 2.000
family = bivariate-bicycle
locality = unrestricted
```

The validator reported no lighter logical in 6,340 RIS trials and
`board_advancing: true`.

### C. `[[176,22,d<=4]]`, maximum check weight 4

Local staging artifacts:

- `research/candidates/weight4-mvb-finalist-2-176-22.json`
- `research/candidates/weight4-mvb-finalist-2-176-22.verdict.json`

Computed parameters:

```text
n = 176
k = 22
d <= 4
w = 4
k*d^2/n = 2.000
family = bivariate-bicycle
locality = unrestricted
```

The validator reported `passed: true` and `board_advancing: true`. Its
tradeoff is distinct from the other weight-4 candidates because it carries
more logical qubits at a larger block size.

### D. `[[192,6,d<=8]]`, maximum check weight 4

Local staging artifacts:

- `research/candidates/weight4-mvb-finalist-3-192-6.json`
- `research/candidates/weight4-mvb-finalist-3-192-6.verdict.json`

Computed parameters:

```text
n = 192
k = 6
d <= 8
w = 4
k*d^2/n = 2.000
family = bivariate-bicycle
locality = unrestricted
```

The validator reported `passed: true` and `board_advancing: true`. This is a
higher-distance, lower-rate tradeoff and should be compared independently from
higher-`k` weight-4 entries.

### E. `[[192,24,d<=4]]`, maximum check weight 4

Local staging artifacts:

- `research/candidates/weight4-mvb-finalist-4-192-24.json`
- `research/candidates/weight4-mvb-finalist-4-192-24.verdict.json`

Computed parameters:

```text
n = 192
k = 24
d <= 4
w = 4
k*d^2/n = 2.000
family = bivariate-bicycle
locality = unrestricted
```

The validator reported `passed: true` and `board_advancing: true`. It is not
dominated by `[[192,6,d<=8]]` because it trades lower distance for four times
the logical-qubit count at the same block size and check weight.

### F. `[[84,2,d<=9]]`, maximum check weight 4

Local staging artifacts:

- `research/candidates/weight4-mvb-finalist-5-84-2.json`
- `research/candidates/weight4-mvb-finalist-5-84-2.verdict.json`

Computed parameters:

```text
n = 84
k = 2
d <= 9
w = 4
k*d^2/n = 1.929
family = bivariate-bicycle
locality = unrestricted
```

The validator reported no lighter logical in 5,860 RIS trials and
`board_advancing: true`. Its small-`n`, high-distance tradeoff makes it a
separate possible weight-4 frontier point even though its headline score is
below 2.

## Common board-worthy preparation plan

Apply every step to every candidate in the set; no candidate is assigned a
priority in this note.

### 1. Freeze and audit the source artifact

For each candidate:

- copy the complete JSON out of ignored local staging into a committed
  candidate-specific working tree;
- preserve both X and Z witnesses exactly;
- record the source file checksum, generator parameters, support sets, and
  search seed;
- verify that the copied JSON, rather than only the local staging file, is the
  artifact used in all subsequent checks;
- identify the construction script needed to regenerate the checks and commit
  that script if it is part of the evidence trail.

No submission prose should cite `research/candidates/` as if it were a committed
artifact.

### 2. Recompute the board comparison

Against the latest `codes/*.json` snapshot:

- recompute exact GF(2) ranks and `k`;
- recompute maximum check weight;
- recompute both witnessed distances from the copied witnesses;
- check CSS commutation;
- check exact and WL-equivalent duplicates;
- evaluate every nested weight cell and the unrestricted cell;
- record the specific incumbent points that each candidate is not dominated by;
- reject or revise any candidate newly dominated by a later board entry.

A candidate's headline score is supporting context only; the submission decision
must use the four-axis dominance relation.

### 3. Reconfirm distance with independent searches

Run fresh-seed searches against both CSS directions. For the large
`[[666,150,d<=95]]` candidate, use a substantially deeper budget than the
8,000-trial validator refutation. For the smaller weight-4 candidates, use the
trusted exact certifier where computationally feasible, otherwise retain the
witness-backed `d<=` claim.

If a lighter logical is found:

- persist it through `research/kit/submit.make_submission`;
- update the candidate's distance claim and filename rather than discarding the
  lower-weight witness;
- rerun validation and the Pareto comparison.

Never call a candidate exact based only on RIS, BP+OSD, or the screening
surrogate.

### 4. Audit provenance and novelty

For each code:

- document the construction family and complete support description;
- identify whether it is a new search result, a literature reconstruction, or a
  variation of an existing board code;
- search the cited literature and public databases for the same parameters and
  supports;
- retain `literature_novelty: unverified` unless the audit establishes
  otherwise;
- include the generator and public reference needed for independent
  reconstruction.

A board-advancing result does not automatically establish literature novelty.

### 5. Prepare committed submission artifacts

For each surviving candidate, create a self-contained PR tree containing:

- one schema-valid JSON submission;
- a note following `notes/TEMPLATE.md` and naming the candidate's own
  `[[n,k,d]]` first;
- all reconstruction/search scripts required by the note, or a precise pinned
  public source and reproducible construction description;
- complete witnesses and the correct `upper_bound` confidence;
- no references to private paths, ignored staging, session URLs, or unfinished
  checklist scaffolding.

Use unique filenames if an identical `(n,k,d)` parameter tuple already exists;
the matrix fingerprint and provenance must make the new code distinguishable.

### 6. Run the contributor validation gate

Before requesting review, run the repository's normal submission path and the
trusted candidate validator on the exact files in the prospective PR tree.
Confirm that:

- all changed files are present in that tree;
- prose paths resolve in that tree;
- the JSON and note agree on `n`, `k`, `d`, weight, family, and confidence;
- the candidate remains `passed: true` and board-advancing;
- no candidate is described as certified exact without a certification artifact.

Only after all six candidates have independently completed this process should
any publication request be made. This note does not authorize promotion,
commit, branch creation, or PR publication by itself.

## Completion criteria

The preparation set is complete when every candidate has either:

1. a committed, self-contained, validator-passing PR-ready artifact whose
   current Pareto comparison is recorded; or
2. a preserved failure record explaining refutation, duplication, domination,
   provenance failure, or inability to reproduce the construction.

The six candidates are treated symmetrically: no publication order or research
priority is implied by their listing above.
