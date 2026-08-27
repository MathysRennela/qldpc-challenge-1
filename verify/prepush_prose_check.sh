#!/bin/sh
# Pre-push prose gate: reproduce CI's view of a submission branch before pushing.
#
# CI checks the PR body and changed notes against a tree containing ONLY
# committed files. This script runs the check inside a clean worktree of
# HEAD, so it fails exactly when CI would.
#
# Usage: BASE=origin/main verify/prepush_prose_check.sh <pr-body-file>
#   The PR body must be given as a file; pass /dev/null if you have none yet.
#
# Exit 0 = safe to push. Anything else = fix the reported paths first.

set -e

BODY=${1:?usage: verify/prepush_prose_check.sh <pr-body-file>}
BASE=${BASE:-origin/main}
ROOT=$(git rev-parse --show-toplevel)
WT=$(mktemp -d "${TMPDIR:-/tmp}/prose-check.XXXXXX")

cleanup() { git worktree remove --force "$WT" >/dev/null 2>&1 || rm -rf "$WT"; }
trap cleanup EXIT

# Fail loudly on uncommitted work: the worktree shows committed content only,
# so a dirty tree means the gate would not see what you might push.
if [ -n "$(git status --porcelain)" ]; then
    echo "ERROR: working tree is dirty; commit (or stash) before running the gate." >&2
    exit 2
fi

# Verify the base ref exists BEFORE degrading behavior on it.
if ! git rev-parse --verify --quiet "$BASE" >/dev/null; then
    echo "ERROR: base ref '$BASE' not found; fetch or set BASE=<ref>." >&2
    exit 2
fi

git worktree add --detach "$WT" HEAD >/dev/null

CHANGED=$(git diff --name-only --diff-filter=AMR "$BASE...HEAD" \
          -- notes/ fieldnotes/ || true)

PY=${QLDPC_PYTHON:-python3}

# No exec here: exec would skip the EXIT trap and leak the worktree.
if [ -z "$CHANGED" ]; then
    echo "no changed notes/fieldnotes vs $BASE; checking PR body only"
    "$PY" "$ROOT/verify/check_prose.py" \
        --root "$WT" --base "$BASE" --body-file "$BODY"
else
    # shellcheck disable=SC2086
    "$PY" "$ROOT/verify/check_prose.py" \
        --root "$WT" --base "$BASE" --body-file "$BODY" --files $CHANGED
fi
