---
title: "Monthly board-housekeeping campaign: three contained loops (layouts, cluster search, exact certs) with an expand/leave decision gate"
date: 2026-09-20
author: "@mathysrennela"
model: "GLM 5.3 Flash (Zed coding agent)"
topics: [board-analysis, pareto-frontier, layout-search, exact-certification, targeted-search, housekeeping]
---

# Monthly board-housekeeping campaign

The board grew fast (1450 entries / 1104 distinct codes as of 2026-09-20).
This fieldnote turns the board-state analysis into a **repeatable monthly
campaign**: three contained, parallel autoresearch loops that improve the
Pareto frontiers and the quality of existing entries, followed by an explicit
**decision gate** (expand / leave as-is). It is written so the next run can
execute it without redoing the analysis.

## Board state that motivated this (2026-09-20, committed board)

Measured with the board's own structural pass (`qldpc_verify.board_reports`,
same cell assignment and Pareto rule as `site/build.py`), **filtered to the
git-tracked `codes/` files** — see the caveat below. Analysis scripts:
`research/_board_analysis.py`, `research/_board_analysis2.py`, and
`research/candidates/2026-09-20-housekeeping/board_state.py` (the tracked-board
filter the campaign drivers use).

**Working-tree caveat (operational, cost us a rerun):** the checkout held 346
untracked `codes/*.json` files with suffixed slugs (`"108-16-2 4.json"`, …).
They are NOT board entries — `site/build.py` rejects their slugs, so CI never
sees them — but a naive directory scan counts them and inflates every number
(first pass here reported 1450 entries / 918 records; the committed board is
1104 / 686). Any board analysis must filter to `git ls-files codes/`.

Committed-board numbers:

- Cell populations / records / dominated (headline cells):
  unrestricted × weight-any 1104 / 686 / 418; unrestricted × weight-8
  943 / 576 / 367; local-2d-bilayer × weight-any 364 / 232 / 132;
  local-2d-single × weight-any 205 / 156 / 49; local-2d-single × weight-4
  175 / 132 / 43.
- **601 of 1104 entries have no exact certificate** (503 do); **403 of the 686
  top-cell records are uncertified**.
- **733 entries have no layout** (484 of them are top-cell records) — they
  compete only in `unrestricted` cells, against ~3–5× more codes than the
  local cells.
- **161 codes sit in weight-9plus**, locked out of the weight-8/6/4 boards.
- The frontier is dense in n (records span 7–998, no coverage gap > 30%), so
  gains come from better (k, d, w) at fixed n or from moving codes into
  thinner cells — not from filling empty n ranges.
- Contested cluster: **n=96 carries 11 top-cell records** (`96-22-6` w=8,
  `96-20-6` w=7, `96-20-8` w=8, `96-16-6` w=6, `96-6-6` w=5, `96-4-13` w=7,
  `96-4-10` w=5, `96-34-4` w=6, `96-50-2` w=8, `96-48-2` w=6, `96-2-14` w=8).
  One new code can take several at once. Single-copy records worth beating:
  `837-45-5` w=4 (local-2d-single), `205-6-6` w=4.
- kd²/n headroom in the local cells: best records are 6.4
  (local-2d-single, `20-8-4`), 19.2 (local-2d-bilayer, `360-12-24`), 2.0
  (local-2d-single × weight-4, `16-2-4`).
- Duplicate fingerprints on the committed board: **0 groups**. The 346
  untracked working-tree files duplicate committed matrices, but that is
  working-tree hygiene, not a board problem — and out of scope (below).

## Scope exclusions (do not do these unattended)

- **No deletion or dedup of existing entries.** Removing duplicate
  `codes/*.json` copies changes the public board and is a maintainer decision;
  unattended runs never delete board content.
- No writes to `codes/`, no commits, no PRs (unattended autoresearch rule,
  `research/AUTORESEARCH.md`). Candidates stage in `research/candidates/`.
- The one sanctioned board-visible write is `certs/<slug>.json` written by the
  trusted certifier (`verify/certify.py`) via `cert_campaign.py` — a
  verifier-produced artifact, not a judgment call. Precedent: the 2026-09-19
  cert run.

## The three contained campaigns

Staging root: `research/candidates/2026-09-20-housekeeping/` (gitignored).
Run-log: `RUN-LOG.md` in that directory. Budgets are the containment; the
decision gate decides expansion.

### A. Layout campaign, records-first (contained)

- **Target:** no-layout codes that are *already* unrestricted records, n ≤ 250,
  top 20 by kd²/n (the full target set is 484 no-layout top-cell records). A
  found 2D-local layout promotes the same matrix into cells with ~3–5× fewer
  competitors.
- **Method:** `research/campaigns/layout_campaign.py` machinery
  (`run_layout_search`, base budget from `_config(n)`), driven by
  `layout_records_driver.py` in the staging root (records-first filter; the
  stock `--limit` takes an arbitrary prefix).
- **Budget:** base budget only, 20 codes, no escalation stage in the contained
  run. Near-miss radii are recorded for a possible expanded run.
- **Find → stage:** any layout reaching radius ≤ 4.0 (single) or ≤ 7.0
  (bilayer) is saved with its coordinates for human review. The verifier
  decides whether it is a real 2d-local record.

### B. Targeted cluster search: the n=96 cluster (contained)

- **Target:** one code that takes several n=96 records at once. Any
  [[96, k≥23, d≥6]] with w≤8, or [[96, k≥22, d≥7]] with w≤8, is a record
  (it dominates `96-22-6` w=8 and is not dominated by the w≤7 records below
  it in k). Secondary stretch: [[96, k≥20, d≥7]] with w≤7.
- **Method:** bivariate-bicycle sweep (`kit/search.py` `screen` over
  `sample_bb`-style generators on torus sizes with 2·l·m = 96: (l,m) ∈
  {(6,8),(8,6),(4,12),(12,4),(3,16),(16,3),(2,24),(24,2)}), screen → rank →
  package with `kit/submit.make_submission` → `verify/validate_candidate.py`
  gate. Odd-n targets (`837-45-6`, `205-6-7`) are out of BB/GB reach (n = 2|G|
  is even); they stay open for tile/quadricycle families.
- **Budget:** ≤ 4000 screened samples, screening trials ≤ 500, ≤ 6 packaged
  finalists through the gate.
- **Find → stage:** gate-passed survivors only, saved under
  `cluster96/` with their full validator verdicts.

### C. Exact-certification campaign, revised targeting (contained)

- **Target:** uncertified codes with **d ≤ 10 and n ≤ 200** (any k, any weight,
  records or not — the exact tier is worth having across the board), sorted by
  **increasing n**. Rationale: the 2026-09-20 cost model (Results below) shows
  k is nearly free and d is the binding axis; the earlier ascending-n·d sort
  cherry-picked d ≤ 5 and left ~145 uncertified d ≤ 10 codes on the table.
- **Method: rotation pipeline** (`cert_pipeline.py` in the staging root),
  cheapest mechanism first, one `d_exact` ends the code:
  0. **BP+OSD pre-filter** (`kit/distance.decoder_distance`, <= 20 s): an
  independent mechanism; a logical lighter than the claimed d records
  REFUTED-PREFILTER and skips the solvers (no cert written).
  1. **MILP** (`verify/certify.py`, tlim = 60 s/side): the fast bulk — most
  d <= 10 codes certify here in seconds.
  2. **SAT** (`verify/sat_certify.certify`, tlim = 120 s/side, single-query
  selector encoding, automatic lex-leader symmetry breaking): catches the
  high-k / symmetric codes the MILP chokes on (e.g. [[24,12,2]], which MILP
  never certified and SAT cracked instantly). A SAT result at W = d-1 that
  is SAT (not UNSAT) REFUTES the claimed distance and carries the witness —
  recorded, no cert written, human review.
  Circuit breaker: stop the run after 2 consecutive codes exhaust all
  stages. Cert files are written only by the certifier paths (stage 1 via
  `certify_one`; stage 2 writes the same JSON shape on `d_exact`), so
  `site cert_consistent()` honors them.
- **2026-09-20 parser fix (prerequisite):** `cert_campaign.certify_one`
  crashed with "bad JSON output" on codes where HiGHS emits a stray C++ log
  line after the JSON document (first seen as the [[24,12,2]] failure).
  Fixed research-side by extracting the braces-delimited document before
  parsing; `verify/` untouched. Until that fix, the MILP stage silently
  degraded to SAT on every such code.
- **Find → keep:** `d_exact: true` results are written to `certs/` by the
  certifier itself; everything else (timeouts, UB) is recorded in the staging
  dir only.

## Decision gate (run after all three campaigns finish)

Expand **only** the campaigns that clear their bar; if none clear, leave the
campaign design as-is and record the negative result here.

- **A expands** if ≥ 1 valid 2D-local layout was found on a record (staged
  coordinates reaching a 2D-local radius). Expansion = doubled budget on the
  near-miss list (gap_to_bilayer ≤ 3), then the full no-layout board.
- **B expands** if ≥ 1 gate-passed candidate advances the n=96 cluster.
  Expansion = more torus sizes / generalized-bicycle (dihedral, metacyclic)
  samplers at the same n, then the 390-82 cluster.
- **C expands** if ≥ 5 new exact certificates landed on records. Expansion =
  raise the count and add the SAT escalation path for MILP timeouts.
- **Global stop:** if all three yield zero at contained budget, do not expand
  any of them; write the negative result into this fieldnote and revisit only
  with a new mechanism (not more of the same compute).

## Results

(Newest run on top.)

### 2026-09-20 run

- **A (layouts):** cast canceled by the user; driver ready and unrun
  (resumable). Pending human decision.
- **B (n=96 cluster):** NEGATIVE, gate = do not expand. 4000 BB samples over
  all 8 torus sizes with 2lm=96; zero met the record conditions. Structural
  cause (`cluster96/DECISION-JOURNAL.md`): BB k is always even, so k=23/21 is
  unreachable in-family; every high-k BB found shares a low-rank common
  factor giving weight-4 orbit-sum logicals (d<=2); the board's BB [[96,20,8]]
  comes from a cover construction uniform sampling does not reach; 10/11
  cluster records are GB codes. Next mechanism (queued): GB
  dihedral/metacyclic samplers at n=96, or structured cover/lifts — not more
  uniform BB sampling.
- **C (exact certs):** tranche 1: 24/25 records certified d= at tlim=60
  (bar >=5 cleared; the one failure, `24-12-2`, is a genuine per-code hard
  case, see cost model below). Expansion tranche was interrupted by the user
  in favor of a cost-model study.

### Certification cost model (2026-09-20, tlim=120 s/side, scipy/HiGHS MILP)

Motivated by the observation that cost-sorted certification (ascending n*d)
only ever certifies d<=5 quickly. Probes: `cert_timing_grid.py`,
`cert_boundary_probe.py` (logs: `cert_timing_grid.json`,
`cert_boundary_probe.json`). Wall-clock times below include both sides (the
certifier runs one MILP per side, each with its own tlim, so wall can
approach 2x tlim).

| d | n~55 | n~110 | n~160 |
|---|---|---|---|
| 6 | 11 s (54-12-6) | 22 s (108-6-6) | 75 s (160-18-6) |
| 7 | 33 s (60-12-7) | 42 s (108-12-7) | 19 s (162-8-7) |
| 8 | 123 s (56-12-8) | 107 s (112-12-8) | 146 s (151-6-8) |
| 9 | 40 s (52-4-9) | — | — |
| 10 | 82 s (52-2-10) | — | — |
| 11 | **timeout** (60-2-11) | — | — |

Findings:

- **k is nearly free.** [[144,36,4]] certified in 0.9 s; [[96,22,6]] in 43 s.
  The k<=1/5/10/20 axis of the monthly question does not bind; do not
  budget by k.
- **d is the binding axis.** At tlim=120 everything probed with d<=10
  certifies, including n=160 at d=6-8 (near the edge: 75-146 s). The wall
  sits at d=11: [[60,2,11]] times out at 150 s wall. The earlier d=9/10
  timeouts were artifacts of tlim=60, not of d.
- **n matters second** (d=6: 11 -> 22 -> 75 s across n=54/108/160), and
  **structure matters more than either**: [[162,8,7]] took 19 s while
  [[108,12,7]] took 42 s. Single samples per cell — the map says a cell is
  *reachable*, not that every code in it is.
- **Small n does not guarantee easy.** [[24,12,2]] never certifies (Z-side
  MILP hits its limit in <1 s wall, reproducibly, both tlim=60 and 120):
  degenerate high-k/low-d codes can be structurally hard for the MILP.
- **Practical rule for the monthly C campaign (revised 2026-09-20):** target
  uncertified codes with **d ≤ 10, any n ≤ 200, sorted by increasing n,
  tlim = 180 s, stop after 2 consecutive timeouts**. The earlier rule
  (ascending n·d, tlim=60) cherry-picked d ≤ 5; the d ≤ 10 pool is ~145 codes
  (55 at n ≤ 100, 19 at n ≤ 150, 29 at n ≤ 200, 42 at n > 200 — the n > 200
  tail is probed only at its cheapest, treat as exploratory). Skip d ≥ 11 and
  expect per-code outliers like [[24,12,2]] that never certify regardless of
  budget.
