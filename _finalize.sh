#!/bin/bash
set -e
SEED=/home/vrusso/Projects/uf/autoresearch/lean_sandbox/Sierpinski/seed_codes.log
REPO=/home/vrusso/Projects/uf/qldpc-challenge
# 1. wait for seeder to finish (or die)
for i in $(seq 1 600); do
  grep -q "^done" "$SEED" && break
  pgrep -f "python3 seed_codes.py" >/dev/null || break
  sleep 5
done
echo "=== seeder log tail ==="; grep -E "wrote|SKIP|done" "$SEED" | tail -30
cd "$REPO"
echo "=== verify_all ==="; python3 verify/verify_all.py
echo "=== build site ==="; python3 site/build.py
echo "=== commit ==="
git add -A
git -c user.name="Vincent Russo" -c user.email="vincentrusso1@gmail.com" \
  commit -q -m "MVP across phases 1-6: seed dataset, leaderboard site, certification, contributor scaffolding

Phase 2 (seed data): codes/ populated with our certified k=6 record family,
the k=5 notched family, a k=12 point, and paper baselines (k=8 Table V and
k=6 Table I), each with genuine self-certifying distance witnesses, emitted
from the research toolchain.

Phase 4 (site): site/build.py generates docs/index.html, a static
per-track leaderboard (Pareto frontier over (n,k,d), full table, SVG
scatter) computed from the verified entries. Deployed by .github/workflows/
pages.yml.

Phase 5 (certification): verify/certify.py is the dependency-light exact
distance certifier (scipy/HiGHS cutoff IP, no commercial solver) that earns
the d= tier; gf2.py gains kernel_basis/logical_basis to support it.

Phase 6 (contributor UX): CONTRIBUTING.md, PR template, pages deploy
workflow. verify.yml already gates PRs.

Phases 1 and 3 (verifier library, CI) were the Phase 0 commit; this builds
the rest on top."
echo "=== push ==="; git push 2>&1 | tail -2
echo "=== FINALIZE DONE ==="
git log --oneline -2
