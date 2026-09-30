"""Import paths for the test suite.

This repo is deliberately not installable (`[tool.uv] package = false`), so
`verify/` and `research/kit/` are plain directories rather than packages and
nothing in them is importable by name. Every test used to open with its own
`sys.path.insert` pair to work around that. pytest imports this file before
collecting anything, so the fix belongs here once instead of in every test.
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

for _rel in ("verify", os.path.join("research", "kit"), "research", "cli", "site"):
    _p = os.path.join(ROOT, _rel)
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

# research/candidates/ is gitignored staging output (AGENTS.md), never present
# in CI. The test_*.py files under it are search scripts that collect zero tests
# yet run their module-level search at import, which costs minutes and reads as
# a hung suite -- one takes over 15 min to import. Keep pytest out of it so the
# local suite collects the same tests CI does.
collect_ignore_glob = ["research/candidates", "research/candidates/*"]
