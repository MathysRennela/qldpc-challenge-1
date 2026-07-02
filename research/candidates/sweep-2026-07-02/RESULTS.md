# Autoresearch sweep 2026-07-02 — staged candidates

18 candidates, every one `validate_candidate: passed=true` and board-advancing in its
cell. **All distances are upper bounds** (witnessed; claimed value = lightest logical
found by deep self-refutation, 2 seeds x 30k RIS trials per side on the trusted
engine, plus the packager's 8k pass). **Literature novelty is unverified for all.**

## Ranked by efficiency kd²/n

| Code | eff | cell | family | origin |
|---|---|---|---|---|
| [[400,8,50]]  | 50.00 | weight-9plus | 2bga-metacyclic (support-5) | phase C sweep |
| [[336,12,36]] | 46.29 | weight-9plus | 2bga-metacyclic (support-5) | phase C sweep |
| [[324,8,40]]  | 39.51 | weight-9plus | 2bga-metacyclic (support-5) | phase C sweep |
| [[300,8,32]]  | 27.31 | weight-9plus | 2bga-metacyclic (support-5) | phase C sweep |
| [[240,12,20]] | 20.00 | weight-9plus | 2bga-metacyclic (support-5) | phase C sweep |
| [[310,8,26]]  | 17.45 | weight-9plus | 2bga-metacyclic (support-5) | phase C sweep |
| [[320,6,28]]  | 14.70 | weight-8     | 2bga-metacyclic | phase A re-mine (the parked Antigravity code, now honest) |
| [[228,8,20]]  | 14.04 | weight-9plus | 2bga-metacyclic (support-5) | phase C sweep |
| [[240,8,20]]  | 13.33 | weight-9plus | 2bga-metacyclic (support-5) | phase C sweep |
| [[272,8,20]]  | 11.76 | weight-9plus | 2bga-metacyclic (support-5) | phase C sweep |
| [[224,8,18]]  | 11.57 | weight-8     | 2bga-metacyclic | phase A re-mine |
| [[248,6,20]]  |  9.68 | weight-8     | 2bga-dihedral   | phase A re-mine |
| [[180,6,16]]  |  8.53 | weight-8     | 2bga-metacyclic | phase A re-mine |
| [[300,6,20]]  |  8.00 | weight-8     | 2bga-metacyclic | phase A re-mine |
| [[192,6,16]]  |  8.00 | weight-8     | 2bga-dihedral   | phase A re-mine |
| [[272,8,16]]  |  7.53 | weight-8     | 2bga-metacyclic | phase A re-mine |
| [[210,8,14]]  |  7.47 | weight-6     | bivariate-bicycle | phase B gap sweep |
| [[240,8,14]]  |  6.53 | weight-6     | bivariate-bicycle | phase B gap sweep |

## Honest caveats (read before promoting anything)

- **Convergence risk scales with n.** The weight-10 codes at n >= 300 ([[400,8,50]],
  [[336,12,36]], [[324,8,40]], [[300,8,32]]) survived 60k trials/side but RIS is far
  from converged there — these are the same conditions that inflated the refuted
  Antigravity claims. Expect them to deflate under longer search; run
  `decoder_distance` (BP+OSD) and/or more RIS before merging any of them.
- Best-settled claims: the phase A weight-8 codes at n <= 250 and the two BB codes —
  smaller n, estimates stable across every escalation stage (2k -> 20k -> 30k x 2).
- The weight-9plus cell had one incumbent ([[126,28,8]]), so "advances the board" is
  a low bar there; the weight-8 finds compete against [[180,20,14]]/[[294,8,19]] and
  mean more.
- Duplicates already handled: the re-found [[294,8,20]] (== board 294-8-19) was
  rejected by the gate's fingerprint dedup; one WL-equivalent BB spec was dropped.

## Reproduce

- `scripts/phaseA_mine.py` — re-mine of research/board_advanced.json (78 specs -> 8)
- `scripts/phaseB_bb.py` — BB sweep n in (150,286) + support-5 2BGA sweep (phase C)
- `scripts/finalize.py` — deep witness search + packaging + gate + staging
- Each `<slug>.verdict.json` is the gate's full verdict for `<slug>.json`.
