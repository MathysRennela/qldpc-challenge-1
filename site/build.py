"""
Generate the static leaderboard site into docs/: an index (per-track Pareto
tables) plus one detail page per code under docs/codes/<slug>.html.

Pure Python, no framework. A code's displayed distance tier is earned, not
self-declared: it shows d= only when a server certificate exists in
certs/<slug>.json (d_exact), otherwise d<= (the witness upper bound the cheap
verifier confirmed). Detail pages expose the actual witness, certificate, and
parity checks so the verification is transparent.
"""

import glob
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "verify"))
from qldpc_verify import verify

DOCS = os.path.join(ROOT, "docs")
CERTS = os.path.join(ROOT, "certs")

try:
    BASELINES = json.load(open(os.path.join(ROOT, "baselines.json")))["cells"]
except Exception:
    BASELINES = {}


def vs_paper(k, d, n):
    """Compare to the paper's best published n at (k,d). Returns
    (delta, label, grafted) where delta = paper_n - n (>0 means we beat it),
    or None if no baseline for this cell."""
    b = BASELINES.get(f"{k},{d}")
    if not b:
        return None
    return (b["n"] - n, b["label"], b["grafted"])
REPO = "https://github.com/unitaryfoundation/qldpc-challenge/blob/main"

ACCENT = "#4f46e5"
EXACT = "#059669"

FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="#1e1b4b"/><stop offset="1" stop-color="#4f46e5"/>
</linearGradient></defs>
<rect width="32" height="32" rx="7" fill="url(#g)"/>
<g fill="#c7d2fe">
<circle cx="9" cy="9" r="2.3"/><circle cx="16" cy="9" r="2.3"/>
<circle cx="23" cy="9" r="2.3"/><circle cx="9" cy="16" r="2.3"/>
<circle cx="23" cy="16" r="2.3"/><circle cx="9" cy="23" r="2.3"/>
<circle cx="16" cy="23" r="2.3"/></g>
<circle cx="16" cy="16" r="2.6" fill="#34d399"/>
<circle cx="23" cy="23" r="2.6" fill="#34d399"/></svg>"""

CSS = f"""
:root{{--ink:#0f172a;--mut:#64748b;--ln:#e2e8f0;--ac:{ACCENT};--ex:{EXACT};
--bg:#fff;--soft:#f8fafc}}
*{{box-sizing:border-box}}
body{{font-family:'Inter',system-ui,-apple-system,sans-serif;color:var(--ink);
margin:0;background:var(--bg);line-height:1.55}}
.mono{{font-family:ui-monospace,'SF Mono',Menlo,monospace;font-weight:600}}
.wrap{{max-width:1080px;margin:0 auto;padding:0 24px}}
header.hero{{background:linear-gradient(160deg,#1e1b4b,#4f46e5);color:#fff;
padding:60px 0 52px}}
header.hero h1{{font-size:44px;margin:0 0 8px;letter-spacing:-1px}}
header.hero h1 a{{color:#fff}}
header.hero p{{font-size:18px;max-width:640px;margin:0;color:#dbeafe}}
.stats{{display:flex;gap:40px;margin-top:30px;flex-wrap:wrap}}
.stat .v{{font-size:30px;font-weight:700}}.stat .l{{color:#c7d2fe;font-size:13px;
text-transform:uppercase;letter-spacing:.05em}}
.how{{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin:40px 0}}
.how .card{{border:1px solid var(--ln);border-radius:12px;padding:20px;
background:var(--soft)}}
.how .n{{display:inline-flex;width:26px;height:26px;border-radius:50%;
background:var(--ac);color:#fff;align-items:center;justify-content:center;
font-size:14px;font-weight:700;margin-bottom:10px}}
.how h3{{margin:.2rem 0;font-size:16px}}.how p{{margin:0;color:var(--mut);
font-size:14px}}
.legend{{display:flex;flex-wrap:wrap;gap:18px;margin:28px 0 4px;padding:14px 16px;
background:var(--soft);border:1px solid var(--ln);border-radius:10px;
font-size:13px;color:var(--mut)}}
.legend b{{color:var(--ink)}}
.dot{{display:inline-block;width:11px;height:11px;border-radius:50%;
vertical-align:-1px;margin-right:2px}}
.dot.ex{{background:var(--ex)}}.dot.ac{{background:var(--ac)}}
.dot.ho{{background:#fff;border:2px solid var(--ac)}}
h2.track{{font-size:24px;margin:48px 0 4px;padding-top:24px;
border-top:1px solid var(--ln)}}
.tcount{{color:var(--mut);font-size:14px;font-weight:400}}
.plot{{float:right;width:46%;min-width:360px;margin:0 0 12px 24px;
border:1px solid var(--ln);border-radius:12px;background:#fff;padding:8px}}
table.board{{border-collapse:collapse;width:100%;font-size:14px;margin:12px 0}}
.board th,.board td{{padding:.55rem .7rem;text-align:left;
border-bottom:1px solid var(--ln)}}
.board th{{font-size:12px;text-transform:uppercase;letter-spacing:.04em;
color:var(--mut);cursor:pointer;user-select:none;border-bottom:2px solid var(--ln)}}
.board th:hover{{color:var(--ink)}}.board td.num,.board th.num{{text-align:right;
font-variant-numeric:tabular-nums}}
.board tbody tr{{cursor:pointer}}.board tbody tr:hover{{background:#eef2ff}}
.board tr.fr{{background:#f5f3ff}}.board tr.fr td:first-child{{
box-shadow:inset 3px 0 0 var(--ac)}}
.board tr.fr:hover{{background:#ecebff}}
.star{{color:var(--ac);width:18px}}.cname{{color:var(--mut);font-size:13px}}
.auth{{color:var(--mut);font-size:13px}}
.b{{display:inline-block;font-size:11px;font-weight:700;padding:1px 6px;
border-radius:5px;font-family:ui-monospace,monospace}}
.b.exact{{background:#d1fae5;color:var(--ex)}}.b.ub{{background:#eef2f7;
color:var(--mut)}}
.vswin{{color:var(--ex);font-weight:700}}.vslose{{color:#b45309}}
.vsnone{{color:#cbd5e1}}
footer{{margin:64px 0 48px;padding-top:24px;border-top:1px solid var(--ln);
color:var(--mut);font-size:14px}}
a{{color:var(--ac);text-decoration:none}}a:hover{{text-decoration:underline}}
code{{background:var(--soft);padding:1px 5px;border-radius:4px;font-size:.9em}}
.hit{{cursor:pointer}}
#tip{{position:fixed;pointer-events:none;z-index:60;background:#0f172a;
color:#fff;padding:7px 10px;border-radius:7px;font-size:12px;line-height:1.45;
white-space:pre-line;box-shadow:0 6px 20px rgba(2,6,23,.28);opacity:0;
transition:opacity .06s;max-width:300px}}
#tip.show{{opacity:1}}
/* detail page */
.back{{display:inline-block;margin:24px 0 0;font-size:14px}}
.codehead{{margin:8px 0 0}}.codehead .big{{font-size:32px;letter-spacing:-.5px}}
.params{{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));
gap:1px;background:var(--ln);border:1px solid var(--ln);border-radius:10px;
overflow:hidden;margin:20px 0}}
.params .cell{{background:#fff;padding:12px 14px}}
.params .l{{font-size:11px;text-transform:uppercase;letter-spacing:.04em;
color:var(--mut)}}.params .v{{font-size:20px;font-weight:700;margin-top:2px}}
section.blk{{margin:28px 0}}section.blk h3{{font-size:16px;margin:0 0 8px;
padding-bottom:6px;border-bottom:1px solid var(--ln)}}
.kv{{font-size:14px;margin:4px 0}}.kv b{{color:var(--mut);font-weight:600;
display:inline-block;min-width:120px}}
.wit{{font-family:ui-monospace,monospace;font-size:12px;background:var(--soft);
border:1px solid var(--ln);border-radius:8px;padding:10px;
white-space:pre-wrap;word-break:break-word}}
details{{margin:8px 0}}summary{{cursor:pointer;color:var(--ac);font-size:14px}}
.cert-ok{{color:var(--ex);font-weight:600}}.cert-no{{color:var(--mut)}}
@media(max-width:760px){{.how{{grid-template-columns:1fr}}.plot{{float:none;
width:100%;margin:12px 0}}header.hero h1{{font-size:34px}}}}
"""

JS = """
document.querySelectorAll('table.board').forEach(t=>{
 t.querySelectorAll('th[data-c]').forEach((th)=>{
  let asc=true;
  th.addEventListener('click',()=>{
   const c=th.dataset.c, num=th.classList.contains('num');
   const rows=[...t.querySelectorAll('tbody tr')];
   rows.sort((a,b)=>{let x=a.dataset[c],y=b.dataset[c];
    if(num){x=parseFloat(x);y=parseFloat(y);return asc?x-y:y-x;}
    return asc?(''+x).localeCompare(y):(''+y).localeCompare(x);});
   asc=!asc; const tb=t.querySelector('tbody'); rows.forEach(r=>tb.appendChild(r));
  });
 });
});
document.querySelectorAll('tr[data-href]').forEach(r=>{
 r.addEventListener('click',()=>{location.href=r.dataset.href;});
});
const tip=document.getElementById('tip');
if(tip)document.querySelectorAll('circle.hit').forEach(c=>{
 c.addEventListener('mouseenter',()=>{tip.textContent=c.dataset.tip;
  tip.classList.add('show');});
 c.addEventListener('mousemove',e=>{let x=e.clientX+14,y=e.clientY+14;
  if(x+310>innerWidth)x=e.clientX-tip.offsetWidth-14;
  tip.style.left=x+'px';tip.style.top=y+'px';});
 c.addEventListener('mouseleave',()=>tip.classList.remove('show'));
});
"""


def head(title, rel=""):
    return ("".join([
        "<!doctype html><html lang=en><head><meta charset=utf-8>",
        '<meta name=viewport content="width=device-width,initial-scale=1">',
        f"<title>{html.escape(title)}</title>",
        f'<link rel=icon type="image/svg+xml" href="{rel}favicon.svg">',
        '<link rel=preconnect href="https://fonts.googleapis.com">',
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;'
        '600;700&display=swap" rel=stylesheet>',
        f"<style>{CSS}</style></head><body>"]))


def cert_info(slug):
    p = os.path.join(CERTS, slug + ".json")
    if os.path.exists(p):
        try:
            with open(p) as f:
                return json.load(f)
        except Exception:
            return None
    return None


def load_entries():
    entries = []
    for p in sorted(glob.glob(os.path.join(ROOT, "codes", "*.json"))):
        slug = os.path.splitext(os.path.basename(p))[0]
        with open(p) as f:
            doc = json.load(f)
        rep = verify(doc)
        if not rep["ok"]:
            continue
        cert = cert_info(slug)
        tier = "exact" if (cert and cert.get("d_exact")) else "ub"
        n, k, d = doc["n"], doc["k"], doc["distance"]["d"]
        entries.append({
            "slug": slug, "name": doc["name"], "n": n, "k": k, "d": d,
            "eff": round(k * d * d / n, 3), "tier": tier,
            "w": rep["computed"].get("max_check_weight"),
            "tracks": doc["tracks"],
            "authors": ", ".join(doc["provenance"]["authors"]),
            "authors_list": doc["provenance"]["authors"],
            "construction": doc["provenance"].get("construction", ""),
            "doc": doc, "cert": cert,
        })
    return entries


def pareto(te):
    front = set()
    for i, a in enumerate(te):
        if not any(i != j and b["n"] <= a["n"] and b["k"] >= a["k"]
                   and b["d"] >= a["d"] and (b["n"] < a["n"] or b["k"] > a["k"]
                                             or b["d"] > a["d"])
                   for j, b in enumerate(te)):
            front.add(i)
    return front


def svg(te, front):
    if not te:
        return ""
    W, H, pad = 520, 300, 50
    ns, ds = [e["n"] for e in te], [e["d"] for e in te]
    nhi, dhi = max(ns), max(ds)
    def sx(n):
        return pad + n / max(nhi, 1) * (W - 2 * pad - 10)
    def sy(d):
        return H - pad - d / max(dhi, 1) * (H - 2 * pad)
    grid = []
    step = max(1, round(nhi / 4 / 50) * 50 or 50)
    for gx in range(0, nhi + 1, step):
        x = sx(gx)
        grid.append(f'<line x1="{x:.0f}" y1="{pad}" x2="{x:.0f}" y2="{H-pad}" '
                    f'stroke="#eef2f7"/><text x="{x:.0f}" y="{H-pad+16}" '
                    f'font-size="10" fill="#94a3b8" text-anchor="middle">{gx}</text>')
    for gy in range(0, dhi + 1, max(1, round(dhi / 4) or 1)):
        y = sy(gy)
        grid.append(f'<line x1="{pad}" y1="{y:.0f}" x2="{W-pad}" y2="{y:.0f}" '
                    f'stroke="#eef2f7"/><text x="{pad-8}" y="{y+3:.0f}" '
                    f'font-size="10" fill="#94a3b8" text-anchor="end">{gy}</text>')
    pts = []
    for i, e in enumerate(te):
        f = i in front
        col = EXACT if e["tier"] == "exact" else ACCENT
        r = 6 if f else 4
        fill = col if f else "#fff"
        tip = (f'[[{e["n"]},{e["k"]},{e["d"]}]]  kd2/n={e["eff"]}\n'
               f'{"exact" if e["tier"]=="exact" else "upper bound"}'
               f'{", frontier" if f else ""}\n{e["name"]}')
        cx, cy = sx(e["n"]), sy(e["d"])
        pts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{fill}" '
                   f'stroke="{col}" stroke-width="2" pointer-events="none"/>')
        pts.append(f'<circle class=hit cx="{cx:.1f}" cy="{cy:.1f}" r="12" '
                   f'fill="transparent" data-tip="{html.escape(tip)}"/>')
    return (f'<svg viewBox="0 0 {W} {H}" class="plot" role="img">'
            + "".join(grid)
            + f'<text x="{W/2}" y="{H-4}" font-size="11" fill="#475569" '
            f'text-anchor="middle">n (physical qubits)</text>'
            f'<text x="14" y="{H/2}" font-size="11" fill="#475569" '
            f'text-anchor="middle" transform="rotate(-90 14 {H/2})">d</text>'
            + "".join(pts) + "</svg>")


def badge(tier):
    return ('<span class="b exact">d =</span>' if tier == "exact"
            else '<span class="b ub">d &le;</span>')


def authors_html(lst):
    """Render a GitHub-handle author as a profile link, anything else (e.g. a
    'First Last, ...' citation string) as plain text."""
    out = []
    for a in lst:
        if re.fullmatch(r"[A-Za-z0-9-]+", a):
            out.append(f'<a href="https://github.com/{a}">@{a}</a>')
        else:
            out.append(html.escape(a))
    return ", ".join(out)


def table(te, front):
    head_row = ("<thead><tr><th></th><th data-c=name>code</th>"
                "<th data-c=n class=num>n</th><th data-c=k class=num>k</th>"
                "<th data-c=d class=num>d</th><th data-c=eff class=num>kd&sup2;/n</th>"
                "<th data-c=w class=num>w</th><th data-c=vs class=num>vs paper</th>"
                "<th data-c=auth>authors</th></tr></thead>")
    order = sorted(range(len(te)), key=lambda i: (-te[i]["k"], -te[i]["d"],
                                                  te[i]["n"]))
    rows = []
    for i in order:
        e = te[i]
        fr = i in front
        vp = vs_paper(e["k"], e["d"], e["n"])
        if vp is None:
            vs_cell, vs_sort = '<span class=vsnone>&mdash;</span>', 0
        elif vp[0] > 0:
            g = " (grafted)" if vp[2] else ""
            vs_cell = (f'<span class=vswin title="beats paper {vp[1]}{g} '
                       f'at this (k,d)">&minus;{vp[0]}</span>')
            vs_sort = vp[0]
        else:
            vs_cell = (f'<span class=vslose title="paper {vp[1]} is smaller '
                       f'here">+{-vp[0]}</span>')
            vs_sort = vp[0]
        rows.append(
            f'<tr class="{"fr" if fr else ""}" data-href="codes/{e["slug"]}.html" '
            f'data-name="{html.escape(e["name"])}" data-n="{e["n"]}" '
            f'data-k="{e["k"]}" data-d="{e["d"]}" data-eff="{e["eff"]}" '
            f'data-w="{e["w"]}" data-vs="{vs_sort}" '
            f'data-auth="{html.escape(e["authors"])}">'
            f'<td class="star">{"&#9733;" if fr else ""}</td>'
            f'<td><span class=mono>[[{e["n"]},{e["k"]},{e["d"]}]]</span> '
            f'<span class=cname>{html.escape(e["name"])}</span></td>'
            f'<td class=num>{e["n"]}</td><td class=num>{e["k"]}</td>'
            f'<td class=num>{badge(e["tier"])} {e["d"]}</td>'
            f'<td class=num>{e["eff"]}</td><td class=num>{e["w"]}</td>'
            f'<td class=num>{vs_cell}</td>'
            f'<td class=auth>{authors_html(e["authors_list"])}</td></tr>')
    return f'<table class=board>{head_row}<tbody>{"".join(rows)}</tbody></table>'


def detail_page(e):
    doc, cert = e["doc"], e["cert"]
    n, k, d = e["n"], e["k"], e["d"]
    P = [head(e["name"], rel="../")]
    P.append('<div class=wrap>')
    P.append('<a class=back href="../index.html">&larr; back to the board</a>')
    P.append(f'<div class=codehead><span class="mono big">[[{n},{k},{d}]]</span> '
             f'{badge(e["tier"])}</div>')
    P.append(f'<p style="color:var(--mut);margin:.3rem 0 0">{html.escape(e["name"])}</p>')

    P.append('<div class=params>')
    for lab, val in [("n", n), ("k", k), ("d", d),
                     ("kd&sup2;/n", e["eff"]), ("max check wt", e["w"])]:
        P.append(f'<div class=cell><div class=l>{lab}</div>'
                 f'<div class=v>{val}</div></div>')
    vp = vs_paper(k, d, n)
    if vp is not None:
        g = " grafted" if vp[2] else ""
        if vp[0] > 0:
            txt = f'<span class=vswin>&minus;{vp[0]} vs {vp[1]}{g}</span>'
        elif vp[0] < 0:
            txt = f'<span class=vslose>+{-vp[0]} vs {vp[1]}{g}</span>'
        else:
            txt = f'ties {vp[1]}{g}'
        P.append(f'<div class=cell><div class=l>vs paper (k,d)</div>'
                 f'<div class=v style="font-size:15px">{txt}</div></div>')
    if "locality" in doc:
        loc = doc["locality"]
        P.append(f'<div class=cell><div class=l>layers</div>'
                 f'<div class=v>{loc.get("layers","?")}</div></div>')
        if "interaction_radius" in loc:
            P.append(f'<div class=cell><div class=l>radius</div>'
                     f'<div class=v>{loc["interaction_radius"]:.2f}</div></div>')
    P.append('</div>')

    # distance + certificate
    P.append('<section class=blk><h3>Distance</h3>')
    for side in ("X", "Z"):
        if side in doc["distance"]:
            sd = doc["distance"][side]
            wit = sd["witness"]
            P.append(f'<div class=kv><b>d_{side}</b> {sd["value"]} '
                     f'&middot; witness weight {len(wit)} '
                     f'({"claimed " + sd["confidence"]})</div>')
            P.append(f'<details><summary>witness operator (support, {len(wit)} '
                     f'qubits)</summary><div class=wit>{wit}</div></details>')
    if cert and cert.get("d_exact"):
        notes = "; ".join(f'{s}: {v["note"]}' for s, v in
                          cert.get("sides", {}).items())
        P.append(f'<div class=kv><b>certificate</b> '
                 f'<span class=cert-ok>exact, d = {d}</span> &middot; '
                 f'{html.escape(cert.get("solver",""))}</div>'
                 f'<div class=kv style="color:var(--mut)">{html.escape(notes)}</div>')
    else:
        P.append('<div class=kv><b>certificate</b> '
                 '<span class=cert-no>none yet &middot; distance stands as a '
                 'self-certified upper bound (d &le;)</span></div>')
    P.append('</section>')

    # construction / provenance
    pr = doc["provenance"]
    P.append('<section class=blk><h3>Construction &amp; provenance</h3>')
    P.append(f'<div class=kv><b>authors</b> {authors_html(pr["authors"])}</div>')
    P.append(f'<div class=kv><b>construction</b> {html.escape(pr.get("construction",""))}</div>')
    if pr.get("references"):
        refs = []
        for r in pr["references"]:
            if r.lower().startswith("arxiv:"):
                aid = r.split(":", 1)[1]
                refs.append(f'<a href="https://arxiv.org/abs/{aid}">{html.escape(r)}</a>')
            else:
                refs.append(html.escape(r))
        P.append(f'<div class=kv><b>references</b> {", ".join(refs)}</div>')
    if pr.get("date"):
        P.append(f'<div class=kv><b>date</b> {html.escape(pr["date"])}</div>')
    if pr.get("notes"):
        P.append(f'<div class=kv><b>notes</b> {html.escape(pr["notes"])}</div>')
    P.append(f'<div class=kv><b>tracks</b> {html.escape(", ".join(doc["tracks"]))}</div>')
    P.append('</section>')

    # parity checks
    X, Z = doc["checks"]["X"], doc["checks"]["Z"]
    P.append('<section class=blk><h3>Parity checks</h3>')
    P.append(f'<div class=kv><b>X-checks</b> {len(X)} &middot; '
             f'<b style="min-width:auto">Z-checks</b> {len(Z)}</div>')
    for nm, H in (("H_X", X), ("H_Z", Z)):
        body = "\n".join(str(s) for s in H)
        P.append(f'<details><summary>{nm} ({len(H)} checks, sparse supports)'
                 f'</summary><div class=wit>{body}</div></details>')
    P.append(f'<div class=kv style="margin-top:10px"><a href="{REPO}/codes/'
             f'{e["slug"]}.json">raw submission JSON</a></div>')
    P.append('</section>')

    P.append('</div></body></html>')
    return "\n".join(P)


def build():
    entries = load_entries()
    tracks = {}
    for i, e in enumerate(entries):
        for t in e["tracks"]:
            tracks.setdefault(t, []).append(i)
    n_exact = sum(1 for e in entries if e["tier"] == "exact")
    best_eff = max((e["eff"] for e in entries), default=0)

    P = [head("qLDPC Challenge")]
    P.append('<header class=hero><div class=wrap>'
             '<h1>qLDPC Challenge</h1>'
             '<p>Find better quantum low-density parity-check codes. Submit one '
             'as a pull request, and the verifier checks every parameter '
             'automatically &mdash; including a proof of the distance. If it '
             'holds up, it lands on the board.</p>'
             '<div class=stats>'
             f'<div class=stat><div class=v>{len(entries)}</div>'
             '<div class=l>verified codes</div></div>'
             f'<div class=stat><div class=v>{len(tracks)}</div>'
             '<div class=l>tracks</div></div>'
             f'<div class=stat><div class=v>{n_exact}</div>'
             '<div class=l>certified exact</div></div>'
             f'<div class=stat><div class=v>{best_eff:g}</div>'
             '<div class=l>best kd&sup2;/n</div></div>'
             '</div></div></header>')
    P.append('<div class=wrap>')
    P.append('<div class=how>'
             '<div class=card><span class=n>1</span><h3>Build a code</h3>'
             '<p>A CSS qLDPC code, written as one JSON file with its parity '
             'checks and a distance witness.</p></div>'
             '<div class=card><span class=n>2</span><h3>Open a PR</h3>'
             '<p>Add it under <code>codes/</code>. CI runs the verifier on '
             'every submission automatically.</p></div>'
             '<div class=card><span class=n>3</span><h3>Climb the board</h3>'
             '<p>If it advances a track&rsquo;s frontier it is highlighted. '
             'Click any row for the witness, certificate, and checks.</p>'
             '</div></div>')
    P.append('<div class=legend>'
             '<span>&#9733; <b>frontier</b>: no code beats it on all of '
             '(n, k, d)</span>'
             '<span><span class="dot ex"></span> certified exact '
             '(<span class="b exact">d =</span>)</span>'
             '<span><span class="dot ac"></span> upper bound '
             '(<span class="b ub">d &le;</span>)</span>'
             '<span><span class="dot ho"></span> open point = dominated</span>'
             '<span><span class=vswin>&minus;N</span> = N fewer qubits than the '
             'paper at the same (k,d), arXiv:2504.08887 Table I '
             '(grafted where published)</span>'
             '<span>rows are clickable; hover plot points</span></div>')
    for t in sorted(tracks):
        te = [entries[i] for i in tracks[t]]
        fr = pareto(te)
        P.append(f'<h2 class=track>{html.escape(t)} '
                 f'<span class=tcount>&middot; {len(te)} codes, '
                 f'{len(fr)} on the frontier</span></h2>')
        P.append(svg(te, fr))
        P.append(table(te, fr))
    P.append('<footer>Submit a code by pull request &mdash; see '
             f'<a href="{REPO}/CONTRIBUTING.md">CONTRIBUTING</a>, '
             f'<a href="{REPO}/schema/SCHEMA.md">the schema</a>, and '
             f'<a href="{REPO}/TRACKS.md">the tracks</a>. &#9733; marks the '
             '(n,k,d) Pareto frontier. Baseline codes from arXiv:2504.08887.'
             '</footer>')
    P.append('</div><div id=tip></div>')
    P.append(f'<script>{JS}</script></body></html>')

    os.makedirs(os.path.join(DOCS, "codes"), exist_ok=True)
    with open(os.path.join(DOCS, "index.html"), "w") as f:
        f.write("\n".join(P))
    with open(os.path.join(DOCS, "favicon.svg"), "w") as f:
        f.write(FAVICON)
    for e in entries:
        with open(os.path.join(DOCS, "codes", e["slug"] + ".html"), "w") as f:
            f.write(detail_page(e))
    print(f"wrote docs/index.html + {len(entries)} detail pages, "
          f"{len(tracks)} tracks, {n_exact} certified exact")


if __name__ == "__main__":
    build()
