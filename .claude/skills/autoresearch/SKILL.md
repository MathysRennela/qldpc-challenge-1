---
name: autoresearch
description: Search for new qLDPC codes on the challenge board. Use when the user gives a research direction (a track cell to attack, a family to try, or a record to beat) and wants an LLM to construct, search, and surface verified candidate codes. Drives the research/ starter kit and the trusted verify/validate_candidate.py gate.
---

# autoresearch

The full, tool-agnostic instructions live in **`research/AUTORESEARCH.md`** (kept there so any
LLM/agent, not just Claude Code, can use them). **Read that file and follow it.**

The one rule, up front so it is never missed:

**No code is a "find" until `verify/validate_candidate.py` returns `passed: true` for it.**
Never write your own distance/quality check, never edit anything under `verify/` (the trusted,
hash-pinned stack), and stage candidates for human review — never commit to `codes/` or open a PR.
