#!/usr/bin/env python3
"""Reconstruct the (n, k) Pareto frontier of the board from git history.

The board ranks codes on several axes, but `d` is a witness-backed *upper*
bound and its history is full of downward revisions (``[[882,18,30]]`` -> 29,
``[[684,12,81]]`` -> 66), so a frontier that leans on `d` is largely measuring
which search ran deeper. Drop `d` (and check weight and locality) and what
remains is the honest (n, k) frontier: n lower is better, k higher is better,
so the frontier is the staircase whose k strictly increases as n does.

This script replays ``codes/*.json`` commit by commit and reports, after every
commit that moves it, the number of CSS codes on the board and the size of that
staircase. It is cheap -- the whole history is a few thousand commits, so it
runs in seconds -- and it is non-monotone on purpose: an n/k correction can push
a code off the frontier, and seeing the frontier step *down* is the point.

  uv run --frozen python research/audits/frontier_history.py
  uv run --frozen python research/audits/frontier_history.py --out /tmp/frontier.csv
  uv run --frozen python research/audits/frontier_history.py --plot frontier.svg

Only the main (CSS) board is replayed; general stabilizer codes rank on their
own board and are skipped. n and k are read per file *version*, so an in-place
correction is seen; a rename (which is how a distance tightening lands on
``codes/``) is followed without inventing a new (n, k) point.
"""

import argparse
import datetime
import json
import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", ".."))


def git(args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                          check=False)


def parse_log(text):
    """Parse the commit list from `git log --name-status`, oldest first.

    Each entry is ``(sha, iso_date, [(status, path, dest), ...])`` with status
    one of ``A`` (added), ``M`` (modified), ``D`` (deleted) or ``R`` (renamed,
    ``dest`` set).
    """
    commits, changes = [], None
    for line in text.splitlines():
        if line.startswith("C "):
            _, sha, date = line.split(" ", 2)
            changes = []
            commits.append((sha, date, changes))
        elif changes is None:
            continue
        elif line.startswith(("A\t", "M\t", "D\t")):
            status, path = line.split("\t")
            changes.append((status, path, None))
        elif line.startswith("R"):
            parts = line.split("\t")
            changes.append(("R", parts[1], parts[2]))
    return commits


def fetch_blobs(requests, cwd):
    """Map each ``(sha, path)`` to its blob bytes (or None if absent).

    One ``git cat-file --batch`` call; its output is consumed in request order,
    since the header echoes the blob's own oid rather than the requested rev.
    """
    if not requests:
        return {}
    stdin = "\n".join(f"{sha}:{path}" for sha, path in requests) + "\n"
    out = subprocess.run(["git", "cat-file", "--batch"], cwd=cwd,
                         input=stdin.encode(), capture_output=True,
                         check=False).stdout
    blobs, i = {}, 0
    for sha, path in requests:
        j = out.index(b"\n", i)
        header = out[i:j].split()
        if len(header) == 3 and header[1] != b"missing":
            size = int(header[2])
            blobs[(sha, path)] = out[j + 1:j + 1 + size]
            i = j + 1 + size + 1
        else:
            blobs[(sha, path)] = None
            i = j + 1
    return blobs


def params(raw):
    """``(n, k, code_type)`` from a code blob, or None if it will not parse."""
    if raw is None:
        return None
    try:
        doc = json.loads(raw)
        return int(doc["n"]), int(doc["k"]), doc.get("code_type", "CSS")
    except (ValueError, KeyError, TypeError):
        return None


def frontier(points):
    """Compute the (n, k) antichain: pairs no other beats on both axes.

    Sort by n ascending, and by k descending within an equal n, so that when
    several codes share an n only the highest-k one can survive; a point is on
    the frontier exactly when its k exceeds every k seen so far.
    """
    front, best_k = [], -1
    for n, k in sorted(points, key=lambda t: (t[0], -t[1])):
        if k > best_k:
            best_k = k
            front.append((n, k))
    return front


def replay(repo):
    """Yield ``(date, sha, n_codes, frontier_points, frontier_codes)`` per move.

    One row per commit that changes the board's (n, k) picture, oldest first.
    """
    log = git(["log", "--reverse", "--name-status", "--format=C %H %aI",
               "--", "codes/"], repo)
    if log.returncode != 0:
        sys.exit(f"git log failed: {log.stderr.decode().strip()}")
    commits = parse_log(log.stdout.decode())

    requests = [(sha, path) for sha, _, changes in commits
                for status, path, _ in changes
                if status in ("A", "M") and path.endswith(".json")]
    blobs = fetch_blobs(requests, repo)

    state = {}
    for sha, date, changes in commits:
        moved = False
        for status, path, dest in changes:
            if not path.endswith(".json"):
                continue
            if status == "R":
                value = state.pop(path, None)
                if value is not None:
                    state[dest] = value
                    moved = True
            elif status == "D":
                if state.pop(path, None) is not None:
                    moved = True
            else:
                value = params(blobs.get((sha, path)))
                if value and value[2] == "CSS":
                    if state.get(path) != value[:2]:
                        state[path] = value[:2]
                        moved = True
                elif state.pop(path, None) is not None:
                    moved = True
        if not moved:
            continue
        points = {(n, k) for n, k in state.values()}
        front = set(frontier(points))
        on_front = sum(1 for nk in state.values() if nk in front)
        yield date[:10], sha[:9], len(state), len(front), on_front


def svg_plot(rows, path):
    """Write the series as a dependency-free SVG step chart.

    Two series share one axis: `frontier_points` (the staircase size) and
    `frontier_codes` (codes standing on it, so ties show as a gap). Both stay
    small, so a shared linear axis is honest; the board's code count runs to
    four figures and is deliberately left out rather than rescaled.
    """
    w, h, left, right, top, bot = 900, 340, 62, 18, 44, 46
    days = [datetime.date.fromisoformat(r[0]).toordinal() for r in rows]
    d0, d1 = days[0], days[-1]
    ymax = max(r[4] for r in rows) * 1.12

    def x(day):
        return left + (day - d0) / (d1 - d0) * (w - left - right)

    def y(v):
        return h - bot - v / ymax * (h - top - bot)

    def step_path(idx):
        # A step line: hold each value until the next commit moves it, emitting a
        # point only where the value changes (1738 commits, ~50 real moves).
        pts, prev = [], None
        for day, row in zip(days, rows):
            v = row[idx]
            if prev is None:
                pts.append(f"M{x(day):.1f},{y(v):.1f}")
            elif v != prev:
                pts.append(f"L{x(day):.1f},{y(prev):.1f}")
                pts.append(f"L{x(day):.1f},{y(v):.1f}")
            prev = v
        pts.append(f"L{x(days[-1]):.1f},{y(prev):.1f}")
        return " ".join(pts)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="system-ui,sans-serif">',
        f'<rect width="{w}" height="{h}" fill="#ffffff"/>',
        f'<text x="{left}" y="24" font-size="15" font-weight="600">'
        'Board (n, k) Pareto frontier over time</text>',
        f'<text x="{left}" y="40" font-size="11.5" fill="#666">'
        'CSS board, replayed from git history; d, check weight and locality ignored'
        '</text>',
    ]
    for v in range(0, int(ymax) + 1, 10):
        yy = y(v)
        parts.append(f'<line x1="{left}" y1="{yy:.1f}" x2="{w - right}" '
                     f'y2="{yy:.1f}" stroke="#eee"/>')
        parts.append(f'<text x="{left - 8}" y="{yy + 4:.1f}" font-size="11" '
                     f'fill="#888" text-anchor="end">{v}</text>')
    # Six date ticks, spaced by DATE not by index (commits cluster toward the
    # end, so evenly spaced indices give unevenly spaced dates). Labelled
    # month-day, ends anchored inward, so nothing collides or clips.
    for n in range(6):
        day = d0 + round(n * (d1 - d0) / 5)
        xx = x(day)
        anchor = "start" if n == 0 else "end" if n == 5 else "middle"
        label = datetime.date.fromordinal(day).strftime("%m-%d")
        parts.append(f'<line x1="{xx:.1f}" y1="{top}" x2="{xx:.1f}" '
                     f'y2="{h - bot}" stroke="#f4f4f4"/>')
        parts.append(f'<text x="{xx:.1f}" y="{h - bot + 16}" font-size="11" '
                     f'fill="#888" text-anchor="{anchor}">{label}</text>')
    parts.append(f'<path d="{step_path(4)}" fill="none" stroke="#c2410c" '
                 'stroke-width="2"/>')
    parts.append(f'<path d="{step_path(3)}" fill="none" stroke="#1d4ed8" '
                 'stroke-width="1.6" stroke-dasharray="5 3"/>')
    parts.append(f'<line x1="{left}" y1="{h - bot}" x2="{w - right}" '
                 f'y2="{h - bot}" stroke="#bbb"/>')
    lx = w - right - 250
    parts.append(f'<line x1="{lx}" y1="{top - 14}" x2="{lx + 22}" '
                 f'y2="{top - 14}" stroke="#1d4ed8" stroke-width="1.6" '
                 'stroke-dasharray="5 3"/>')
    parts.append(f'<text x="{lx + 28}" y="{top - 10}" font-size="11.5" '
                 'fill="#444">frontier points (n, k)</text>')
    parts.append(f'<line x1="{lx}" y1="{top - 30}" x2="{lx + 22}" '
                 f'y2="{top - 30}" stroke="#c2410c" stroke-width="2"/>')
    parts.append(f'<text x="{lx + 28}" y="{top - 26}" font-size="11.5" '
                 'fill="#444">codes on the frontier</text>')
    parts.append("</svg>")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=_REPO,
                    help="repository to replay (default: this checkout)")
    ap.add_argument("--out", default=None,
                    help="write the series as CSV here (default: print a summary)")
    ap.add_argument("--plot", default=None,
                    help="write the series as an SVG step chart here")
    args = ap.parse_args()

    rows = list(replay(args.repo))
    if not rows:
        sys.exit("no board-moving commits found; is --repo the board's repo?")

    if args.plot:
        svg_plot(rows, args.plot)
        print(f"wrote plot to {args.plot}")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write("date,commit,codes,frontier_points,frontier_codes\n")
            for date, sha, n, fp, fc in rows:
                f.write(f"{date},{sha},{n},{fp},{fc}\n")
        print(f"wrote {len(rows)} rows to {args.out}")

    date, sha, n, fp, fc = rows[-1]
    print(f"{len(rows)} board-moving commits, {rows[0][0]} .. {rows[-1][0]}")
    print(f"current: {n} CSS codes, {fp} (n,k) points on the frontier, "
          f"{fc} codes standing on it")

    if not args.out:
        step = max(1, len(rows) // 10)
        for row in rows[::step]:
            print(f"  {row[0]}  codes={row[2]:<5} frontier_points={row[3]:<4} "
                  f"frontier_codes={row[4]}")
        print(f"  {rows[-1][0]}  codes={rows[-1][2]:<5} frontier_points="
              f"{rows[-1][3]:<4} frontier_codes={rows[-1][4]}")


if __name__ == "__main__":
    main()
