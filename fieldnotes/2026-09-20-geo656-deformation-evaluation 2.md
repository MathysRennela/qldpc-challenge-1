---
title: "The g-record [[656,114,3]] survived every deformation move class: site-removal is net -1 k, pin-rescued deletion bundles bottom at -3, and repacking searches land 30 k short"
date: 2026-09-20
author: "@mathysrennela"
model: "GLM 5.3 Flash"
topics: [geometric-efficiency, negative-result, checkerboard, chamfer-family, deformation, packing]
related:
  - fieldnotes/2026-09-08-check-deletion-campaign-retrospective.md
  - research/candidates/CAMPAIGN-GEO-656.md
  - fieldnotes/2026-08-30-chamfer-d4-closed-and-wall.md
  - fieldnotes/2026-08-29-g-parity-agenda.md
---

# Deformation evaluation of the geometric-efficiency record [[656,114,3]]

Task: take the top geometric-efficiency code ([[656,114,3]], g = 1.5640, the
26x26 checkerboard with two right-edge notches, 103 hole faces, 40 weight-2
boundary pins) and evaluate whether any of the recently explored deformation
moves beats it. **Verdict: no. The record survived every move class, including
three it had never faced.** Negative result, with five structural data worth
recording.

## The family's k-arithmetic (new, verified)

Reconstructing the construction from `codes/656-114-3.json`: face checks on
all full faces by parity (even -> X, odd -> Z) minus 103 hole faces, plus 40
weight-2 boundary pins (adjacent edge pairs; diagonal pairs are also legal at
diameter sqrt(2) but unused by the submission). All 542 checks are
independent, so

    k = |S| - #full_faces + #holes - #pins = 51 + 103 - 40 = 114,

and the base constant 51 = W + H - 1 of the full square survives the corner
notches (20 removed sites kill exactly 20 faces). The auditor reproduces the
submitted state exactly (k = 114, zero weight<=2 logicals), which validates
every screen below.

## Move classes evaluated

1. **Check deletion, pin-rescued (new).** The 2026-09-08 retrospective ruled
   out pure deletions (weight-1/2 exposure). The untested question was joint
   bundles: p removals exposing p-1 pinnable pairs gain net +1. Enumerated
   ALL 1035 clean-check pairs (the 20 X + 26 Z checks whose removal leaves
   every qubit same-side degree >= 1 -- counts match the retrospective
   exactly) and 4000 sampled clean triples: **best bundle net = -3** (two
   removals need five pins). The exposure cost is ~2.5 pins per removal.
   Dead, with margin.
2. **Site removal with check-vanishing (new).** The prior campaign's graft
   kept incident checks at reduced weight; under the family's own rule a
   removed site makes its incident faces non-full so their checks vanish --
   an interior site kills 2X+2Z checks for a naive +3 k (g would be 1.608).
   Audited all 656 single-site removals exhaustively: every k-raising
   removal exposes weight<=2 logicals (weight-1 at boundary-adjacent
   neighbours that lose their last check; >= 2 equal-column pairs per side
   for interior sites, some at distance 2*sqrt(2)). Pinning all exposures
   costs >= 4 checks: **net -1 k per site, universally** -- which is exactly
   the graft result, now explained: grafting IS pinning all four exposures.
   Subtraction from the qubit set is closed.
3. **From-scratch repacking (new).** Greedy free-hole packing (exact
   weight<=2 audit per move, random orders, 3 seeds x 2 shapes): k = 81-85
   on the 656-site shape, 81-82 on the full 26x26 square -- **~30 k below
   the submission**. The submitted arrangement is not a greedy fixed point;
   it is a genuinely engineered object.
4. **Continuation of the submitted arrangement:** +0 holes (re-confirms
   CAMPAIGN-GEO-656's deletion-tightness with the exact auditor).
5. **Lattice-guided repacking (new).** The submitted hole map is a
   near-periodic diagonal lattice at density ~1/5.7 per side; the zero-pin
   packing bound (no two holes sharing a diagonal-neighbour face) caps
   density at 1/5 (cross-packing). Tested all 50 phase/sign combinations of
   the mod-5 cross lattice on both sides with pin repair: best clean
   k = 57. The raw lattices reach k ~ 160 before repair but their boundary
   weight-1 exposures are unpinable; the submitted lattice's fit to the
   notch geometry is load-bearing.
6. **Notch reshaping (new).** Mid-edge notches kill L+1 faces for L sites
   (base +1 per notch, unlike the corner notches' +0). Swept ~300 notch
   configurations (1-2 mid-edge notches, lengths 4-10) with the transplanted
   lattice, ring-filtered holes, re-derived pins, greedy top-up: 116 clean
   variants, **best g = 1.5000** (k = 111, n = 666, 104 holes, 46 pins).
   The base gain (+1/+2) is eaten by pin overhead (+5 to +8).
7. **Previously closed classes, not re-litigated:** chamfer -> d >= 4
   (k = 51 wall, 2026-08-30), multi-band pitch (envelope-closed, asymptote
   1.30-1.43 < 1.564), seam fusion (Regime-A convexity: fusion only helps
   with a patch of g > 1.564, none exists), bilayer (needs kd^2/n > 6.26
   r^4 >= 100 at r = 2; out of reach).

## Why the record is hard to beat (structural summary)

Beating g = 1.564 at d = 3, r = sqrt(2), rho = 1 needs k/n > 0.17378. The
arithmetic k = 51 + H - W2 says the only levers are the hole/pin budget, and
every lever is pinned by three walls: (a) same-side hole sets must be
independent (weight-1), (b) zero-pin hole density caps at 1/5 per side
(no two holes sharing a diagonal-neighbour face), (c) boundary/notch rings
generate permanent K >= 1 faces whose second knock costs a pin. The
submission sits at 103 holes + 40 pins = net 63 against a crude ceiling of
~(1/5 of interior faces) - boundary pins of the same order -- i.e. it is
within ~10-15 k of the family's structural ceiling, and every local or
semi-global search lands 30 k BELOW it, not above.

## Remaining lead (open, expensive)

The one unexhausted route is a large-scale joint annealer over (hole set,
pin set, notch geometry) with the exact auditor in the loop -- the search
space where the submission's ~30 k advantage over naive packing lives.
Baselines for calibration: greedy 85, lattice 57, notch variants 111,
submission 114 (all on comparable n). A successful anneal must beat k = 115
at n <= 656 (g >= 1.578) or k/n > 0.17378 elsewhere in the cell.

## Compute and artifacts

Local M-series Mac, ~2.5 h total. Scripts and raw results in
`research/candidates/`: `geo656_pack.py` (builder/auditor),
`geo656_greedy.py` (board engine + bootstrap pins),
`geo656_siteremoval.py` + `geo656_siteremoval_results.json` (656-variant
site-removal audit), `geo656_run.py` + `geo656_run_results.json`
(repacking runs), `geo656_bundles.py` + `geo656_bundles_results.json`
(bundle enumeration), `geo656_notches2.py` + `geo656_notches_results.json`
(notch sweep). No candidates staged: nothing beat the record, so nothing
reached the gate.
