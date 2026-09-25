---
title: "UnitaryCON qLDPC Code Sprint (#1155) closing wrap-up: 481 merged PRs, 27 participant frontier records, and the strategies that scored"
date: 2026-09-19
author: "@mathysrennela"
model: "GLM 5.3 Flash (opencode CLI agent, tally + wrap-up)"
topics: [hackathon-1155, sprint-1155, frontier-record, wrap-up, leaderboard, generalized-bicycle, lifted-product, surface-code, qubit-reduction]
---

# UnitaryCON qLDPC Code Sprint (#1155) — closing wrap-up

The sprint ran from Thu 17 Sep 18:00 ET to Sat 19 Sep 18:00 ET (issue #1155,
co-coding session at UnitaryCON Toronto during IEEE Quantum Week). This
fieldnote is the closing tally on the board snapshot at the sprint's close
(HEAD 6c9f51a3, 1097 board entries), the ratified rules used to score it, and
a strategy-by-strategy account of what worked. The scoring-methodology
clarification that these numbers rely on is pinned in the issue thread
(https://github.com/unitaryfoundation/qldpc-challenge/issues/1155, comment of
2026-09-19/20): scoring window = PRs opened between the start and end time and
merged at the snapshot; frontier records computed exactly as the site's
contributor panel does; organizers' submissions stay on the board but score
zero.

## 1. The event in numbers

- **488 PRs opened** in the window, **481 merged** by the snapshot. The 7
  that remained open carry fieldnotes and research harnesses, no codes.
- **437 code files** were added by in-window PRs (the remaining 91 codes
  merged during the window came from PRs opened before the start, which the
  rules exclude). The board grew from 569 to 1097 entries over the three
  days.
- Of the 437: **289 are frontier records** at the snapshot — no other code in
  any (locality class, check-weight class) cell they live in beats them on
  all four of n, k, d, w — **145 were dominated** by other submissions before
  the close, and **3 fall outside the eligibility box** (n ≤ 1000, w ≤ 8,
  d ≤ 40): [[396,10,37]] at w = 12 (`codes/396-10-37.json`),
  [[684,12,66]] and [[684,20,48]] at d > 40 (`codes/684-12-66.json`,
  `codes/684-20-48.json`).
- Of the 289 records, **27 score for participants**; the other 262 belong to
  @MathysRennela and 5 to @vprusso, both organizers and therefore excluded
  per the ratified rules. Organizer codes still dominate on the board —
  which is exactly what the sprint rules intend ("if someone dominates your
  record, it is worth zero"): 131 of the 145 dominated sprint codes were
  dominated only by organizer-owned codes.

One point is one *code*, not one cell: a code that is a record in a nested
cell and the top-level board still scores one. Every author listed on a code
gets the point; no sprint code had two @handle authors, so each of the 27
records is one person's point.

## 2. Final ratified leaderboard

| # | Contributor | Frontier records | w ≤ 6 | w ≤ 8 | 2D-local |
|---|---|---:|---:|---:|---:|
| 1 | @msilve160 | **8** | 8 | 8 | 0 |
| 2–5 | @dorakingx | 3 | 3 | 3 | 3 |
| 2–5 | @natestemen | 3 | 3 | 3 | 0 |
| 2–5 | @pandey-tushar | 3 | 2 | 3 | 0 |
| 2–5 | @victor-onofre | 3 | 3 | 3 | 3 |
| 6–7 | @e-eight | 1 | 0 | 1 | 1 |
| 6–7 | @rexrowan | 1 | 1 | 1 | 0 |

Excluded as organizers (per the rules clarified in the issue): @MathysRennela
(262 records on the board at close) and @vprusso (5 records: [[350,70,9]],
[[390,78,9]], [[540,112,8]], [[624,52,9]], [[675,139,8]], all non-abelian
lifted products, e.g. `codes/675-139-8.json`).

### Prizes

- **Weight ≤ 6:** @msilve160, 8 records — all eight of his records have
  check weight ≤ 6 (w = 5 or 6). Runner-up group at 3: @dorakingx,
  @natestemen, @victor-onofre.
- **Weight ≤ 8:** @msilve160, 8 records. Runner-up group at 3: @dorakingx,
  @natestemen, @pandey-tushar, @victor-onofre.
- **2D-local (single-layer + bilayer cells):** tie, **@dorakingx and
  @victor-onofre, 3 each**. @dorakingx's three reductions all preserve the
  locality class of their sources ([[118,8,7]] and [[203,8,10]] bilayer,
  [[205,6,6]] single-layer); @victor-onofre's three surface-code packings are
  all single-layer at interaction radius ≤ 4.

All distances above are the board's witnessed distances (an explicit logical
witness at weight d, re-searched by CI and the weekly sweeps), not certified
exact values unless the per-code notes say so.

## 3. What the records were, contributor by contributor

**@msilve160 — 8 records, the sweep winner.** Two strategies.

1. *Planar hyperbolic codes, catalog mining.* Five records
   ([[80,18,5]], [[150,32,6]], [[336,58,6]], [[360,38,8]], [[660,68,8]]) are
   literature reproductions pulled from one pinned source —
   github.com/QEC-pages/Quantum_LDPC_Codes @ 1c95489383564e4dc2cce517de00d64d6f2c4f56,
   `Hyperbolic_Codes_Planar.zip` — selecting different {p,q,N} tilings
   ({5,5} at small n, {4,5} mid and large, {4,6} at [[336,58,6]]). These are
   very high-rate codes (k/n between 0.09 and 0.27) at w = 5–6, in
   `unrestricted`/weight-6 and weight-8 cells that were thin at large n.
   Three of the five ([[336,58,6]], [[360,38,8]], [[660,68,8]]) were opened
   in the last 20 minutes of the sprint and merged just past the close —
   ratified as scoring under the closing clarification. Notes:
   `notes/150-32-6.md`, `notes/660-68-8.md`.
2. *Non-abelian lifted products.* [[520,44,8]], [[546,46,8]],
   [[624,54,8]] (PRs #1345, #1346, #1352) — lifted products of 2x3 monomial
   base matrices over metacyclic and non-metacyclic group algebras
   (Z_5 x|_4 Z_8, C_7 x D-type, C_6 x D-type), built with
   `research/kit/nonabelian_lp.py` at check weight 5 and d = 8, k/n ≈ 0.085.
   Notes: `notes/520-44-8.md`.

Model per provenance: Claude Sonnet 5.

**@dorakingx — 3 records, all in the 2D-local prize.** The sprint's cleanest
display of qubit shaving with locality preservation. Each code takes a board
fixpoint and applies one row-space graft: pick a low-weight element S of the
stabilizer row space, replace one generator of the subset summing to S by S
itself, and delete the now-redundant qubit — losing one check's worth of
redundancy while keeping k, the check-weight class, and crucially the
locality class. The payoff of keeping the layout: [[256,6,6]] → [[205,6,6]]
(n − 51, `codes/205-6-6.json`, `notes/205-6-6.md`),
[[162,8,7]] → [[118,8,7]] (n − 44, `codes/118-8-7.json`),
[[242,8,10]] → [[203,8,10]] (n − 39, `codes/203-8-10.json`). Because these
land in single-layer and bilayer cells where the frontier is far emptier than
in `unrestricted`, each reduction was a record in its 2D-local cell as well
as in the weight cells. Model: Claude Opus 5 (Claude Code).

**@victor-onofre — 3 records, tied for the 2D-local prize.** Multi-band
dense packing of distance-5 surface-code patches, generalizing
arXiv:2511.06758: stack the patches in bands with a fixed band pitch and per
band lay m patches side by side at patch pitch P_x. Each of [[837,45,5]],
[[964,52,5]], [[998,54,5]] (`codes/837-45-5.json`, `notes/837-45-5.md`,
`notes/964-52-5.md`, `notes/998-54-5.md`) is a single-layer layout with
interaction radius ≤ 4 — a `local-2d-single`/weight-4 cell almost empty at
large n — and each carries k = 45–54 at d = 5. The work shipped a general
builder (PR #1608) rather than one-off matrices, so the (bands, m, pitch)
knobs are parameterized; three (rows, m) choices produced the three records.
Model: Claude Opus 5.

**@natestemen — 3 records.** Reconstructed 2BGA (two-block group-algebra)
codes from the pinned QEC-pages 2BGA catalogue
(github.com/QEC-pages/2BGA-codes @ 403d194c3f98f0cadc236aecbc4a8b6139ccf23c):
[[78,4,9]] on SmallGroup(39,2), [[132,4,12]] on SmallGroup(66,1),
[[192,4,16]] on SmallGroup(96,4) — all weight-5, k = 4, supports given as
GAP element indices (`codes/78-4-9.json`, `notes/78-4-9.md`,
`notes/132-4-12.md`, `notes/192-4-16.md`). Deliberately targeting the thin
k = 4 cells that the sprint's own targets screen flagged. Model: GPT-6 via
OpenAI Codex.

**@pandey-tushar — 3 records.** The widest family spread of any participant:
a weight-5 coset two-block code over G = D_6 x Z_28 with a deliberately
non-normal subgroup (Aydin–Tamo–Barg; the coset structure is what gives
k = 6 at n = 168, `codes/168-4-14.json`, `notes/168-4-14.md`); a generalized
toric code [[196,2,14]] on the twisted torus Z_7 x Z_14, a member of the
[[4r^2, 2, 2r]] family whose construction proves d = 2r exact
(`codes/196-2-14.json`, `notes/196-2-14.md`); and an Okada–Kasai
pair-partition CPM code [[808,206,20]] (arXiv:2607.14091, (J,L) = (3,8),
prime lift P = 101) — k = 206 at d = 20 is the sprint's highest
(k, d) product on a single code by a participant
(`codes/808-206-20.json`, `notes/808-206-20.md`). Model: Claude Opus 5.

**@rexrowan — 1 record.** [[42,6,6]], a generalized-bicycle code
reconstructed from a qecdb.org record and dropped into a weight-6 cell where
d = 6 at n = 42 had no rival (`codes/42-6-6.json`, `notes/42-6-6.md`).

**@e-eight — 1 record.** A deep RIS re-verification that corrected the
board's [[882,18,30]] to [[882,18,29]] (`codes/882-18-29.json`,
`notes/882-18-29.md`, PR #1165): the lighter witness is itself evidence, and
under the closing clarification the revised board entry scores. Honest
distance bookkeeping is on the board too.

**Organizer contributions (excluded from scoring, on the board).**
@MathysRennela merged 262 records — systematic generalized-bicycle and 2BGA
sweeps over (n, k, d) grids, a quadricycle (rank-4 multivariate bicycle)
constructor (fieldnote `fieldnotes/2026-09-19-quadricycle-rank4.md`), a k = 2
generalized-bicycle ladder reaching [[454,2,21]] (`codes/454-2-21.json`),
and weight-6 through weight-8 2BGA sweep lines documented in
`fieldnotes/2026-09-18-hackathon-1155-frontier-map-and-playbook.md`.
@vprusso added 5 non-abelian lifted-product records and two site features,
including the contributor-panel frontier ranking (PR #1612) that the tally
in section 2 mirrors.

## 4. What the event left on the board

- +528 codes in 48 hours (569 → 1097), roughly half of the entire board,
  with every one passing the same verify gate and independent distance
  search as any submission.
- The 27 participant records cluster exactly where the sprint's
  "where records are cheap" guidance pointed: n-shaves with preserved
  locality (2D-local cells), large-n high-rate topological codes, and thin
  k = 4 weight-5 cells.
- The dominant failure mode was timing, not merit: 145 sprint codes were
  off the frontier at close because someone else improved on them first —
  13 of them to other participants (e.g. @msilve160's [[162,8,7]] and
  [[242,8,10]] to @dorakingx's shaves, [[160,18,6]] to @msilve160's own
  [[80,18,5]]), 131 of them to organizer-owned codes that do not score.

The issue #1155 closes with this PR; the live standings remain on the site's
contributor panel, which ranks every contributor by the same per-cell
frontier count used here.
