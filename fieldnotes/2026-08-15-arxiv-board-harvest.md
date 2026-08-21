---
title: "ArXiv literature harvest for board-eligible qLDPC codes"
date: 2026-08-15
author: "@mathysrennela"
model: "GPT-5.6 Luna"
topics: [literature-mining, arxiv, provenance, validation, research-plan]
status: pilot-complete
related:
  - 2026-08-15-dead-ends-and-leads.md
  - 2026-07-01-confirmation-is-the-bottleneck.md
  - ../research/literature/README.md
  - 2026-08-16-arxiv-code-inspection-queue.md
---

## Plan

Search the arXiv systematically for published or preprint qLDPC constructions
that may contain a code not yet represented on the board. The goal is not to
copy headline parameters into `codes/`: it is to recover a reproducible
construction, reconstruct its checks, and determine whether the repository's
trusted validator accepts it.

The first pass will cover generalized and multivariate bicycles, hypergraph
products, lifted-product and balanced-product codes, quasi-cyclic CSS codes,
abelian Cayley constructions, and geometrically local families. Search terms
will combine the construction name with `quantum LDPC`, `CSS`, `distance`,
`stabilizer`, `table`, and `supplementary data`. For each promising paper, record
its arXiv identifier and version, theorem or table row, construction parameters,
claimed `(n,k,d)`, check-weight bounds, and the exact source of the matrices or
polynomials.

## Evidence status

The metadata-only pilot completed one resumable harvest run on 2026-08-16,
recording 10 normalized paper-version records in
`research/literature/records.jsonl`. The exact query, cursor, and run manifest
are tracked under `research/literature/`; the harvester did not download PDFs,
source archives, or supplementary files.

The pilot produced two reconstruction tranches. The explicit-row queue for
arXiv:2608.09115v1 and arXiv:2608.08996v1 is recorded in
`fieldnotes/2026-08-16-arxiv-code-inspection-queue.md`. Several rows passed the
trusted validator and advanced a board cell, but none has been promoted to
`codes/` or submitted for review. A literature record remains a lead until the
construction is rebuilt and `verify/validate_candidate.py` returns `passed:
true`; a distance inferred from a paper, a random search, or a low-weight
witness remains an upper bound unless an exact certificate supports it.

The pilot is complete for its initial metadata tranche. New papers should be
added through the resumable harvester, while further model or compute budget
should target pinned reconstruction artifacts rather than broad metadata
triage.

## Harvest protocol

1. Search by construction family and inspect papers, revisions, appendices, and
   linked public data. Prefer sources that expose support sets, polynomials,
   generator matrices, or an unambiguous finite-group recipe rather than only a
   plotted or quoted distance.
2. Deduplicate papers and parameter rows against the current `codes/` entries.
   Normalize every row to the repository convention for `n`, `k`, check weight,
   and distance before spending confirmation compute.
3. Reconstruct the CSS checks from the paper's stated convention. Keep the
   arXiv ID, version, section/table/equation, and any public data repository
   commit alongside the reconstruction so another searcher can audit it.
4. Apply the schema and cheap rank/locality checks first. Send only plausible
   improvements through the normal submission builder, preserving the complete
   witness through the repository's required staging workflow.
5. Run `verify/validate_candidate.py` on each staged submission. Report the
   paper's distance separately from the repository's observed witness and any
   exact certificate; do not rename a candidate or write a board claim from an
   unsupported distance.
6. For every gate-fresh improvement, write a submission note containing the
   source pin and reconstruction recipe. If the source cannot be reconstructed,
   retain it as a literature lead with the missing artifact stated explicitly.

## Token budget

Use a staged language-model budget rather than spending equally on every paper.
The initial pilot is capped at approximately **500,000 tokens**: about 100,000
for discovery and classification, 250,000 for triaging 20--30 promising papers,
and 150,000 reserved for reconstruction, deduplication, and provenance checks.

If the pilot yields reproducible leads, budget approximately **1--2.25 million
tokens** for a complete campaign: 50,000--150,000 for broad discovery,
300,000--800,000 for relevant sections from 30--60 papers, 300,000--1 million
for 10--20 reconstruction reviews, and 100,000--300,000 for provenance and
submission notes. Restricting the search to papers with explicit matrices,
polynomial supports, or public code should keep the campaign near the lower end.
The token budget is not expected to dominate runtime; matrix reconstruction,
validation, and distance confirmation are the likely compute bottlenecks.

## Incremental reproducibility

The harvest must be resumable rather than a one-off list. Maintain a tracked
query manifest with the exact search strings, category filters, sort order, and
page size. Maintain a separate cursor for each query. A cursor records the last
successful `(submitted_at, canonical_arXiv_id)` pair, the newest pair seen, the
query definition hash, the overlap window, and the timestamp of the successful
run.

Use `(submitted_at, canonical_arXiv_id)` as the ordering key; an arXiv ID alone
is not a sufficient checkpoint because different queries have different result
streams, timestamps can tie, pagination can shift, and a paper can receive a
later revision. Each run should query from an overlap window, initially seven
days before the previous timestamp, then discard already recorded keys. Keep
revisions as separate versions of the same canonical paper record and re-triage
them when metadata, tables, or supplementary artifacts change.

Store paper metadata and triage decisions in append-only records. Each completed
run should also write a manifest containing its timestamp, code/query revision,
exact queries, previous and new cursors, result counts, new-paper and revision
counts, hashes where available, and API errors. Advance a cursor only after the
corresponding page and manifest have been persisted; an interrupted run must
restart from the previous committed cursor without losing records.

The first run establishes the baseline newest result. Later runs start at the
stored cursor, recheck the overlap, deduplicate by canonical ID and version, and
advance to the newest result. Discovery and metadata normalization should be
deterministic and scriptable; model tokens should be spent primarily on new or
revised papers that survive automated filtering. This both lowers the token
budget and makes the literature frontier auditable by another searcher.

## Triage and stop conditions

Prioritize rows that are both plausibly absent from the board and cheap to
reconstruct: small or structured supports, public matrices, and check weights
within the schema cap. Reject or defer records with unclear qubit-count
conventions, non-CSS stabilizers, unavailable matrices, or a check weight above
the repository limit unless the paper gives a faithful reduction.

The first campaign should stop after every selected family has had its table
rows and stated parameter range checked, all obvious duplicates have been
removed, and each remaining lead has either a pinned reconstruction artifact or
an explicit reason it is not reproducible. It is successful only if it produces
at least one validator-passing, provenance-complete candidate that improves a
board track, or a durable list of ruled-out literature leads and the exact
missing evidence needed to reopen them.

## Reproduction

The search log should include the date, exact arXiv queries, paper IDs and
versions, examined table/section locations, deduplication decisions, and
reconstruction scripts or parameters. Candidate files belong in the repository's ignored staging area; durable
evidence belongs in a submission note or a committed research script, not in an
uncitable local checkout.
