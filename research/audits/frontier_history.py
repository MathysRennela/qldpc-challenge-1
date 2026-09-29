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

``--plot`` draws the frontier as what it *is* rather than as a count of it: the
(n, k) plane carrying one staircase per time block, oldest lightest and newest
darkest, so the board's history is the envelope itself creeping up and to the
right (and occasionally slipping back), not a number ticking upward.

  uv run --frozen python research/audits/frontier_history.py
  uv run --frozen python research/audits/frontier_history.py --out /tmp/frontier.csv
  uv run --frozen python research/audits/frontier_history.py --plot frontier.svg
  uv run --frozen python research/audits/frontier_history.py --plot frontier.svg --bucket day

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
    """Yield one row per commit that moves the board's (n, k) picture.

    Each row is ``(date, sha, n_codes, frontier_points, frontier_codes, front)``
    with ``front`` the staircase itself, oldest first.
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
        flat = frontier(points)
        front = set(flat)
        on_front = sum(1 for nk in state.values() if nk in front)
        yield date[:10], sha[:9], len(state), len(front), on_front, tuple(flat)


def svg_counts(rows, path):
    """Write the size series as a dependency-free SVG step chart.

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


# Oldest -> newest: light-warm to dark-cool, so today's staircase is the
# darkest line on the page while the earliest ones still read against white.
_RAMP = ["#f6bd60", "#f8961e", "#e76f51", "#a34a7c", "#4a6fa5", "#1d3557"]


def ramp(t):
    """Hex colour lerped along ``_RAMP`` at position t in [0, 1]."""
    pos = min(max(float(t), 0.0), 1.0) * (len(_RAMP) - 1)
    i = min(int(pos), len(_RAMP) - 2)
    f = pos - i
    lo = [_RAMP[i][j:j + 2] for j in (1, 3, 5)]
    hi = [_RAMP[i + 1][j:j + 2] for j in (1, 3, 5)]
    mix = [round(int(a, 16) + (int(b, 16) - int(a, 16)) * f)
           for a, b in zip(lo, hi)]
    return "#%02x%02x%02x" % tuple(mix)


def bucket_key(iso, bucket):
    """Sort key assigning a date to its day / ISO week / month bucket."""
    day = datetime.date.fromisoformat(iso)
    if bucket == "day":
        return (day.toordinal(),)
    if bucket == "week":
        year, week, _ = day.isocalendar()
        return (year, week)
    return (day.year, day.month)


def snapshots(rows, bucket):
    """Report the board as it stood at the last commit of each bucket.

    Oldest first. A bucket with no commit simply has no row: its frontier is
    the previous bucket's, which is the staircase that would be drawn for it
    anyway.
    """
    out, seen = [], {}
    for row in rows:
        key = bucket_key(row[0], bucket)
        if key in seen:
            out[seen[key]] = row
        else:
            seen[key] = len(out)
            out.append(row)
    return out


def merge_stable(snaps):
    """Collapse buckets that share a frontier into a single curve.

    Returns ``(first_date, last_date, front)`` triples: a staircase is drawn
    only when the frontier actually moved, and its label spans every bucket it
    stayed current for, so an unchanged week is not overdrawn twice in two
    colours that the legend then cannot be read back from.
    """
    out = []
    for date, _sha, _codes, _fp, _fc, front in snaps:
        if out and out[-1][2] == front:
            out[-1][1] = date
        else:
            out.append([date, date, front])
    return [(first, last, front) for first, last, front in out]


def axis_max(value):
    """Return a round upper bound of at most eight ticks, plus the tick step."""
    for step in (5, 10, 20, 25, 50, 100, 200, 250, 500, 1000):
        if value <= step * 7:
            return -(-value // step) * step, step
    return value, 1000


def stair_path(front, sx, sy, x_end):
    """Build the step line of one frontier: flat at k, up at each new n.

    It runs out to ``x_end`` because past the largest n on the frontier no
    larger k exists either, so k_max stays flat out there.
    """
    pts = [f"M{sx(front[0][0]):.1f},{sy(front[0][1]):.1f}"]
    for i in range(1, len(front)):
        n, k = front[i]
        pts.append(f"L{sx(n):.1f},{sy(front[i - 1][1]):.1f}")
        pts.append(f"L{sx(n):.1f},{sy(k):.1f}")
    pts.append(f"L{x_end:.1f},{sy(front[-1][1]):.1f}")
    return " ".join(pts)


def svg_frontier(rows, path, bucket="week"):
    """Draw the frontier as a shape: one staircase per time bucket on (n, k).

    Each bucket's staircase is coloured along ``_RAMP`` from oldest to newest,
    so progress reads as the envelope creeping up and to the right instead of
    as a count ticking over, and an n/k correction reads as a darker curve
    dipping below an older one. The legend is one swatch per curve when they
    fit and a colour strip -- one band per bucket -- when they do not, which is
    what a day bucket needs.
    """
    curves = merge_stable(snapshots(rows, bucket))
    if not curves:
        sys.exit("no frontier snapshots found to plot")

    w, h, left, right, top, bot = 980, 560, 66, 206, 64, 54
    x_end, y_base = w - right, h - bot
    xmax, xstep = axis_max(max(front[-1][0] for _, _, front in curves))
    ymax, ystep = axis_max(max(front[-1][1] for _, _, front in curves))

    def sx(n):
        return left + n / xmax * (x_end - left)

    def sy(k):
        return y_base - k / ymax * (y_base - top)

    colors = ([ramp(1.0)] if len(curves) == 1 else
              [ramp(i / (len(curves) - 1)) for i in range(len(curves))])

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="system-ui,sans-serif">',
        f'<rect width="{w}" height="{h}" fill="#ffffff"/>',
        f'<text x="{left}" y="26" font-size="15" font-weight="600">'
        f'Board (n, k) Pareto frontier, one staircase per {bucket}</text>',
        f'<text x="{left}" y="43" font-size="11.5" fill="#666">'
        'CSS board replayed from git history; lower n and higher k are better; '
        'd, check weight and locality ignored; colour runs oldest to newest'
        '</text>',
    ]
    for v in range(0, ymax + 1, ystep):
        yy = sy(v)
        parts.append(f'<line x1="{left}" y1="{yy:.1f}" x2="{x_end}" '
                     f'y2="{yy:.1f}" stroke="#eee"/>')
        parts.append(f'<text x="{left - 8}" y="{yy + 4:.1f}" font-size="11" '
                     f'fill="#888" text-anchor="end">{v}</text>')
    for v in range(0, xmax + 1, xstep):
        xx = sx(v)
        parts.append(f'<line x1="{xx:.1f}" y1="{top}" x2="{xx:.1f}" '
                     f'y2="{y_base}" stroke="#f4f4f4"/>')
        parts.append(f'<text x="{xx:.1f}" y="{y_base + 16}" font-size="11" '
                     f'fill="#888" text-anchor="middle">{v}</text>')
    parts.append(f'<text x="{(left + x_end) / 2:.1f}" y="{h - 14}" '
                 'font-size="11.5" fill="#666" text-anchor="middle">'
                 'block length n (smaller is better)</text>')
    parts.append(f'<text transform="translate(15,{(top + y_base) / 2:.1f}) '
                 'rotate(-90)" font-size="11.5" fill="#666" '
                 'text-anchor="middle">logical qubits k (higher is better)'
                 '</text>')

    for i, ((_first, _last, front), color) in enumerate(zip(curves, colors)):
        # Today's frontier carries the weight; the rest are one thickness.
        width = 2.5 if i == len(curves) - 1 else 1.7
        parts.append(f'<path d="{stair_path(front, sx, sy, x_end)}" '
                     f'fill="none" stroke="{color}" stroke-width="{width}" '
                     'stroke-linejoin="round"/>')
    parts.append(f'<line x1="{left}" y1="{y_base}" x2="{x_end}" '
                 f'y2="{y_base}" stroke="#bbb"/>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" '
                 f'y2="{y_base}" stroke="#bbb"/>')

    lx = x_end + 16
    if len(curves) * 15 <= y_base - top - 26:
        parts.append(f'<text x="{lx}" y="{top + 2}" font-size="10.5" '
                     'fill="#888">date range  (# n,k points)</text>')
        for i, ((start, end, front), color) in enumerate(zip(curves, colors)):
            yy = top + 24 + i * 15
            label = start if start == end else f"{start}\u2013{end[5:]}"
            last = i == len(curves) - 1
            weight = ' font-weight="600"' if last else ""
            parts.append(f'<line x1="{lx}" y1="{yy - 4:.1f}" '
                         f'x2="{lx + 24}" y2="{yy - 4:.1f}" stroke="{color}" '
                         f'stroke-width="{2.5 if last else 2.4}"/>')
            parts.append(f'<text x="{lx + 30}" y="{yy:.1f}" font-size="11" '
                         f'fill="#444"{weight}>{label}  ({len(front)})</text>')
    else:
        # Too many buckets to list: one band each, stacked oldest at the top.
        parts.append(f'<text x="{lx}" y="{top + 2}" font-size="10.5" '
                     'fill="#888">one band per frontier</text>')
        bar_top, bar_bot, bw = top + 16, y_base - 2, 18
        band = (bar_bot - bar_top) / len(curves)
        for i, color in enumerate(colors):
            yy = bar_top + i * band
            parts.append(f'<rect x="{lx}" y="{yy:.2f}" width="{bw}" '
                         f'height="{band + 0.4:.2f}" fill="{color}"/>')
        parts.append(f'<rect x="{lx}" y="{bar_top:.1f}" width="{bw}" '
                     f'height="{bar_bot - bar_top:.1f}" fill="none" '
                     'stroke="#bbb"/>')
        every = max(1, -(-len(curves) // 6))
        for i in list(range(0, len(curves), every)) + [len(curves) - 1]:
            yy = bar_top + (i + 0.5) * band
            parts.append(f'<text x="{lx + bw + 6}" y="{yy + 3.5:.1f}" '
                         f'font-size="9.5" fill="#666">'
                         f'{curves[i][0][5:]}</text>')

    parts.append("</svg>")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts) + "\n")
    return curves


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=_REPO,
                    help="repository to replay (default: this checkout)")
    ap.add_argument("--out", default=None,
                    help="write the series as CSV here (default: print a summary)")
    ap.add_argument("--plot", default=None,
                    help="write one staircase per time block as an SVG here")
    ap.add_argument("--bucket", default="week",
                    choices=("day", "week", "month"),
                    help="time block for --plot (default: week)")
    ap.add_argument("--plot-counts", default=None,
                    help="write the counts-over-time step chart as an SVG here")
    args = ap.parse_args()

    rows = list(replay(args.repo))
    if not rows:
        sys.exit("no board-moving commits found; is --repo the board's repo?")

    if args.plot:
        curves = svg_frontier(rows, args.plot, args.bucket)
        print(f"wrote {len(curves)} frontiers, one per {args.bucket} "
              f"({curves[0][0]} .. {curves[-1][1]}), to {args.plot}")

    if args.plot_counts:
        svg_counts(rows, args.plot_counts)
        print(f"wrote plot to {args.plot_counts}")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write("date,commit,codes,frontier_points,frontier_codes\n")
            for date, sha, n, fp, fc, _front in rows:
                f.write(f"{date},{sha},{n},{fp},{fc}\n")
        print(f"wrote {len(rows)} rows to {args.out}")

    date, sha, n, fp, fc, _front = rows[-1]
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
