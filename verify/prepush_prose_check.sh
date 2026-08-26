#!/bin/sh
# Pre-push prose gate: reproduce CI's view of a submission branch before pushing.
#
# CI checks the PR body and changed notes against a tree containing ONLY
# committed files. A local working-tree run of check_prose.py cannot catch
# citations to uncommitted files, because those files exist locally. This
# script runs the check inside a clean worktree of HEAD (staged + committed
# content only), so it fails exactly when CI would.
#
# Usage: verify/prepush_prose_check.sh <pr-body-file>
#   The PR body must be given as a file; pass /dev/null if you have none yet.
#
# Exit 0 = safe to push. Anything else = fix the reported paths first.

set -e

BODY=${1:?usage: verify/prepush_prose_check.sh <pr-body-file>}
ROOT=$(git rev-parse --show-toplevel)
WT=$(mktemp -d "${TMPDIR:-/tmp}/prose-check.XXXXXX")

trap 'git worktree remove --force "$WT" 2>/dev/null' EXIT

# Clean checkout of everything COMMITTED at HEAD. Uncommitted or untracked
# files are invisible here -- which is the entire point.
git worktree add --detach "$WT" HEAD >/dev/null 2>&1

CHANGED=$(git diff --name-only --diff-filter=AMR origin/main...HEAD \
          -- notes/ fieldnotes/ || true)

if [ -z "$CHANGED" ]; then
    echo "no changed notes/fieldnotes vs origin/main; checking PR body only"
    exec python3 "$ROOT/verify/check_prose.py" \
        --root "$WT" --base origin/main --body-file "$BODY"
fi

# Pass the file list via xargs-style splitting; check_prose.py takes --files
# as nargs="*", so word splitting is what we want here (paths have no spaces).
# shellcheck disable=SC2086
python3 "$ROOT/verify/check_prose.py" \
    --root "$WT" \
    --base origin/main \
    --body-file "$BODY" \
    --files $CHANGED
