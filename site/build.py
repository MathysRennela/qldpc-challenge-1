"""
Generate the static leaderboard site from codes/*.json into docs/index.html.

Pure Python, no framework. For each track: a Pareto frontier over (n, k, d),
a full sortable table, and an SVG scatter of d vs n. Runs the verifier on each
entry so the displayed params are the computed ones, not the claimed ones.
"""

import glob
import html
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "verify"))
from qldpc_verify import verify

DOCS = os.path.join(ROOT, "docs")


def load_entries():
    entries = []
    for p in sorted(glob.glob(os.path.join(ROOT, "codes", "*.json"))):
        with open(p) as f:
            doc = json.load(f)
        rep = verify(doc)
        if not rep["ok"]:
            continue
        n, k, d = doc["n"], doc["k"], doc["distance"]["d"]
        confs = [doc["distance"][s]["confidence"] for s in ("X", "Z")
                 if s in doc["distance"]]
        tier = "exact" if confs and all(c == "exact" for c in confs) else "ub"
        entries.append({
            "name": doc["name"], "n": n, "k": k, "d": d,
            "eff": round(k * d * d / n, 3), "tier": tier,
            "w": rep["computed"].get("max_check_weight"),
            "tracks": doc["tracks"],
            "authors": ", ".join(doc["provenance"]["authors"]),
            "construction": doc["provenance"].get("construction", ""),
        })
    return entries


def pareto(track_entries):
    """Non-dominated set over (minimize n, maximize k, maximize d)."""
    front = set()
    for i, a in enumerate(track_entries):
        dominated = False
        for j, b in enumerate(track_entries):
            if i == j:
                continue
            if (b["n"] <= a["n"] and b["k"] >= a["k"] and b["d"] >= a["d"]
                    and (b["n"] < a["n"] or b["k"] > a["k"] or b["d"] > a["d"])):
                dominated = True
                break
        if not dominated:
            front.add(i)
    return front


def svg_scatter(entries, front_idx):
    if not entries:
        return ""
    W, H, pad = 460, 300, 44
    ns = [e["n"] for e in entries]
    ds = [e["d"] for e in entries]
    nlo, nhi = min(ns), max(ns)
    dlo, dhi = min(ds), max(ds)
    nlo = min(nlo, 0)
    dlo = min(dlo, 0)
    def sx(n):
        return pad + (n - nlo) / max(nhi - nlo, 1) * (W - 2 * pad)
    def sy(d):
        return H - pad - (d - dlo) / max(dhi - dlo, 1) * (H - 2 * pad)
    pts = []
    for i, e in enumerate(entries):
        filled = i in front_idx
        col = "#2563eb" if e["tier"] == "exact" else "#9ca3af"
        pts.append(
            f'<circle cx="{sx(e["n"]):.1f}" cy="{sy(e["d"]):.1f}" r="5" '
            f'{"fill=\""+col+"\"" if filled else "fill=\"white\" stroke=\""+col+"\""} '
            f'stroke-width="1.5"><title>{html.escape(e["name"])}</title></circle>')
    axis = (f'<line x1="{pad}" y1="{H-pad}" x2="{W-pad}" y2="{H-pad}" '
            f'stroke="#444"/><line x1="{pad}" y1="{pad}" x2="{pad}" '
            f'y2="{H-pad}" stroke="#444"/>')
    labels = (f'<text x="{W/2}" y="{H-8}" text-anchor="middle" '
              f'font-size="12">n (physical qubits)</text>'
              f'<text x="14" y="{H/2}" text-anchor="middle" font-size="12" '
              f'transform="rotate(-90 14 {H/2})">d (distance)</text>')
    return (f'<svg viewBox="0 0 {W} {H}" class="plot">{axis}{labels}'
            + "".join(pts) + "</svg>")


def table(entries, front_idx):
    head = ("<tr><th></th><th>code</th><th>n</th><th>k</th><th>d</th>"
            "<th>kd&sup2;/n</th><th>w</th><th>authors</th></tr>")
    rows = []
    order = sorted(range(len(entries)),
                   key=lambda i: (-entries[i]["k"], -entries[i]["d"],
                                  entries[i]["n"]))
    for i in order:
        e = entries[i]
        star = "&#9733;" if i in front_idx else ""
        badge = ('<span class="exact">d=</span>' if e["tier"] == "exact"
                 else '<span class="ub">d&le;</span>')
        rows.append(
            f'<tr class="{"front" if i in front_idx else ""}">'
            f'<td>{star}</td><td title="{html.escape(e["construction"])}">'
            f'{html.escape(e["name"])}</td><td>{e["n"]}</td><td>{e["k"]}</td>'
            f'<td>{badge} {e["d"]}</td><td>{e["eff"]}</td><td>{e["w"]}</td>'
            f'<td>{html.escape(e["authors"])}</td></tr>')
    return f"<table>{head}{''.join(rows)}</table>"


CSS = """
body{font-family:system-ui,sans-serif;max-width:1000px;margin:2rem auto;
padding:0 1rem;color:#111;line-height:1.5}
h1{margin-bottom:.2rem}.sub{color:#555;margin-top:0}
table{border-collapse:collapse;width:100%;margin:.5rem 0 2rem;font-size:14px}
th,td{border-bottom:1px solid #e5e7eb;padding:.4rem .6rem;text-align:left}
th{border-bottom:2px solid #999}tr.front{background:#f0f6ff}
.exact{color:#2563eb;font-weight:600}.ub{color:#777}
.plot{border:1px solid #eee;background:#fff;float:right;margin:0 0 1rem 1rem}
.track{clear:both;border-top:3px solid #111;padding-top:1rem}
.legend{color:#555;font-size:13px}code{background:#f4f4f4;padding:0 .2rem}
"""


def build():
    entries = load_entries()
    tracks = {}
    for i, e in enumerate(entries):
        for t in e["tracks"]:
            tracks.setdefault(t, []).append(i)
    parts = [f"<!doctype html><meta charset=utf-8><title>qLDPC challenge</title>"
             f"<style>{CSS}</style>",
             "<h1>qLDPC challenge leaderboard</h1>",
             f"<p class=sub>{len(entries)} verified codes across "
             f"{len(tracks)} tracks. "
             '<span class="exact">d=</span> server-certified exact, '
             '<span class="ub">d&le;</span> self-certified upper bound. '
             "&#9733; = on the (n,k,d) Pareto frontier.</p>"]
    for t in sorted(tracks):
        idxs = tracks[t]
        te = [entries[i] for i in idxs]
        fr = pareto(te)
        parts.append(f'<div class="track"><h2>{html.escape(t)} '
                     f'<span class=legend>({len(te)} codes)</span></h2>')
        parts.append(svg_scatter(te, fr))
        parts.append(table(te, fr))
        parts.append("</div>")
    parts.append('<p class=legend>Submit a code by PR; see '
                 '<code>schema/SCHEMA.md</code> and <code>TRACKS.md</code>. '
                 "Baseline codes from arXiv:2504.08887.</p>")
    os.makedirs(DOCS, exist_ok=True)
    with open(os.path.join(DOCS, "index.html"), "w") as f:
        f.write("\n".join(parts))
    print(f"wrote docs/index.html: {len(entries)} codes, {len(tracks)} tracks")


if __name__ == "__main__":
    build()
