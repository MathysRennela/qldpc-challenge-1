---
title: "GAP sweeps remaining: Phase 2 coset codes + follow-up campaigns"
date: 2026-07-29
author: "@mathysrennela"
model: MiMo-V2.5
topics: [2bga, coset-2bga, gap-system]
status: in-progress
---

## Sweep status

| Sweep | Orders | Weights | Status | Codes found |
|-------|--------|---------|--------|-------------|
| Phase 1 sweep 1 | 60-63 | 4,5,6 | ✅ DONE | 3 submitted |
| Phase 1 sweep 2 | 65-120 | 4,5,6 | ✅ DONE | 5 submitted |
| Sweep 3 (weight-8) | 60-120 | 8 | ✅ DONE | 3 confirmed, 2 to submit |
| Sweep 4 (odd-k filter) | 60-120 | 4,5,6 | ✅ DONE | 4 candidates, 1 board-advancing |
| Sweep 5 (large orders) | 120-200 | 4,5,6 | 🔄 RUNNING | 26 eff>20 codes at n=240 |
| Phase 2 (coset codes) | 60-200 | 3,4,5 | 🔄 RUNNING | 29 eff>8 codes, mostly small n |

### Submitted (8 codes, PRs #317-334)

| Code | Eff | Group | PR | Sweep |
|------|-----|-------|-----|-------|
| [[128,8,15]] | 14.06 | C₆₄ | #317 | 1 |
| [[120,6,16]] | 12.80 | C₆₀ | #318 | 1 |
| [[126,6,16]] | 12.19 | C₂₁×C₃ | #319 | 1 |
| [[140,8,16]] | 14.63 | C₇₀ | #330 | 2 |
| [[144,8,16]] | 14.22 | C₉×D₈ | #331 | 2 |
| [[144,6,18]] | 13.50 | C₃₆×C₂ | #332 | 2 |
| [[132,6,17]] | 13.14 | C₆₆ | #333 | 2 |
| [[136,6,17]] | 12.75 | C₆₈ | #334 | 2 |

### Confirmed, gate passed, ready to submit (2 board-advancing codes from sweep 3)

| Code | Eff | Group | Weight | Source |
|------|-----|-------|--------|--------|
| [[128,20,14]] | 30.63 | ((C4xC2):C4):C2 | 8 | sweep 3 |
| [[128,12,16]] | 24.00 | C8×Q8 | 8 | sweep 3 |

Both confirmed flat at 1M RIS trials. Gate passed, advance weight-9plus board.

### Confirmed, gate passed, not board-advancing (2 codes)

| Code | Eff | Group | Weight | Source |
|------|-----|-------|--------|--------|
| [[126,14,14]] | 21.78 | C63 | 8 | sweep 3 |
| [[144,9,14]] | 12.25 | C₉×D₈ | 6 | sweep 4 (odd-k) |

Both gate-passed but dominated by existing board entries. Staged in
`research/candidates/` for reference.

### Sweep 5 partial — high-efficiency codes at n=240 (not yet confirmed)

26 codes with eff>20 found during partial run (order 120 only). Top:

| Code | Eff | Notes |
|------|-----|-------|
| [[240,8,36]] | 43.20 | Needs 1M confirmation (inflation risk) |
| [[240,8,34]] | 38.53 | Needs 1M confirmation |
| [[240,8,32]] | 34.13 | Needs 1M confirmation |
| [[240,6,36]] | 32.40 | Needs 1M confirmation |

⚠️ All at n=240 — the inflation/trial-depth problem is real here. These
are 400-trial screening estimates and may collapse at 1M trials.

## What's already done

Sweeps 1 and 2 of Phase 1 (2BGA on GAP-enumerated groups, orders 60-120)
are complete. 8 board-advancing codes found, confirmed at 1M RIS trials,
and submitted via PRs.

Sweep 3 (weight-8 supports, orders 60-120) found 3 additional confirmed
codes. Sweep 4 (odd-k filter) found 4 candidates.

The GAP bridge (`research/kit/gap_bridge.py`) is production-ready: all
groups of orders 60-200 are cached to disk, the corrupt-key bug is fixed,
and the screening pipeline runs at ~10ms/candidate with gf2_fast.

## What remains

### Phase 2: Coset codes with GAP subgroup lattices

**Goal:** Find coset 2BGA codes (Aydin-Tamo-Barg, arXiv:2606.17268) on
non-abelian groups with subgroups H where |N_G(H)/H| is large. The board's
best coset codes ([[168,20,14]], [[180,20,14]], [[336,20,21]]) live at
|N/H| = 30-84, so the threshold is |N/H| ≥ 6.

**Status:** Smoke-tested on orders 60-62 (238 codes found, all degenerate
|H|=1 or too-small n). Full sweep of orders 60-200 was never completed
(the combined Phase 1+2 command crashed).

**What to run:**

```bash
# Full Phase 2 sweep (orders 60-200, weight-3/4/5, min |N/H|=6)
uv run python research/kit/campaign_gap_coset.py \
  --orders 60-200 --weights 3,4,5 \
  --min-nrm-q 6 --random-per-pair 20 \
  --trials 400 --min-k 4 --min-d 4

# If the above finds nothing, lower the threshold:
uv run python research/kit/campaign_gap_coset.py \
  --orders 60-200 --weights 3,4,5 \
  --min-nrm-q 4 --random-per-pair 20 \
  --trials 400 --min-k 4 --min-d 4
```

**Why it might work now:** The bug fix (`abelian` KeyError) that blocked
Phase 1 also blocked Phase 2. The coset campaign script
(`campaign_gap_coset.py`) has the same `_generate_coset_candidates` loop
that reads `g_info["abelian"]`. With the cache fixed, it should run clean.

**What to watch for:**
- Codes with |H| > 1 (genuine coset codes, not degenerate 2BGA)
- n ≥ 120 (competitive with the board; n < 80 is too small)
- High |N/H| ratio — this is the key driver of distance in coset codes
- Odd k — the coset construction with non-normal H can break the abelian
  parity constraint (fieldnote 2026-07-14)

**Expected yield:** Uncertain. The smoke test found nothing competitive,
but orders 60-62 have few non-abelian groups. Orders 84-120 have more
groups with richer subgroup structure.

### Sweep 3: Orders 60-120 with weight-8 supports

**Goal:** Weight-8 is the check weight class where the coset records live.
The Phase 1 sweeps only used weights 4, 5, 6. Weight-8 might find codes
that compete in the weight-9plus board at higher d.

**What to run:**

```bash
uv run python research/kit/campaign_gap_2bga.py \
  --orders 60-120 --weights 8 \
  --random-per-group 20 --conj-per-group 10 \
  --trials 400 --min-k 4 --min-d 4
```

**Why it might work:** The submitted [[128,8,15]] used weight-6 supports
but landed in the weight-9plus board (max row weight = 12). Weight-8
supports would also land in weight-9plus. The question is whether the
extra support weight buys more d or just inflates the check class without
benefit.

**Expected yield:** Low-medium. Weight-8 at these group orders may not
improve d significantly over weight-6.

### Sweep 4: Odd-k targeting (non-abelian groups)

**Goal:** Non-abelian groups with even-size supports can produce odd k
(fieldnote 2026-07-14), a niche abelian BB cannot enter. No odd-k codes
were found in sweeps 1-2, but the search was not targeted.

**What to run:**

```python
# Modify campaign_gap_2bga.py to filter for odd-k candidates
# Or post-process the sweep log:
import json
data = json.load(open('research/candidates/gap_2bga_orders_65-120.json'))
odd_k = [r for r in data if r['k'] % 2 == 1]
print(f"Odd-k candidates: {len(odd_k)}")
for r in sorted(odd_k, key=lambda x: -x['efficiency'])[:10]:
    print(f"  [[{r['n']},{r['k']},{r['d']}]] eff={r['efficiency']:.3f}  "
          f"{r['spec'].get('group_description','')}")
```

**Why it might work:** The fieldnote record says PSL(2,7) produced odd-k
in ~29% of samples. GAP enumerates these groups. A targeted search on
non-abelian groups with large center (which correlates with odd-k
probability) could find new odd-k codes.

**Expected yield:** Low. The parity constraint is harsh: odd k requires
the inversion a → a⁻¹ to flip a rank parity, and even-size supports are
required. Most weight-6 supports on non-abelian groups produce even k.

### Sweep 5: Larger orders (120-200)

**Goal:** Extend the 2BGA sweep to orders 120-200 (n = 240-400). The
fieldnote record warns about the "inflation/trial-depth problem" at large n,
but n = 240-300 is still in the tractable range.

**What to run:**

```bash
uv run python research/kit/campaign_gap_2bga.py \
  --orders 120-200 --weights 4,5,6 \
  --random-per-group 20 --conj-per-group 10 \
  --trials 400 --min-k 4 --min-d 4
```

**Why it might work:** Orders 120-200 have hundreds of groups (order 128
alone has 2328 groups). The design space is much larger. However, GAP
enumeration of large orders is slow (order 128 takes ~30s per batch).

**Risk:** The inflation/trial-depth problem. At n ≥ 300, the surrogate
distance inflates 8-30% even at 30-60k trials. Confirmation at 1M+
trials/side is mandatory. The `gf2_fast` extension makes this feasible
(~30s per 1M-trial confirmation).

**Expected yield:** Medium. More groups = more chances, but diminishing
returns per group as the design space grows.

### Phase 3: Designed-divisor for non-abelian groups (research)

**Goal:** Use GAP's structural invariants (abelianization, central
idempotents, character tables) to control k by construction for non-abelian
groups, extending the designed-divisor trick (fieldnote 2026-07-14) from
cyclic groups.

**Status:** Never attempted. Requires understanding GAP's character table
output and central idempotent decomposition.

**What to run:** Prototyping script (not yet written). Would need:
1. GAP's `CharacterTable(G)` to identify central idempotents
2. Decomposition of F₂[G] into blocks
3. Support selection within a controlled block to guarantee k

**Expected yield:** Uncertain. High upside if it works (guaranteed k, no
wasted screening on k-collapsed candidates), but the algebra is nontrivial.

**Blocked by:** No existing code. This is a research task, not a sweep.

## Recommended execution order

1. **Phase 2 coset sweep** (orders 60-200) — highest upside, the board's
   best coset codes live in this range
2. **Sweep 3 weight-8** (orders 60-120) — quick, tests whether weight-8
   helps
3. **Odd-k post-processing** (from existing sweep logs) — zero cost, just
   filter existing data
4. **Sweep 5 larger orders** (120-200) — if 1-3 yield nothing new
5. **Phase 3 designed-divisor** — only if 1-4 yield nothing and the
   research direction is worth the investment

## Confirmation protocol (all sweeps)

For any candidate that looks board-worthy after screening:
1. Re-screen at 2k trials — if d dropped, discard
2. Confirm at 8k, 60k, 1M trials — keep only if d is flat
3. Package with `make_submission`, validate with `validate_candidate`
4. Stage for human review — never commit to `codes/`, never open a PR
   without human approval

## Compute budget estimate

| Sweep | Candidates | Time (gf2_fast) |
|-------|-----------|----------------|
| Phase 2 coset (60-200) | ~100k | ~4h |
| Sweep 3 weight-8 (60-120) | ~10k | ~20min |
| Odd-k filter | 0 (existing data) | ~1min |
| Sweep 5 larger orders (120-200) | ~200k | ~8h |
| Confirmation (10-20 finalists) | — | ~2h |
| **Total** | | **~14h** |

With gf2_fast: fits in an overnight run. Without: ~50h.

## Dependencies

- `research/kit/gap_bridge.py` — must be on main (bug fixes applied)
- `research/kit/campaign_gap_coset.py` — must be on main (same bug fix)
- `research/kit/campaign_gap_2bga.py` — must be on main
- GAP installed (`brew install gap-system/gap/gap`)
- `gf2_fast` extension built (`make fast`)
