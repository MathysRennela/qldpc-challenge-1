"""Tests for the frontier replay (``frontier_history.py``).

The script exists so that other people can quote its numbers, and its numbers
are only as good as its replay of ``codes/``, so the invariant that matters is
stated once and asserted directly: whatever walk ``replay()`` takes through
history, it must end where the repository is. The final state is compared to
``git ls-tree -r HEAD -- codes/`` read as ``(n, k)`` pairs, CSS only -- three
seconds of git, and the exact check that would have caught a replay that
applies commits in an order the ancestry never had.

Two further properties are pinned because each one is wrong silently if it
regresses: a rename is read at its destination (git reports a rewrite of an
unrelated file as a rename when the similarity check matches, so carrying the
source's ``(n, k)`` over invents a value no blob has), and buckets with an
unchanged frontier collapse into one drawn curve rather than two overlapping
ones the legend cannot be read back from.
"""

import os
import subprocess
import sys
import types

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import frontier_history as fh  # noqa: E402


def head_css_state(repo):
    """``{path: (n, k)}`` for every CSS code in ``git ls-tree -r HEAD``."""
    out = subprocess.run(["git", "ls-tree", "-r", "HEAD", "--", "codes/"],
                         cwd=repo, capture_output=True, text=True,
                         check=True).stdout
    paths = [line.split("\t")[1] for line in out.splitlines()
             if line.split("\t")[1].endswith(".json")]
    blobs = fh.fetch_params([("HEAD", p) for p in paths], repo)
    return {path: value[:2] for (_rev, path), value in blobs.items()
            if value and value[2] == "CSS"}


def test_replay_ends_where_head_is():
    """The state the walk reaches is the state the repository is in.

    This is the whole trust argument for the chart: a replay that ends at a
    board HEAD never had -- one file too many, one file too few, or the same
    file carrying another commit's ``(n, k)`` -- reports a frontier that
    describes the walk rather than the board.
    """
    rows, state = fh.replay(fh._REPO)
    assert rows, "no board-moving commit found"
    assert state == head_css_state(fh._REPO)
    # The last row is the board at the last commit that moved it, and nothing
    # after it moved the board, so the row and HEAD agree on size too.
    assert rows[-1][2] == len(state)


def test_rename_is_read_at_its_destination(monkeypatch):
    """A rename takes the destination's own blob, not the source's value."""
    log = "\n".join([
        "C aaaa1111 2026-01-01T00:00:00+00:00",
        "M\tcodes/old.json",
        "C bbbb2222 2026-01-02T00:00:00+00:00",
        "R100\tcodes/old.json\tcodes/new.json",
    ])
    seen = {}

    def fake_git(args, cwd):
        return types.SimpleNamespace(returncode=0, stdout=log.encode(),
                                     stderr=b"")

    def fake_fetch(requests, cwd):
        seen["requests"] = list(requests)
        return {
            ("aaaa1111", "codes/old.json"): (64, 8, "CSS"),
            ("bbbb2222", "codes/new.json"): (100, 8, "CSS"),
        }

    monkeypatch.setattr(fh, "git", fake_git)
    monkeypatch.setattr(fh, "fetch_params", fake_fetch)

    rows, state = fh.replay("unused")
    assert ("bbbb2222", "codes/new.json") in seen["requests"]
    assert state == {"codes/new.json": (100, 8)}
    assert [r[2] for r in rows] == [1, 1]


def test_frontier_is_a_strict_antichain():
    """A strict antichain: k rises with n, and equal n keeps only the best k."""
    points = [(4, 4), (4, 8), (8, 6), (16, 10), (32, 9)]
    assert fh.frontier(points) == [(4, 8), (16, 10)]

    grid = [(4, 2), (4, 6), (8, 6), (8, 10), (16, 10), (16, 14), (32, 14)]
    front = fh.frontier(grid)
    assert front == [(4, 6), (8, 10), (16, 14)]
    assert all(n1 < n2 and k1 < k2
               for (n1, k1), (n2, k2) in zip(front, front[1:]))
    assert set(front) <= set(grid)


def test_snapshots_keep_the_last_row_of_each_bucket():
    rows = [("2026-01-01", "a", 10, 1, 1, ((4, 4),)),
            ("2026-01-02", "b", 11, 2, 2, ((4, 4), (8, 6))),
            ("2026-01-09", "c", 12, 2, 2, ((4, 4), (8, 6)))]
    assert [r[0] for r in fh.snapshots(rows, "week")] == \
        ["2026-01-02", "2026-01-09"]
    assert [r[0] for r in fh.snapshots(rows, "day")] == [r[0] for r in rows]


def test_an_unchanged_bucket_stays_one_curve():
    """A frontier that did not move is drawn once, labelled over its span."""
    def row(date, front):
        return (date, "x", 10, len(front), 0, tuple(front))

    snaps = [row("2026-01-01", [(4, 4)]), row("2026-01-08", [(4, 4)]),
             row("2026-01-15", [(4, 4), (8, 6)])]
    assert fh.merge_stable(snaps) == [
        ("2026-01-01", "2026-01-08", ((4, 4),)),
        ("2026-01-15", "2026-01-15", ((4, 4), (8, 6))),
    ]


@pytest.mark.parametrize("bucket", ["day", "week", "month"])
def test_bucket_key_is_monotone_within_a_bucket(bucket):
    """Dates inside one bucket share a key and sort with it, not against it."""
    keys = [fh.bucket_key(d, bucket) for d in
            ("2026-01-01", "2026-01-31", "2026-02-01")]
    assert keys == sorted(keys)
