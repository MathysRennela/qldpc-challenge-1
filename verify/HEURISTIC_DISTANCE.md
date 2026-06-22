# Heuristic distance verification — design

Status: **plan / RFC**. Branch: `heuristic-distance-verify`.

## 1. Why

Today a code's distance reaches the board in two ways:

| tier | mechanism | where |
|---|---|---|
| `d<=` (upper bound) | submitter's witness, re-checked | cheap CI, `verify/qldpc_verify.py` |
| `d=` (exact) | server proves no lighter logical (MILP) | server, `verify/certify.py` → `certs/<slug>.json` |

There is a real gap between them:

1. **Exact is often intractable.** The min-weight-logical IP is loose for dense,
   high-rate, geometrically non-local codes. Concretely, the weight-8 coset codes
   `[[180,20,<=14]]` / `[[180,18,<=14]]` defeat the cutoff IP (the per-generator
   lower bound stalls well below the target). These can never reach `d=`, yet a
   single witness (`d<=14`) is weak evidence that 14 is actually the distance.
2. **The witness does not guard against over-claims.** A weight-`v` witness proves
   `d <= v`; it says nothing about whether the *true* distance is `v` or much
   lower. A submission claiming `d=14` whose true distance is 12 passes the cheap
   verifier unchanged and is over-ranked.

**Heuristic distance verification** is an independent, reproducible *search* for a
low-weight logical, run server-side. It does two things the current pipeline
cannot:

- **Refute** an over-claim: if the search finds a logical lighter than the claimed
  `value`, the claim is wrong — the true distance is `<= found < value`. Decisive.
- **Corroborate** a claim: if a large, fixed-budget search finds nothing lighter,
  it raises confidence beyond a single witness, without claiming a proof.

It sits strictly between the witness upper bound and exact certification.

## 2. What it is (and is not)

- It is an **upper-bound search**: every method here can only exhibit a logical of
  some weight, i.e. tighten `d <= w`. It never proves a lower bound.
- A "corroborated" verdict is therefore **not** a proof that `d = value`; it is
  "an independent search of budget B found nothing lighter than `value`". Exact
  certification (`certify.py`) remains the only path to `d=`.
- It is **computed, reproducible (fixed seed + budget), never submitter-claimed**,
  so it cannot be gamed. The cheap *refutation* half runs in CI as a gate; the
  expensive *corroboration* half runs offline like `certify.py` (Section 10).

## 3. Methods

**Reuse, do not reimplement.** Both search engines already exist, validated, in
the companion research repo (`autoresearch/lean_sandbox/Sierpinski/`). This work
is a **port + thin adapter**, not new search code. The only genuinely new code is
the adapter (submission `checks` -> `H_X,H_Z` -> call engine -> compare to the
claimed `value` -> verdict -> result JSON) and the board integration (Section 5).

Two independent upper-bound searches; agreement strengthens a corroboration.

1. **Random information set (QDistRnd-style)** — *primary, Phase 1.* Random column
   permutation -> GF(2) RREF of the logical-coset generators -> lightest nontrivial
   reduced row (and short combinations). Deterministic given `(seed, trials)`.
   - Pure-Python source (canonical, no build): `fitness.min_logical_weight_rand`.
   - C++ accelerated drop-in (~1.3e5 trials/s, std::thread): `cpp/gf2_fast.cpp`
     `distance_rand` / `distance_rand_parallel`.
   Canonical path stays pure-Python to respect the repo's scripts-only default;
   the C++ is an optional accelerator built like the existing ext (setup.py).
2. **Syndrome decoder (BP+OSD residual)** — *secondary cross-check, Phase 2.*
   Source: `syndrome_distance.py` (already multiprocessed, fork start-method).
   Residual `e ^ correction` is a logical when it leaves the opposite checks'
   rowspace; its weight is an upper bound. Needs `ldpc`, so it lands in `decode/`
   next to `eval.py` and runs `uv run --with ldpc`, **out of cheap CI** — same
   policy as the LER evaluator.

Both probe `d_X` (X-logicals in `ker H_Z` outside `rowsp H_X`) and `d_Z`
symmetrically; the code distance is `min`. Porting = lift these files in, swap
their ad-hoc `.npz` loading for the challenge's `checks`->matrix builder (reuse
`verify/gf2.py` / the loader in `qldpc_verify.py`), and keep their logic intact.

## 4. Interface (mirrors `certify.py`)

```python
# verify/heuristic_distance.py
def estimate(doc, trials=200_000, seed=0, methods=("ris",)) -> dict:
    # returns, per side: claimed value, lightest logical found, the witness for it,
    # trials spent, method; plus an overall verdict.
```

Result shape (stored like a cert):

```jsonc
{
  "name": "...",
  "sides": {
    "X": { "value": 14, "lightest_found": 14, "witness": [...], "trials": 200000, "method": "ris" },
    "Z": { "value": 14, "lightest_found": 14, "witness": [...], "trials": 200000, "method": "ris" }
  },
  "verdict": "corroborated",      // corroborated | refuted | inconclusive
  "d_heuristic": 14,              // min lightest_found over sides
  "seed": 0, "methods": ["ris"]
}
```

- `refuted` iff `lightest_found < value` on any side (and we keep the lighter
  witness as proof of the tighter bound).
- `corroborated` iff `lightest_found == value` on both sides and `trials >=` a
  per-`n` threshold.
- `inconclusive` if the budget is too small to trust a null result.

CLI: `python verify/heuristic_distance.py codes/foo.json [--trials N] [--seed S]`,
exit non-zero on `refuted` (so it can gate, if desired).

## 5. Storage and board surfacing

- Write results to `certs/heuristic/<slug>.json` (parallel to `certs/<slug>.json`),
  so the existing exact certs are untouched.
- `site/build.py` gains a third tier between `ub` and `exact`:

  | board label | condition |
  |---|---|
  | `d=` (exact) | `certs/<slug>.json` has `d_exact` |
  | `d≈` / `d<=` (corroborated) | `certs/heuristic/<slug>.json` verdict `corroborated` |
  | `d<=` (upper bound) | witness only |
  | flagged / downgraded | heuristic `refuted` → show the lighter `d` |

  Exact always outranks corroborated, which outranks witness-only. A `refuted`
  result lowers the code's distance to the found value (and flags the original
  claim in the detail page).

## 6. Reproducibility / anti-gaming

The server runs the search from the code alone with a pinned `(seed, trials,
method)` recorded in the result; anyone can re-run and reproduce. Like
`certify.py`, the verification is computed, never trusted from the submission.

## 7. Phasing

- **Phase 1 — RIS refutation + corroboration (port).**
  Lift `min_logical_weight_rand` (and helpers) from the research repo into
  `verify/heuristic_distance.py`; write only the thin adapter (`checks`->matrices
  via `verify/gf2.py`, verdict, result JSON) + CLI. No new deps. Optional: vendor
  `cpp/gf2_fast.cpp` + `setup.py` as the accelerated drop-in.
  *Done when:* it corroborates the 27 exact-certified codes (finds nothing lighter
  than each certified `d`) and refutes a planted over-claim test.
- **Phase 2 — syndrome-decoder cross-check (port).**
  Lift `syndrome_distance.py` into `decode/distance.py` (BP+OSD residual), offline
  with `ldpc`; reuse its multiprocessing as-is; agreement recorded in the result.
- **Phase 3 — board integration.**
  `certs/heuristic/` storage, the third tier in `site/build.py`, a badge.
- **Phase 4 (optional) — effective distance for the decoding track.**
  Sub-threshold LER slope / fixed-weight onset (from `docs/distance_via_simulation`)
  feeding the planned `decoding` track, distinct from the code-distance estimate.

## 8. Validation

- **Corroboration sanity:** run Phase 1 over all `certs/*.json`; it must never find
  a logical lighter than the certified exact distance (a hit would be a bug or a
  bad cert).
- **Refutation sanity:** construct a code whose claimed `value` exceeds a planted
  low-weight logical; the search must find it and return `refuted`.
- **Target cases:** `[[180,20,<=14]]`, `[[180,18,<=14]]` should corroborate
  (no logical `<14` found over budget), upgrading them from witness-only to
  `corroborated` — the intended outcome for codes exact IP cannot reach.

## 9. Open questions

- Per-`n` trial-budget thresholds for a trustworthy `corroborated` null (calibrate
  against the exact certs, where we know the true distance).
- Optional accelerated RIS (the C++ threaded `distance_rand` exists in the
  author's tooling at ~1.3e5 trials/s); keep the canonical path pure-Python and
  treat acceleration as an optional drop-in.

Resolved: the *refutation* half runs in CI (Section 10); the *corroboration* half
stays offline/server-side, as originally planned.

## 10. Refutation as a CI gate (implemented)

The two halves split by cost, and only the cheap half gates PRs:

| | where | budget | on a hit |
|---|---|---|---|
| **refutation** | CI, inside `qldpc_verify.verify()` | small, fixed seed, n-scaled trials under a wall-clock cap | the PR **fails** with the lighter witness |
| corroboration | offline (`heuristic_certify.py`) | large + syndrome-decoder cross-check | writes the `corroborated` cert |

`heuristic_distance.refute_check(doc)` runs a bounded, time-capped RIS
(`trials = min(8000, 2500 + 40 n)`, ~10 s wall-clock) and `qldpc_verify` records a
`distance_not_refuted` check: if a logical lighter than the claimed distance is
found, the check fails and so does CI. Properties:

- **Sound, never a false failure.** Every refutation is a checkable lighter logical
  (in the right kernel, outside the stabilizers), so a genuine over-claim; the
  submitter gets the explicit operator. CI never wrongly rejects a valid code.
- **Not complete.** A randomized bounded search can miss a lighter logical, so a
  clean pass means "no over-claim found at this budget", not a certified distance.
  A passing code still posts as `d<=` until the offline corroboration upgrades it.
- **Deterministic.** Fixed seed -> reproducible, non-flaky; a maintainer can replay
  any failure exactly.
- **Bounded.** Pure Python (no build in CI); the wall-clock cap holds per-code cost
  to ~10 s regardless of n. Validated: 38/38 existing codes pass, planted
  over-claims are caught.
