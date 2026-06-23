# Getting started: constructing a code

This directory is a **starter kit for building qLDPC codes** to submit to the
leaderboard. The rest of the repo (`verify/`, `schema/`, `codes/`, `site/`)
*checks and ranks* codes; this is the missing front half — actually
*constructing* one, *estimating its distance*, and *packaging* a valid
submission. It is written so that a newcomer (or an LLM doing the work) can go
from nothing to a verifiable PR in one sitting.

Everything here is **pure numpy** (no extra dependencies beyond what the
verifier already needs) and sits directly on top of the verifier's own GF(2)
core, so what you read here is exactly what the board will record.

## The loop

```
  pick a family ──▶ build (HX, HZ) ──▶ estimate distance ──▶ package ──▶ verify ──▶ PR
     bb.py            construct()        surrogate.py        submit.py    verify/    codes/
   group_algebra.py                   (witness comes free)
   coset.py
```

Run the worked example first — it does the whole loop and runs the real
verifier in-process at the end:

```
uv run python research/recipes/01_build_and_submit_bb.py
```

## 1. Pick a family and build `(HX, HZ)`

Every constructor returns two parity-check matrices `HX, HZ` (numpy int arrays,
shape `(num_checks, n)`) for a CSS code. Pick by the track you're aiming at
(see `../TRACKS.md`):

| Module | Family | Good for tracks | CSS holds because |
|---|---|---|---|
| `bb.py` | bivariate bicycle on a torus Z_l × Z_m (the "gross code" family) | `bivariate bicycle (periodic)`, `weight-6` | abelian circulants commute |
| `group_algebra.py` | two-block group-algebra (2BGA) on **any** finite group | `weight-6`, `generalized bicycle` | left/right multiplication commute |
| `coset.py` | coset 2BGA on G/H (record efficiencies; non-normal H) | `weight-8` | left action commutes with right action by the normalizer |

`bb.py` is the place to start — it's the simplest and any choice of monomials is
a valid code. `group_algebra.py` generalizes it to non-abelian groups (which can
reach odd `k`); `coset.py` generalizes further to the highest known efficiencies.

```python
from bb import build_bb, KNOWN
HX, HZ = build_bb(l=6, m=6, A_terms=[(3,0),(0,1),(0,2)], B_terms=[(0,3),(1,0),(2,0)])
```

Check the basic parameters with `css.py`:

```python
from css import compute_k, verify_css
assert verify_css(HX, HZ)          # H_X H_Z^T = 0 over GF(2)
k = compute_k(HX, HZ)              # = n - rank(HX) - rank(HZ), exactly what the verifier recomputes
```

To make a **new** code, change the monomials / group / supports. A code is only
*interesting* if it advances a track's Pareto frontier over (n, k, d) — see
`../CONTRIBUTING.md`.

## 2. Estimate the distance (and get a witness for free)

Distance is the hard part: computing it exactly is NP-hard, so the board uses a
**trustless witness** instead — you attach an explicit low-weight logical
operator and the verifier confirms it, certifying `d <= value`. `surrogate.py`
finds that witness for you:

```python
from surrogate import distance_rand, lightest_logical
d = distance_rand(HX, HZ, trials=600)        # an UPPER BOUND on min(dX, dZ)
wx, x_witness = lightest_logical(HX, HZ)     # lightest X-logical: (weight, support)
wz, z_witness = lightest_logical(HZ, HX)     # lightest Z-logical
```

**Read this carefully — it's the one place honesty matters most:**

- `distance_rand` returns an **upper bound**. It found *a* logical of that
  weight, so `d <= value`; it is Monte Carlo, **not a proof**.
- To gain confidence, **raise `trials` until the value stops dropping** (e.g.
  `distance_rand(.., trials=t) == distance_rand(.., trials=2*t)`). Then treat it
  as a solid upper bound.
- The matching submission confidence is therefore `"upper_bound"`. An `"exact"`
  claim is a *separate, server-certified tier* (`../verify/certify.py`) — don't
  mark `exact` unless you mean to earn it.
- `mixed_volume(S_f, S_g)` gives a fast, matrix-free **upper bound on k** for
  bivariate constructions — use it to screen candidate exponent sets before you
  ever build a matrix.

## 3. Package a submission

`submit.py` turns `(HX, HZ)` plus a little provenance into a schema-valid
submission. It recomputes n/k, asserts CSS, extracts the witnesses, and
**pre-checks each witness against the verifier's own criteria**, so the document
it returns is built to pass:

```python
from submit import make_submission, save_submission
doc = make_submission(
    HX, HZ,
    name="[[72,12,6]] my BB code",
    construction="Bivariate bicycle on Z_6 x Z_6, A = x^3+y+y^2, B = y^3+x+x^2.",
    authors=["your-handle"],
    tracks=["bivariate bicycle (periodic)", "weight-6"],
    references=["arXiv:2308.07915"],
    confidence="upper_bound",
)
save_submission(doc, "codes/my-72-12-6.json")
```

For the `2d-local-*` tracks, also pass `coordinates=[[x,y], ...]` (one per qubit)
and `layers=`; `submit.py` fills the `locality` block and computes the true
interaction radius for you.

## 4. Verify, then open a PR

```
uv run python verify/qldpc_verify.py codes/my-72-12-6.json
```

Exit 0 with an `earned_distance` block means it will pass CI. Then open a PR
adding your file under `codes/` (see `../CONTRIBUTING.md`).

## Module reference

| File | What it gives you |
|---|---|
| `css.py` | `compute_k`, `verify_css`, and the re-exported GF(2) core (`rref`, `rank`, `kernel_basis`, `logical_basis`, ...) shared with the verifier |
| `bb.py` | `build_bb`, `poly_matrix`, `KNOWN` (known BB codes to start from) |
| `group_algebra.py` | `build_2bga` + group builders: `perm_group`, `cyclic_product`, `dihedral`, `metacyclic`, `sym`, `alt` |
| `coset.py` | `build_coset` + `subgroup_closure`, `left_cosets`, `normalizer` |
| `surrogate.py` | `distance_rand`, `lightest_logical` (witnesses), `mixed_volume` (k upper bound) |
| `submit.py` | `make_submission`, `save_submission`, `validate` |
| `recipes/` | runnable end-to-end examples |

Each module is runnable on its own (`uv run python research/<module>.py`) and
prints a small self-test / demo.

## What's here, and what's coming

This is **Phase 1**: constructors, a fast distance/k surrogate, and submission
packaging — enough to build a code and submit it today, with no dependencies
beyond numpy. Deliberately **not** here yet (planned follow-ons):

- **Exact distance** backends (SAT / ILP) to certify `d =` rather than `d <=`.
- **Decoder-based** distance evidence (BP+OSD residual witnesses) — needs `ldpc`.
- A generic **search loop** (the screen → rank → confirm funnel) for sweeping a
  family for record-beaters, and the **planar / open-boundary** engine for the
  `2d-local-bilayer` track.

These add heavier dependencies and will live behind an optional extra so this
core stays numpy-only.
