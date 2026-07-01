---
name: autoresearch
description: Search for new qLDPC codes on the challenge board. Use when the user gives a research direction (a track cell to attack, a family to try, or a record to beat) and wants an LLM to construct, search, and surface verified candidate codes. Drives the research/ starter kit and the trusted verify/validate_candidate.py gate.
---

# autoresearch: find new qLDPC codes for a direction

Your job: given a research direction, construct and search qLDPC codes, and surface
**verified, genuinely-new candidates** for human review. You may write and run any code
you like — but you do **not** get to decide whether a code is good. A trusted gate does.

## The one rule that makes this trustworthy

**No code is a "find" until `verify/validate_candidate.py` returns `passed: true` for it.**

- Never write your own distance check, "good enough" heuristic, or convergence logic to
  judge a candidate. The screening surrogate is for *ranking candidates cheaply*, never for
  *claiming* one. The gate is the only thing that decides.
- **Never edit anything under `verify/`** — that is the trusted stack (verifier, refuter,
  the gate). CI pins its hashes; tampering fails the build and is pointless. If you believe
  the gate is wrong, **stop and tell the human**; do not route around it.
- Believe the gate. If it reports `over_claimed` or `refuted`, your code's real distance is
  lower than you thought — that is the surrogate fooling you, not a gate bug.

Run it on a packaged submission doc:

```
uv run python verify/validate_candidate.py candidate.json   # exit 0 iff passed
```

or in-process (add `verify/` to the path first):
`import sys; sys.path.insert(0, "verify"); from validate_candidate import validate_candidate`.
The verdict's `gates` block is your evidence; `labels` are what you show the human.

## The loop

1. **Pick a direction** → a concrete target: a track cell (locality class × weight class, e.g.
   `unrestricted × weight-6`) plus a family/approach and a budget. If the user's direction is
   vague, translate it: look at the board (`codes/*.json`, the site, `TRACKS.md`) for a **sparse
   cell** or a **record to beat**, and aim there.
2. **Construct** `(HX, HZ)` from a family. Reuse the kit — don't reinvent:
   - `research/bb.py` — bivariate bicycle (start here; weight-6, `unrestricted`).
   - `research/group_algebra.py` — 2BGA over any finite group.
   - `research/coset.py` — coset 2BGA (record efficiencies; weight-8).
   - Write a new `research/sample_<family>.py` **only** for a family the kit can't build.
3. **Screen** many candidates cheaply: `research/search.py` (`screen`, `sample_bb`,
   `pareto_frontier`). This uses the surrogate — an **upper bound**, so it ranks *candidates*,
   nothing more.
4. **Package** the promising ones: `research/submit.make_submission(...)` (recomputes n/k,
   asserts CSS, extracts witnesses, sets `family=` and `confidence="upper_bound"`).
5. **Validate** each with `validate_candidate` (the rule above). Keep only `passed: true`.
6. **Stage** survivors for review (below). Loop until the budget is spent, then report.

## Pitfalls (these are why the gate exists)

- **The surrogate distance is an UPPER BOUND.** A high `d` at low trials usually means the
  search hasn't found the light logical yet — *not* that the code is good. The gate's converge
  step raises trials until it stops dropping; trust that, not your screening number.
- **"Advances the board" ≠ "novel".** The gate labels literature novelty `unverified` — it only
  dedups against *this board*. Never call a candidate a discovery. Say: "advances the
  `<cell>` board; novelty vs the literature unverified."
- **`upper_bound` is not `exact`.** The gate certifies an upper bound (`d<=`). An exact (`d=`)
  claim needs server certification — `research/distance.exact_distance` (scipy MILP) — which is
  slow; only pursue it for a standout the human wants to promote.

## Definition of done (a candidate you may surface)

- `validate_candidate` → `passed: true` (verifies, distance converged, not refuted, not a board
  duplicate).
- Labeled honestly: `confidence: upper_bound`; novelty vs literature flagged unverified;
  "advances this board cell," not "discovery."
- **Staged for review — never committed to `codes/`, never a PR.** The human decides what lands.

## Output & housekeeping

- Write each surviving candidate's **submission JSON + its full validator verdict** to a staging
  folder (e.g. `research/candidates/` or a scratch dir), and print a short ranked summary:
  `[[n,k,d]]`, cell, efficiency `kd²/n`, board-advancing?, and the honest labels.
- **Persist any new constructor code you wrote** and a brief decision journal, so the run is
  reproducible and a good `sample_<family>` can later graduate into `research/`.
- Respect the budget (time / iterations / until-one-find). Log progress. Stop and report — do
  not silently keep going.

## Quick start

```
# one code, end to end (reads like your loop):
uv run python research/recipes/01_build_and_submit_bb.py
# sweep a family, screen, take the best:
uv run python research/recipes/02_search_a_family.py
```

Read `research/GETTING_STARTED.md` for the construction/surrogate/search/packaging details, then
drive the loop above for the user's direction.
