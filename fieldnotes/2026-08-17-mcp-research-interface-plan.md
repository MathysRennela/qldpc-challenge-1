---
title: "Implementation plan: MCP interface for qLDPC research"
date: 2026-08-17
author: "@mathysrennela"
model: "GPT-5.6 Luna"
topics: [research-plan, mcp, agent-interface, reproducibility, validation]
status: planned
related:
  - ../AGENTS.md
  - ../research/AUTORESEARCH.md
  - ../CONTRIBUTING.md
  - 2026-08-17-existing-code-layout-audit.md
---

## Question

Would a Model Context Protocol (MCP) interface make the qLDPC challenge easier
for research agents to use without weakening the repository's validation and
publication boundaries?

Yes, if MCP is treated as a typed coordination layer over the existing board,
research kit, CLI, and trusted verifier. It should not become a second
implementation of code validation or a generic shell/Python execution service.

This plan deliberately excludes branch creation, commits, pushes, pull requests,
and publication approval. Existing MCP integrations already cover those actions;
this repository-side interface only needs to expose research context and bounded
research computations.

## Objective

Provide agents with a stable, machine-readable interface for:

1. understanding the current board and research record;
2. selecting a target frontier and avoiding documented dead ends;
3. screening construction families with reproducible budgets;
4. packaging candidates with preserved witnesses and provenance;
5. running the trusted validation gate; and
6. staging validated survivors for human review.

The MCP server must make the safe autoresearch workflow easier, not make it
possible to bypass it.

## Design principles

- **The repository remains the source of truth.** MCP delegates to existing
  functions and commands rather than reimplementing rank, CSS, distance, schema,
  locality, or frontier logic.
- **Validation is authoritative.** A candidate is a find only when the existing
  `verify/validate_candidate.py` result contains `passed: true`.
- **Witnesses are durable artifacts.** Candidate-producing calls must persist the
  complete submission document, including both logical witnesses, before
  returning success.
- **Stage by default.** Unattended calls may write only to ignored local staging
  output such as `research/candidates/`; they must not modify `codes/`.
- **Upper bounds stay upper bounds.** MCP responses must preserve confidence and
  validator fields instead of converting surrogate results into exact distances.
- **Reproducibility is part of the result.** Every search response records family,
  parameters, seed, budget, backend, software version where available, and output
  artifact paths.
- **Bounded computation is mandatory.** Every expensive tool accepts explicit
  time, trial, candidate-count, and memory limits where applicable.
- **No arbitrary execution.** Do not expose `run_shell`, `run_python`, or an
  equivalent escape hatch through MCP.

## Proposed MCP surface

### Read-only resources

Expose repository knowledge as resources or read-only tools:

- `TRACKS.md`, `research/AUTORESEARCH.md`, and contribution requirements;
- schema and verifier-facing submission requirements;
- current code metadata and computed board cells;
- Pareto frontiers by locality and weight class;
- recent codes, notes, and fieldnotes;
- fieldnotes matching a construction family or topic;
- public candidate and validator metadata, excluding private machine paths.

Suggested operations:

```text
get_tracks()
get_research_workflow()
get_submission_schema()
get_recent_activity(limit)
list_frontier(locality, weight_class)
get_code(identifier)
search_fieldnotes(query)
```

These operations should return structured data with source paths and, where
possible, the relevant commit or generated-board version.

### Controlled research tools

Add typed wrappers around existing repository capabilities:

```text
screen_family(family, parameters, budget, seed, backend, threads)
package_candidate(checks_or_generator_output, provenance, confidence)
validate_candidate(candidate_path)
confirm_distance(candidate_path_or_checks, method, budget)
stage_candidate(candidate_document, label)
```

The exact names may change during implementation. The important constraints are:

- `screen_family` returns screening records and audit data, not board claims;
- `package_candidate` uses `research/kit/submit.py` so witnesses are embedded;
- `validate_candidate` invokes the trusted validator rather than an MCP copy;
- `confirm_distance` clearly distinguishes exact certification from independent
  upper-bound evidence;
- `stage_candidate` refuses paths outside the permitted staging area;
- failed validation still preserves the candidate and its verdict for research
  accounting rather than silently discarding it.

Where an operation can produce many candidates, use a campaign identifier and
persist a manifest compatible with `research/kit/campaign.py`. The response may
summarize the run, but the full records must remain available as artifacts.

## Implementation sequence

### Phase 1: establish a machine-readable read layer

1. Identify the existing Python functions for board cells, Pareto comparison,
   recent activity, schema loading, and fieldnote discovery.
2. Add an MCP server package outside `verify/`, preferably under a clearly named
   integration directory such as `mcp/`.
3. Implement read-only resources first.
4. Add JSON serialization tests for representative board entries, frontiers,
   fieldnotes, and schema data.
5. Ensure responses never expose private checkout paths or cite ignored staging
   output as durable evidence.

Deliverable: an agent can inspect the current research context without manually
parsing the repository or invoking shell commands.

### Phase 2: add bounded research operations

1. Wrap the existing research-kit APIs instead of copying their algorithms.
2. Define input and output schemas for family selection, budgets, seeds, and
   backend selection.
3. Require an explicit output location for every artifact and reject `codes/`
   writes in unattended mode.
4. Persist complete candidate documents, screening audits, validator verdicts,
   and failure reasons.
5. Add tests covering:
   - malformed matrices;
   - non-CSS candidates;
   - missing witnesses;
   - validator refutation;
   - successful staging;
   - timeout and candidate-count limits;
   - preservation of the original random seed and parameters.
6. Run the existing smoke and verifier tests against MCP-produced artifacts.

Deliverable: an agent can perform the research loop through typed calls while
remaining subject to the same evidence and staging rules as a human or CLI user.

### Phase 3: deliberately out of scope

Publication operations are not part of this integration. Existing MCPs already
handle the surrounding GitHub workflow, so this project should not add tools for
branching, committing, pushing, opening PRs, requesting reviews, or merging.

The server may return a review-ready staged artifact and a concise report for an
external publication MCP to consume, but it must not perform publication itself.

## Trust and resource boundaries

The MCP process should run with a working-directory boundary and no credentials
by default. It should not require GitHub write access. Expensive search and exact
certification calls need process-level timeouts and resource limits; a client
must not be able to request an unbounded campaign accidentally.

The server must never modify `verify/`. If a wrapped command reports a verifier
integrity failure, the operation should stop and return the failure rather than
attempting a fallback check. Likewise, MCP must not decide whether a candidate
advances a board frontier by itself: it should reuse the site's existing cell and
Pareto helpers and return their computed result.

Because candidate matrices can be large, inputs should be accepted by validated
artifact path or a constrained serialized representation, not unrestricted
embedded Python objects. Paths must be checked against the repository and staging
roots before reading or writing.

## Acceptance criteria

The implementation is ready for a pilot when:

- a clean agent session can retrieve tracks, recent activity, and relevant
  fieldnotes through MCP;
- a seeded family screen produces the same key records as the direct research-kit
  call;
- every packaged candidate contains both side witnesses and provenance;
- every validation result is the direct trusted-validator verdict;
- failed candidates remain persisted with their failure evidence;
- no unattended MCP call can write to `codes/` or `verify/`;
- all expensive operations have enforced limits;
- MCP-generated artifacts pass the existing repository test and validation
  commands; and
- the output is sufficient for an external publication MCP to review, without
  the repository MCP performing publication actions.

## Stop conditions

Do not proceed beyond the read-only phase if the server would need to duplicate
verifier or site logic, expose arbitrary code execution, or require GitHub write
credentials. Do not add a tool merely because an existing CLI command can be
wrapped: each operation must reduce agent friction while preserving an artifact
or evidence guarantee.

If direct CLI and MCP results diverge, stop the integration and fix the shared
interface or serialization boundary before adding more tools.

## Decision

Proceed with a small read-only MCP prototype, followed by controlled wrappers for
screening, packaging, validation, and staging. Keep publication automation out of
scope because it is already supplied by existing MCPs. The first useful milestone
is not a full autonomous researcher; it is a reliable context and evidence
interface that makes the repository's existing workflow difficult to misuse.
