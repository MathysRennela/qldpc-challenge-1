# Agent guide

This repo is a public, automatically verified leaderboard for quantum LDPC (qLDPC) codes.
The `verify/` stack machine-checks submissions; `research/` is a starter kit for constructing
and searching for new codes.

## Doing autoresearch (finding new codes)

Read **[`research/AUTORESEARCH.md`](research/AUTORESEARCH.md)** and follow it. That is the
tool-agnostic operating manual for the research loop and the reference for the `research/` kit.

The one rule, up front so it is never missed:

**No code is a "find" until `verify/validate_candidate.py` returns `passed: true` for it.**
Never write your own distance/quality check; never edit anything under `verify/` (the trusted,
CI-hash-pinned stack); stage candidates for human review — never commit to `codes/` or open a PR.

A second rule, equally non-negotiable:

**A found low-weight logical (witness) is the most expensive data we produce — never lose it.**
Never run an ad-hoc `python -c` that calls a witness/distance search and only prints the result; that discards the data. Always persist the candidate through the kit's own path: call
`research/kit/submit.make_submission` (which computes and embeds the witness) and then `research/kit/submit.save_submission(doc, "research/candidates/<n>-<k>-<d>.json")`. 
The `research/candidates/` directory is gitignored working output, so writes there are safe and never pollute the board. If a search finds a valid logical but the save fails, that is a hard
error — stop and report it, do not just print.

## Working on the repo itself

- `verify/` is the trust anchor and is hash-pinned in CI (`verify/check_validator_integrity.py`).
  Changing it is deliberate: re-pin with `--update` and get the diff reviewed.
- Submissions live in `codes/` (schema: `schema/code.schema.json`); the board/site is generated
  from them by `site/build.py`. See `CONTRIBUTING.md` and `TRACKS.md`.
