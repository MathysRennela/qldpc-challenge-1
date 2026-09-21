---
title: "Jev triage on layout and certification campaigns: cert triage sound, layout triage miscalibrated (11/12 false skips)"
date: 2026-09-19
author: "@mathysrennela"
model: "DeepSeek V4 Flash 0731 (Zed coding agent)"
topics: [jev, calibration, layout-search, exact-certification, triage]
---

# Jev triage on layout and certification campaigns

Measured how well the `jev` MCP server's bounded triage performs on two
expensive search operations, on the first 30 codes of each campaign. The
verdict: **certification triage is sound and useful; layout triage as designed
is miscalibrated and would have discarded 11 of 12 real 2D-local layouts.**

## Setup

Two campaign drivers in `research/campaigns/` (`layout_campaign.py`,
`cert_campaign.py`) write a compact evidence pack per code; the agent calls
`jev_classify` (triage) then runs the expensive operation only on approved
codes. Evidence is one line per code: n, k, d, w, `on_frontier`, cell
thinness / `cost_signal`.

## Certification campaign (30 codes)

- **Jev triage:** 21 `certify`, 9 `skip`, 23 auto-accepted (high confidence).
- **Result:** 10 of 21 certified exactly at tlim=60 (most in <30s); 11 timed
  out. 10 board codes gained exact `d=` tiers.
- **Skipped (9):** all off-frontier, mostly high-k/low-d (k=24–56, d=2–5),
  dominated codes — exactly the low-value set Jev should drop.
- **Assessment:** sound. The `on_frontier` + `cost_signal` signal discriminates
  well; Jev's skips were low-value codes.

## Layout campaign (30 codes)

- **Jev triage:** 29 `skip`, 1 invalid response, 0 `attempt` (16 auto, 13
  review — all leaning skip).
- **Ground truth (ran all 30):** 12 codes have 2D-local layouts (radius ≤ 7
  bilayer). **Jev skipped 11 of those 12.** False-skip rate 11/12.
- **Root cause:** the evidence signal is wrong. All 30 codes live in crowded
  unrestricted cells (≥542 members), so `thinnest_current_cell_members` and
  `on_frontier` (in the unrestricted cells) do not predict 2d-local record
  status. A code in a crowded unrestricted cell can still be a 2d-local
  bilayer record because the 2d-local cells are thinner (338 members vs 542+).
  Jev correctly flagged its own uncertainty (13/30 review, high `uncertain`
  probs) but the `skip` leanings were wrong.

## What this means

- **Certification triage: keep.** It saves compute on low-value codes and the
  `certify` set is genuinely worth certifying.
- **Layout triage: do not trust the current evidence.** The cheap signal
  (current-cell thinness) is a poor proxy for 2d-local record status. Either
  (a) run a cheap layout search first and use Jev only for *escalation* (the
  near-miss radius is a meaningful signal), or (b) find a better pre-search
  predictor of 2d-local record status. The escalation decision is where Jev
  adds value for layouts, not the pre-search triage.

## Boundary

Measured on the first 30 no-layout codes (n ≤ 114) and first 30 uncertified
codes (n ≤ 114), one Jev call each, `typesafe/jev-1.13`. The layout ground
truth is `fold_layout.search_layout` at base budget; a deeper search might
find more layouts, which would only worsen the false-skip rate.

## Resolution

`research/campaigns/layout_campaign.py` was pivoted to an **escalation-only**
design: it runs a cheap base-budget search on every no-layout code (no
pre-search triage) and uses Jev only to decide whether to spend a doubled
budget on a code whose cheap search came close to a 2D-local radius. The
near-miss radius is the meaningful signal the pre-search triage lacked.