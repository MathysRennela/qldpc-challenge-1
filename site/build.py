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
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "verify"))
from qldpc_verify import verify

DOCS = os.path.join(ROOT, "docs")
CERTS = os.path.join(ROOT, "certs")


def load_refs():
    """Parse refs.bib into an ordered list of entries. Each entry is a dict of
    lowercased field -> value plus 'key' and 'type'. No external dependency: a
    BibTeX file is regular enough that a brace-aware scan handles it."""
    path = os.path.join(ROOT, "refs.bib")
    try:
        text = open(path).read()
    except Exception:
        return []
    entries = []
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,]+),", text):
        typ, key = m.group(1).lower(), m.group(2).strip()
        # capture the entry body by matching balanced braces from the opening {
        i = text.index("{", m.start())
        depth, j = 0, i
        while j < len(text):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        body = text[i + 1:j]
        fields = {"key": key, "type": typ}
        for fm in re.finditer(r"(\w+)\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\}|[^,\n]+)",
                              body):
            name, val = fm.group(1).lower(), fm.group(2).strip()
            if name == key.split(",")[0]:  # skip the key token itself
                continue
            val = re.sub(r"\s+", " ", val).strip().strip(",").strip()
            # resolve the few LaTeX accents, then drop all BibTeX braces (they
            # are case-protection markup, not part of the displayed text).
            val = (val.replace("{\\'e}", "e").replace("\\'e", "e")
                      .replace('{\\"o}', "o").replace('\\"o', "o"))
            val = val.replace("{", "").replace("}", "")
            fields[name] = val
        entries.append(fields)
    return entries


REFS = load_refs()


def _surnames(author_field):
    """Surnames from a BibTeX 'and'-joined author string ('Last, First and ...'
    or 'First Last and ...'), lowercased, for loose citation matching."""
    out = []
    for a in author_field.split(" and "):
        a = a.strip()
        out.append((a.split(",")[0] if "," in a else a.split()[-1]).lower())
    return [s for s in out if s]


def resolve_ref(s):
    """Map a free-text reference string from a submission (e.g. 'arXiv:2504.08887'
    or 'Liang, Eberhardt, Chen') to a refs.bib key, or None. Matches by arXiv id
    or DOI when present, else by author-surname subset."""
    low = s.lower()
    # modern (2504.08887) or old-style (quant-ph/9707021) arXiv id
    am = re.search(r"(\d{4}\.\d{4,5}|[a-z-]+(?:\.[a-z]{2})?/\d{7})", low)
    aid = am.group(1) if am else None
    for e in REFS:
        if aid and e.get("eprint", "").strip() == aid:
            return e["key"]
        doi = e.get("doi", "").lower()
        if doi and doi in low:
            return e["key"]
    if aid:
        return None
    toks = [t for t in re.split(r"[,\s]+", low) if len(t) > 2]
    for e in REFS:
        sn = set(_surnames(e.get("author", "")))
        if sn and toks and set(toks) <= sn:
            return e["key"]
    return None


def cite(s, rel=""):
    """Render a reference string as a link. An arXiv reference links straight to
    the paper on arXiv; any other reference that resolves to a bib entry links
    to its entry on the references page (reachable from the footer too)."""
    if s.lower().startswith("arxiv:"):
        aid = s.split(":", 1)[1]
        return f'<a href="https://arxiv.org/abs/{aid}">{html.escape(s)}</a>'
    key = resolve_ref(s)
    if key:
        return (f'<a href="{rel}references.html#{key}">{html.escape(s)}</a>')
    return html.escape(s)


REPO_ROOT = "https://github.com/unitaryfoundation/qldpc-challenge"
REPO = REPO_ROOT + "/blob/main"
# Public base URL of the deployed site, used to build shareable per-code links.
# Update this to the real domain once the board is hosted.
SITE_URL = "https://unitaryfoundation.github.io/qldpc-challenge"

# Palette (single source of truth; the CSS :root and the inline SVGs all draw
# from these). Greens have two intentional roles: EXACT (deep) for text/marks
# on light backgrounds, GREEN_BRIGHT for marks on the dark surface.
ACCENT = "#4f46e5"        # brand indigo (links, accents, hero glow)
EXACT = "#059669"         # certified-exact green, on light backgrounds
GREEN_BRIGHT = "#34d399"  # green on the dark surface (logo highlight)
DARK = "#0b1020"          # deep surface: hero background + logo/UI tiles

# Logo mark: a six-node cyclic graph (the node-and-edge structure associated
# with qLDPC / Tanner graphs) on a dark tile, one node highlighted. Used for
# the favicon, hero, and footer. All attributes quoted so it is valid as a
# standalone SVG file (parsed as XML) and inline in HTML.
MARK = f"""\
<rect x="1" y="1" width="62" height="62" rx="14" fill="{DARK}" \
stroke="rgba(255,255,255,0.16)" stroke-width="1.5"/>
<g stroke="#ffffff" stroke-width="4" stroke-linecap="round" opacity="0.9">
<line x1="32" y1="14" x2="16" y2="23"/><line x1="16" y1="23" x2="16" y2="41"/>
<line x1="16" y1="41" x2="32" y2="50"/><line x1="32" y1="50" x2="48" y2="41"/>
<line x1="48" y1="41" x2="48" y2="23"/><line x1="48" y1="23" x2="32" y2="14"/></g>
<g fill="#ffffff"><circle cx="16" cy="23" r="5"/><circle cx="16" cy="41" r="5"/>
<circle cx="32" cy="50" r="5"/><circle cx="48" cy="41" r="5"/>
<circle cx="48" cy="23" r="5"/></g>
<circle cx="32" cy="14" r="5.5" fill="{GREEN_BRIGHT}"/>"""

FAVICON = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
           + MARK + "</svg>")

# Small inline copy of the site mark (the hexagon graph), without the dark
# tile and recoloured to the accent so it reads on a light row. Used to flag a
# code as found through the challenge, the way the star flags the frontier.
HEX_MARK = (
    '<svg class=hexmark viewBox="0 0 64 64" width="15" height="15" '
    'aria-hidden="true">'
    '<g stroke="currentColor" stroke-width="5" stroke-linecap="round">'
    '<line x1="32" y1="14" x2="16" y2="23"/><line x1="16" y1="23" x2="16" y2="41"/>'
    '<line x1="16" y1="41" x2="32" y2="50"/><line x1="32" y1="50" x2="48" y2="41"/>'
    '<line x1="48" y1="41" x2="48" y2="23"/><line x1="48" y1="23" x2="32" y2="14"/></g>'
    '<g fill="currentColor"><circle cx="16" cy="23" r="6"/>'
    '<circle cx="16" cy="41" r="6"/><circle cx="32" cy="50" r="6"/>'
    '<circle cx="48" cy="41" r="6"/><circle cx="48" cy="23" r="6"/></g>'
    f'<circle cx="32" cy="14" r="6.5" fill="{GREEN_BRIGHT}"/></svg>')


# GitHub mark (official octocat silhouette), inherits the link color.
GH_ICON = ('<svg viewBox="0 0 16 16" width="18" height="18" fill="currentColor" '
           'aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 '
           '5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49'
           '-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 '
           '1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78'
           '-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 '
           '0 0 .67-.21 2.2.82a7.6 7.6 0 0 1 2-.27c.68 0 1.36.09 2 .27 1.53-1.04 '
           '2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07'
           '-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 '
           '.21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>')

# share icons (monochrome, currentColor). Brand glyphs for X / Bluesky /
# LinkedIn; a link glyph for copy.
LINK_ICON = ('<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"'
             ' aria-hidden="true"><path d="M3.9 12c0-1.71 1.39-3.1 3.1-3.1h4V7H7'
             'c-2.76 0-5 2.24-5 5s2.24 5 5 5h4v-1.9H7c-1.71 0-3.1-1.39-3.1-3.1z'
             'M8 13h8v-2H8v2zm9-6h-4v1.9h4c1.71 0 3.1 1.39 3.1 3.1s-1.39 3.1-3.1'
             ' 3.1h-4V17h4c2.76 0 5-2.24 5-5s-2.24-5-5-5z"/></svg>')
X_ICON = ('<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" '
          'aria-hidden="true"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 '
          '11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08'
          'l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>')
BSKY_ICON = ('<svg viewBox="0 0 568 501" width="18" height="18" '
             'fill="currentColor" aria-hidden="true"><path d="M123.121 33.664C'
             '188.241 82.553 258.281 181.68 284 234.873c25.719-53.193 95.759'
             '-152.32 160.879-201.21C491.866-1.611 568-28.906 568 57.947c0 '
             '17.346-9.945 145.713-15.778 166.555-20.275 72.453-94.155 90.933'
             '-159.875 79.748C507.222 323.8 536.444 388.56 473.333 453.32c'
             '-119.86 122.992-172.272-30.859-185.702-70.281-2.462-7.227-3.614'
             '-10.608-3.631-7.733-.017-2.875-1.169.506-3.631 7.733-13.43 39.422'
             '-65.842 193.273-185.702 70.281-63.111-64.76-33.889-129.52 80.986'
             '-149.071-65.72 11.185-139.6-7.295-159.875-79.748C9.945 203.66 0 '
             '75.293 0 57.947 0-28.906 76.135-1.611 123.121 33.664Z"/></svg>')
LI_ICON = ('<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" '
           'aria-hidden="true"><path d="M20.447 20.452h-3.554v-5.569c0-1.328'
           '-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351'
           'V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 '
           '4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 '
           '2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H'
           '1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C'
           '23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.225 0z"/></svg>')

CSS = f"""
:root{{--ink:#0f172a;--mut:#64748b;--ln:#e2e8f0;--ac:{ACCENT};--ex:{EXACT};
--exb:{GREEN_BRIGHT};--dark:{DARK};--bg:#fff;--soft:#f8fafc}}
*{{box-sizing:border-box}}
/* Use a locally-installed Blippo if present (no font file is shipped, so no
   redistribution of a commercial font); fall back to Inter otherwise. */
@font-face{{font-family:'Blippo';font-display:swap;
src:local('Blippo Black'),local('Blippo-Black'),local('BlippoBlack'),
local('Blippo')}}
body{{font-family:'Blippo','Inter',system-ui,-apple-system,sans-serif;
color:var(--ink);margin:0;background:var(--bg);line-height:1.55}}
.mono{{font-family:'Blippo',ui-monospace,'SF Mono',Menlo,monospace;
font-weight:600}}
.wrap{{max-width:1080px;margin:0 auto;padding:0 24px}}
header.hero{{background:
radial-gradient(115% 130% at 50% -25%,rgba(79,70,229,.5),transparent 62%),
repeating-linear-gradient(0deg,transparent 0 27px,rgba(255,255,255,.05) 27px 28px),
repeating-linear-gradient(90deg,transparent 0 27px,rgba(255,255,255,.05) 27px 28px),
var(--dark);color:#fff;padding:62px 0 54px;
border-bottom:1px solid rgba(255,255,255,.08)}}
.brand{{display:flex;align-items:center;justify-content:space-between;
gap:16px;margin:0 0 8px}}
.brandmark{{display:flex;align-items:center;gap:16px}}
.brand .brandmark svg{{flex:0 0 auto;filter:drop-shadow(0 4px 14px rgba(0,0,0,.35))}}
.ghlink{{display:inline-flex;align-items:center;gap:8px;color:#fff;
text-decoration:none;font-size:14px;font-weight:600;
border:1px solid rgba(255,255,255,.28);border-radius:9px;padding:8px 14px;
background:rgba(255,255,255,.08)}}
.ghlink:hover{{background:rgba(255,255,255,.18)}}
header.hero h1{{font-size:44px;margin:0;letter-spacing:-1px}}
header.hero h1 a{{color:#fff}}
header.hero p{{font-size:18px;max-width:640px;margin:0;color:#dbeafe}}
header.hero p a{{color:#fff;text-decoration:underline}}
.topnav{{display:flex;flex-wrap:wrap;gap:10px;margin-top:20px}}
.topnav a{{display:inline-flex;align-items:center;gap:7px;color:#dbeafe;
font-size:14px;font-weight:600;padding:7px 14px;
border:1px solid rgba(255,255,255,.18);border-radius:8px;
background:rgba(255,255,255,.06)}}
.topnav a:hover{{background:rgba(255,255,255,.16);color:#fff}}
.decnote{{margin:-6px 0 14px;font-size:13px;color:var(--mut);max-width:80ch}}
.decwrap{{max-height:460px;overflow:auto}}
.decsub{{margin:18px 0 4px;border-top:1px solid var(--ln);padding-top:12px}}
.decsub>summary{{cursor:pointer;font-weight:600;font-size:15px;
  list-style:none;display:flex;align-items:center;gap:8px}}
.decsub>summary::before{{content:"\\25B8";color:var(--mut);font-size:12px}}
.decsub[open]>summary::before{{content:"\\25BE"}}
.decsub>summary::-webkit-details-marker{{display:none}}
.decn{{font-weight:400;color:var(--mut);font-size:13px}}
.stats{{display:flex;gap:40px;margin-top:30px;flex-wrap:wrap}}
.stat .v{{font-size:30px;font-weight:700}}.stat .l{{color:#c7d2fe;font-size:13px;
text-transform:uppercase;letter-spacing:.05em}}
.progress{{margin:28px 0 8px;border:1px solid var(--ln);border-radius:14px;
padding:20px 22px;background:var(--soft)}}
.ph{{font-size:13px;margin:0 0 16px;color:var(--mut);letter-spacing:.6px;
text-transform:uppercase;font-weight:700}}
.pmetrics{{display:flex;flex-wrap:wrap;gap:14px 40px;margin-bottom:18px}}
.pm{{display:flex;flex-direction:column}}
.pmn{{font-size:26px;font-weight:700;line-height:1.1}}
.pmsub{{font-size:17px;color:var(--mut);font-weight:600}}
.pml{{font-size:12px;color:var(--mut);margin-top:5px}}
.lb{{margin:18px 0 8px;border:1px solid var(--ln);border-radius:14px;
background:#fff;overflow:hidden}}
.lbhead{{display:flex;justify-content:space-between;align-items:center;gap:16px;
padding:16px 20px;background:var(--soft);border-bottom:1px solid var(--ln)}}
.lbh{{font-size:18px;margin:0}}
.lbsub{{margin:4px 0 0;font-size:13px;color:var(--mut)}}
.lbcta{{flex:0 0 auto;font-size:13px;font-weight:600;color:#fff;
background:var(--ac);border-radius:8px;padding:8px 14px;text-decoration:none}}
.lbcta:hover{{filter:brightness(1.08)}}
.lblist{{max-height:232px;overflow-y:auto}}
.lbrow{{display:flex;align-items:center;gap:14px;padding:11px 20px;
border-bottom:1px solid var(--ln);text-decoration:none;color:var(--ink)}}
.lbrow:last-child{{border-bottom:none}}.lbrow:hover{{background:#f7f8fc}}
.lbrank{{width:20px;text-align:center;color:var(--mut);font-weight:600;
font-variant-numeric:tabular-nums}}
.lbav{{width:34px;height:34px;border-radius:50%;background:var(--soft);
object-fit:cover;flex:0 0 auto}}
.lbname{{flex:1 1 auto;font-weight:600;min-width:0;color:var(--ac)}}
.lbcrown{{margin-left:5px}}
.lbm{{display:flex;flex-direction:column;align-items:center;width:82px;
flex:0 0 auto}}
.lbm b{{font-size:17px;font-variant-numeric:tabular-nums}}
.lbml{{font-size:11px;color:var(--mut);margin-top:1px;white-space:nowrap}}
@media(max-width:680px){{.lbm:nth-child(n+5){{display:none}}.lbm{{width:64px}}}}
.pm.hero{{border-left:3px solid var(--ac);padding-left:13px;cursor:default}}
.pm.hero .pmn{{color:var(--ac)}}
.ptracks{{border-collapse:collapse;width:100%;font-size:13px;background:#fff;
border:1px solid var(--ln);border-radius:8px;overflow:hidden}}
.ptracks th,.ptracks td{{padding:.45rem .7rem;border-bottom:1px solid var(--ln)}}
.ptracks tr:last-child td{{border-bottom:none}}
.ptracks th{{background:var(--soft);color:var(--mut);font-weight:600;
text-align:left}}
.ptracks td:not(:first-child),.ptracks th:not(:first-child){{text-align:center;
font-variant-numeric:tabular-nums}}
.ptracks td:first-child{{font-weight:600}}
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
.legbreak{{flex-basis:100%}}
.collegend{{flex-basis:100%;border-top:1px solid var(--ln);padding-top:10px;
line-height:1.7}}
.dot{{display:inline-block;width:11px;height:11px;border-radius:50%;
vertical-align:-1px;margin-right:2px}}
.dot.ex{{background:var(--ex)}}.dot.ac{{background:var(--ac)}}
.dot.ho{{background:#fff;border:2px solid var(--ac)}}
.swatch{{display:inline-block;width:18px;height:11px;vertical-align:-1px;
margin-right:3px;background:#f5f3ff;border-left:3px solid var(--ac)}}
h2.track{{font-size:24px;margin:48px 0 4px;padding-top:24px;
border-top:1px solid var(--ln);scroll-margin-top:16px}}
.tcount{{color:var(--mut);font-size:14px;font-weight:400}}
.tracknote{{max-width:70ch;margin:6px 0 0;font-size:13px;color:var(--mut)}}
.trackbody{{display:flex;gap:22px;align-items:flex-start;margin:14px 0 4px}}
.gridcol{{flex:0 0 auto}}
.plot{{flex:1 1 0;min-width:0;max-width:520px;align-self:flex-start;
border:1px solid var(--ln);border-radius:12px;background:#fff;padding:8px}}
/* full width (matching the panels above) with fixed, evenly distributed
   columns so the slack isn't dumped into one column as a stray gap. */
table.board{{border-collapse:collapse;width:100%;table-layout:fixed;
font-size:14px;margin:12px 0}}
.board th,.board td{{padding:.55rem .9rem;text-align:left;white-space:nowrap;
border-bottom:1px solid var(--ln)}}
.board th{{font-size:12px;text-transform:uppercase;letter-spacing:.04em;
color:var(--mut);cursor:pointer;user-select:none;border-bottom:2px solid var(--ln)}}
.board th:hover{{color:var(--ink)}}.board td.num,.board th.num{{text-align:center;
font-variant-numeric:tabular-nums}}
.board td.auth{{white-space:normal}}
.hexwrap{{display:inline-flex;align-items:center;margin-left:8px}}
.hexmark{{color:var(--ac);vertical-align:-2px}}
.board tbody tr{{cursor:pointer}}.board tbody tr:hover{{background:#eef2ff}}
.board tr.fr{{background:#f5f3ff}}.board tr.fr td:first-child{{
box-shadow:inset 3px 0 0 var(--ac)}}
.board tr.fr:hover{{background:#ecebff}}
.board tbody tr.xh,.board tbody tr.fr.xh{{background:#fef3c7}}
.board tbody tr.xh td:first-child{{box-shadow:inset 3px 0 0 #f59e0b}}
.cells td.xh{{background:#fde68a;outline:2px solid #f59e0b;outline-offset:-2px}}
.plot circle.pt.xh{{stroke:#f59e0b;stroke-width:4;r:7}}
.plot circle.hit{{cursor:pointer}}
.star{{color:var(--ac);width:18px}}.cname{{color:var(--mut);font-size:13px}}
.auth{{color:var(--mut);font-size:13px}}
.b{{display:inline-block;font-size:11px;font-weight:700;padding:1px 6px;
border-radius:5px;font-family:ui-monospace,monospace}}
.b.exact{{background:#d1fae5;color:var(--ex)}}.b.ub{{background:#eef2f7;
color:var(--mut)}}
.vswin{{color:var(--ex);font-weight:700}}.vslose{{color:#b45309}}
.vsnone{{color:#cbd5e1}}
.gridh{{font-size:14px;color:var(--mut);margin:20px 0 2px;clear:both}}
table.cells{{border-collapse:collapse;margin:6px 0 4px;font-size:13px;
clear:both}}
.cells th,.cells td{{border:1px solid var(--ln);padding:.3rem .45rem;
text-align:center;min-width:30px}}
.cells th{{background:var(--soft);color:var(--mut);font-weight:600}}
.cells td.cellwin{{background:#ecfdf5}}.cells td.celllose{{background:#fff7ed}}
.cells td.cellopen{{color:#cbd5e1;background:repeating-linear-gradient(45deg,
transparent,transparent 4px,#f1f5f9 4px,#f1f5f9 5px)}}
.opendot{{color:#94a3b8;font-weight:700}}
.cells td a{{font-variant-numeric:tabular-nums}}
.gridkey{{display:flex;flex-direction:column;gap:3px;margin:6px 0 2px;
font-size:12px;color:var(--mut)}}
.gridkey .sw{{display:inline-block;width:11px;height:11px;border-radius:3px;
border:1px solid var(--ln);margin-right:6px;vertical-align:-1px}}
.gridkey .sw.win{{background:#ecfdf5}}.gridkey .sw.lose{{background:#fff7ed}}
footer.foot{{margin-top:72px;border-top:1px solid var(--ln);
background:linear-gradient(180deg,var(--soft),var(--bg));color:var(--mut);
font-size:14px}}
.footmain{{max-width:1080px;margin:0 auto;padding:34px 24px 26px;display:flex;
flex-wrap:wrap;gap:24px;justify-content:space-between;align-items:flex-start}}
.footbrand{{max-width:360px}}
.footbrand .fb{{display:flex;align-items:center;gap:12px;margin-bottom:8px}}
.footbrand .fb span{{font-size:18px;font-weight:700;color:var(--ink)}}
.footbrand p{{margin:0;color:var(--mut)}}
.footlinks{{display:flex;flex-wrap:wrap;gap:8px 22px;align-items:center}}
.footlinks a{{display:inline-flex;align-items:center;gap:7px;color:var(--mut);
font-weight:600}}
.footlinks a:hover{{color:var(--ac);text-decoration:none}}
.footlinks svg{{width:16px;height:16px}}
.footbar{{border-top:1px solid var(--ln);text-align:center;padding:16px;
color:var(--mut);font-size:13px}}
a{{color:var(--ac);text-decoration:none}}a:hover{{text-decoration:underline}}
code{{background:var(--soft);padding:1px 5px;border-radius:4px;font-size:.9em}}
.faq{{max-width:64ch;margin:22px 0;padding-bottom:18px;
border-bottom:1px solid var(--ln)}}
.faq h3{{font-size:17px;margin:0 0 6px}}
.faq p{{margin:0;color:var(--mut);line-height:1.6}}
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
.share{{display:flex;flex-wrap:wrap;gap:10px}}
.sharebtn{{cursor:pointer;border:1px solid var(--ln);background:var(--soft);
color:var(--mut);border-radius:9px;width:40px;height:40px;padding:0;
display:inline-flex;align-items:center;justify-content:center;
text-decoration:none;line-height:0}}
.sharebtn:hover{{border-color:var(--ac);color:var(--ac)}}
.sharebtn svg{{display:block}}
.wit{{font-family:ui-monospace,monospace;font-size:12px;background:var(--soft);
border:1px solid var(--ln);border-radius:8px;padding:10px;
white-space:pre-wrap;word-break:break-word}}
details{{margin:8px 0}}summary{{cursor:pointer;color:var(--ac);font-size:14px}}
.cert-ok{{color:var(--ex);font-weight:600}}.cert-no{{color:var(--mut)}}
.ref{{display:flex;gap:16px;padding:16px 0;border-bottom:1px solid var(--ln);
font-size:15px;line-height:1.55;scroll-margin-top:16px}}
.ref:target{{background:var(--soft);border-radius:8px;padding:16px 12px}}
.refkey{{flex:0 0 auto;width:170px;font-family:ui-monospace,monospace;
font-size:12px;color:var(--ac);word-break:break-all}}
.refbody{{flex:1 1 0;min-width:0}}
.refauth{{color:var(--mut)}}
.reftitle{{font-style:italic}}
.refmeta{{color:var(--mut)}}
.refcited{{font-size:12px;color:var(--mut);margin-top:8px;
display:flex;flex-wrap:wrap;gap:6px;align-items:center}}
.refcited a{{font-family:ui-monospace,monospace;font-size:11px;
color:var(--mut);background:var(--soft);border:1px solid var(--ln);
border-radius:5px;padding:1px 6px;white-space:nowrap;text-decoration:none}}
.refcited a:hover{{color:var(--ac);border-color:var(--ac)}}
@media(max-width:680px){{.ref{{flex-direction:column;gap:4px}}
.refkey{{width:auto}}}}
@media(max-width:880px){{.how{{grid-template-columns:1fr}}
.trackbody{{flex-direction:column}}.plot{{flex-basis:auto;width:100%;
position:static}}header.hero h1{{font-size:34px}}}}
"""

JS = """
// Remember where the user was on the board when they open a code, so the
// detail page's "back to the board" link (and the browser back button) return
// to that spot rather than the top of the page.
document.addEventListener('click',e=>{
 if(e.target.closest('a[href^="codes/"],tr[data-href],circle.hit[data-code]'))
  sessionStorage.setItem('boardY', String(window.scrollY));
},true);
(function(){const y=sessionStorage.getItem('boardY');
 if(y!==null){sessionStorage.removeItem('boardY');
  requestAnimationFrame(()=>window.scrollTo(0, parseInt(y,10)));}})();
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
document.querySelectorAll('.tracksec').forEach(sec=>{
 const mark=(code,on)=>sec.querySelectorAll('[data-code="'+code+'"]')
  .forEach(el=>el.classList.toggle('xh',on));
 sec.querySelectorAll('[data-code]').forEach(el=>{
  const code=el.dataset.code;
  el.addEventListener('mouseenter',()=>mark(code,true));
  el.addEventListener('mouseleave',()=>mark(code,false));
 });
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
document.querySelectorAll('circle.hit[data-code]').forEach(c=>{
 c.addEventListener('click',()=>{location.href='codes/'+c.dataset.code+'.html';});
});
"""


def head(title, rel=""):
    return ("".join([
        "<!doctype html><html lang=en><head><meta charset=utf-8>",
        '<meta name=viewport content="width=device-width,initial-scale=1">',
        f"<title>{html.escape(title)}</title>",
        f'<link rel=icon type="image/svg+xml" href="{rel}favicon.svg">',
        '<link rel=preconnect href="https://fonts.googleapis.com">',
        '<link rel=preconnect href="https://fonts.gstatic.com" crossorigin>',
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
            "origin": doc["provenance"].get("origin", "submission"),
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
               f'{", frontier" if f else ""}')
        cx, cy = sx(e["n"]), sy(e["d"])
        pts.append(f'<circle class=pt data-code="{e["slug"]}" cx="{cx:.1f}" '
                   f'cy="{cy:.1f}" r="{r}" fill="{fill}" '
                   f'stroke="{col}" stroke-width="2" pointer-events="none"/>')
        pts.append(f'<circle class=hit data-code="{e["slug"]}" cx="{cx:.1f}" '
                   f'cy="{cy:.1f}" r="12" '
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


def mathfmt(s):
    """Light typographic math for the construction strings: render Python-style
    (x**3) and caret-style (x^-2) powers as superscripts. Laurent exponents can
    be negative. Variables are left in normal text on purpose (the strings mix
    in prose, so blanket italics would catch letters inside words)."""
    return re.sub(r"(?:\*\*|\^)(-?\d+)", r"<sup>\1</sup>", html.escape(s))


def authors_html(lst):
    """A GitHub handle is written with a leading '@' in the data and rendered as
    a profile link; anything else (a paper-author surname or citation string) is
    plain text. So '@vprusso' links, but 'Kitaev' does not."""
    out = []
    for a in lst:
        h = a.strip()
        if h.startswith("@") and re.fullmatch(r"@[A-Za-z0-9-]+", h):
            out.append(f'<a href="https://github.com/{h[1:]}">{h}</a>')
        else:
            out.append(html.escape(h))
    return ", ".join(out)


def table(te, front):
    cols = ('<colgroup><col style="width:4%"><col style="width:18%">'
            '<col style="width:10%"><col style="width:9%">'
            '<col style="width:13%"><col style="width:13%">'
            '<col style="width:9%"><col style="width:24%"></colgroup>')
    head_row = (
        "<thead><tr><th></th>"
        '<th data-c=name title="the code, written [[n,k,d]]">code</th>'
        '<th data-c=n class=num title="physical qubits">n</th>'
        '<th data-c=k class=num title="logical qubits encoded">k</th>'
        '<th data-c=d class=num title="code distance: weight of the smallest '
        'undetectable error">d</th>'
        '<th data-c=eff class=num title="k&middot;d&sup2;/n, a figure of merit; '
        'higher is better">kd&sup2;/n</th>'
        '<th data-c=w class=num title="maximum stabilizer check weight">w</th>'
        '<th data-c=auth title="who submitted it">authors</th></tr></thead>')
    order = sorted(range(len(te)), key=lambda i: (-te[i]["k"], -te[i]["d"],
                                                  te[i]["n"]))
    rows = []
    for i in order:
        e = te[i]
        fr = i in front
        rows.append(
            f'<tr class="{"fr" if fr else ""}" data-href="codes/{e["slug"]}.html" '
            f'data-code="{e["slug"]}" '
            f'data-name="[[{e["n"]},{e["k"]},{e["d"]}]]" data-n="{e["n"]}" '
            f'data-k="{e["k"]}" data-d="{e["d"]}" data-eff="{e["eff"]}" '
            f'data-w="{e["w"]}" '
            f'data-auth="{html.escape(e["authors"])}">'
            f'<td class="star">{"&#9733;" if fr else ""}</td>'
            f'<td><span class=mono>[[{e["n"]},{e["k"]},{e["d"]}]]</span>'
            + ('<span class=hexwrap title="found and submitted through the '
               f'challenge">{HEX_MARK}</span>'
               if e["origin"] != "baseline" else "")
            + '</td>'
            f'<td class=num>{e["n"]}</td><td class=num>{e["k"]}</td>'
            f'<td class=num>{badge(e["tier"])} {e["d"]}</td>'
            f'<td class=num>{e["eff"]}</td><td class=num>{e["w"]}</td>'
            f'<td class=auth>{authors_html(e["authors_list"])}</td></tr>')
    return (f'<table class=board>{cols}{head_row}'
            f'<tbody>{"".join(rows)}</tbody></table>')


def cell_grid(te):
    """Code-tables view: the minimal n at each (k, d) cell for this track.
    Empty cells are flagged as open territory."""
    by = {}
    for e in te:
        key = (e["k"], e["d"])
        if key not in by or e["n"] < by[key]["n"]:
            by[key] = e
    if not by:
        return ""
    ks = sorted({k for k, _ in by}, reverse=True)
    ds = sorted({d for _, d in by})
    head_row = ("<tr><th>k \\ d</th>"
                + "".join(f"<th>{d}</th>" for d in ds) + "</tr>")
    rows = []
    for k in ks:
        cells = [f"<th>{k}</th>"]
        for d in ds:
            e = by.get((k, d))
            if not e:
                cells.append('<td class=cellopen title="no code on the board at '
                             'this (k, d) yet">&middot;</td>')
                continue
            cells.append(
                f'<td data-code="{e["slug"]}"><a href="codes/{e["slug"]}.html" '
                f'title="[[{e["n"]},{k},{d}]] &middot; '
                f'{html.escape(e["authors"])}">{e["n"]}</a></td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return ('<h3 class=gridh>Minimal n by (k, d)</h3>'
            f'<table class=cells>{head_row}{"".join(rows)}</table>'
            '<div class=gridkey><span>each filled cell is the smallest n on the '
            'board for that (k, d)</span><span><span class=opendot>&middot;</span> '
            'open territory (no code there yet)</span></div>')


def detail_page(e, dec=None, phenom=None, circuit=None):
    doc, cert = e["doc"], e["cert"]
    n, k, d = e["n"], e["k"], e["d"]
    P = [head(f"[[{n},{k},{d}]] · qLDPC Challenge", rel="../")]
    P.append('<div class=wrap>')
    P.append('<a class=back href="../index.html">&larr; back to the board</a>')
    P.append(f'<div class=codehead><span class="mono big">[[{n},{k},{d}]]</span> '
             f'{badge(e["tier"])}</div>')

    P.append('<div class=params>')
    params = [
        ("n", n, "physical qubits"),
        ("k", k, "logical qubits"),
        ("d", d, "distance (smallest undetectable error)"),
        ("kd&sup2;/n", e["eff"], "figure of merit, higher is better"),
        ("w", e["w"], "max check weight"),
    ]
    if "locality" in doc:
        loc = doc["locality"]
        params.append(("layers", loc.get("layers", "?"),
                       "physical layers (e.g. 2 for a flip-chip bilayer)"))
        if "interaction_radius" in loc:
            params.append(("radius", f'{loc["interaction_radius"]:.2f}',
                           "interaction radius: max check diameter in the layout"))
    for lab, val, tip in params:
        P.append(f'<div class=cell title="{html.escape(tip)}">'
                 f'<div class=l>{lab}</div><div class=v>{val}</div></div>')
    P.append('</div>')

    # share: a link back to this entry plus pre-filled posts
    url = f"{SITE_URL}/codes/{e['slug']}.html"
    msg = f"[[{n},{k},{d}]] quantum LDPC code on the qLDPC Challenge"
    q = urllib.parse.quote
    x_url = f"https://twitter.com/intent/tweet?text={q(msg)}&url={q(url)}"
    bsky_url = f"https://bsky.app/intent/compose?text={q(msg + ' ' + url)}"
    li_url = ("https://www.linkedin.com/sharing/share-offsite/?url="
              + q(url))
    P.append(
        '<section class=blk><h3>Share this result</h3>'
        '<div class=share>'
        f'<button class=sharebtn type=button data-copy="{html.escape(url)}" '
        f'aria-label="Copy link" title="Copy link">{LINK_ICON}</button>'
        f'<a class=sharebtn href="{html.escape(x_url)}" target=_blank '
        f'rel=noopener aria-label="Post on X" title="Post on X">{X_ICON}</a>'
        f'<a class=sharebtn href="{html.escape(bsky_url)}" target=_blank '
        f'rel=noopener aria-label="Share on Bluesky" title="Bluesky">'
        f'{BSKY_ICON}</a>'
        f'<a class=sharebtn href="{html.escape(li_url)}" target=_blank '
        f'rel=noopener aria-label="Share on LinkedIn" title="LinkedIn">'
        f'{LI_ICON}</a>'
        '</div></section>')

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

    # decoding performance (if this code was evaluated)
    def _dec_line(res, proto, label):
        r = (res or {}).get("results", {}).get(e["slug"]) if res else None
        if not r:
            return ""
        p = (proto or {}).get("p", "?")
        out = (f'<div class=kv><b>{label}</b> per-logical LER '
               f'{r["per_logical_ler"]:.4f} at p={p}')
        plo = proto.get("p_low") if proto else None
        if plo and "per_logical_ler_low" in r:
            out += f' &middot; {r["per_logical_ler_low"]:.4f} at p={plo}'
        return out + '</div>'
    cc_line = _dec_line(dec, (dec or {}).get("protocol", {}), "code-capacity")
    ph_line = _dec_line(phenom, (phenom or {}).get("protocol", {}),
                        "phenomenological")
    ci_line = _dec_line(circuit, (circuit or {}).get("protocol", {}),
                        "circuit-level")
    if cc_line or ph_line or ci_line:
        P.append('<section class=blk><h3>Decoding</h3>')
        P.append('<div class=kv style="color:var(--mut)">Per-logical-qubit '
                 'logical error rate, computed by the evaluator (lower is '
                 'better). See the <a href="../index.html#decoding">Decoding '
                 'leaderboard</a>.</div>')
        P.append(cc_line)
        P.append(ph_line)
        P.append(ci_line)
        P.append('</section>')

    # construction / provenance
    pr = doc["provenance"]
    P.append('<section class=blk><h3>Construction &amp; provenance</h3>')
    P.append(f'<div class=kv><b>authors</b> {authors_html(pr["authors"])}</div>')
    P.append(f'<div class=kv><b>construction</b> {mathfmt(pr.get("construction",""))}</div>')
    if pr.get("references"):
        refs = [cite(r, rel="../") for r in pr["references"]]
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

    P.append("<script>document.querySelectorAll('[data-copy]').forEach("
             "b=>b.addEventListener('click',()=>{navigator.clipboard"
             ".writeText(b.dataset.copy);const o=b.innerHTML;"
             "b.innerHTML='\\u2713';b.title='link copied';"
             "setTimeout(()=>{b.innerHTML=o;b.title='Copy link';},1400);}));"
             "</script>")
    P.append('</div></body></html>')
    return "\n".join(P)


def fmt_citation(e, extra=""):
    """One reference, formatted as HTML: bibtag, authors, title, venue/year,
    links, plus an optional trailing block (e.g. the citing codes)."""
    sn = e.get("author", "")
    authors = " and ".join(a.strip() for a in sn.split(" and ")) if sn else ""
    title = html.escape(e.get("title", e["key"]))
    bits = []
    pages = e.get("pages", "").replace("--", "-")
    if e.get("journal"):
        v = e["journal"]
        if e.get("volume"):
            v += f" {e['volume']}"
        if e.get("number"):
            v += f"({e['number']})"
        if pages:
            v += f":{pages}"
        bits.append(html.escape(v))
    elif e.get("booktitle"):
        v = f"In {e['booktitle']}"
        if pages:
            v += f", pp. {pages}"
        bits.append(html.escape(v))
    if e.get("year"):
        bits.append(html.escape(e["year"]))
    links = []
    if e.get("eprint"):
        links.append(f'<a href="https://arxiv.org/abs/{e["eprint"]}">'
                     f'arXiv:{html.escape(e["eprint"])}</a>')
    if e.get("doi"):
        links.append(f'<a href="https://doi.org/{html.escape(e["doi"])}">doi</a>')
    if e.get("url") and not e.get("eprint") and not e.get("doi"):
        host = re.sub(r"^https?://(www\.)?|/.*$", "", e["url"]) or "link"
        links.append(f'<a href="{html.escape(e["url"])}">{html.escape(host)}</a>')
    out = [f'<div class=ref id="{html.escape(e["key"])}">']
    out.append(f'<span class=refkey>{html.escape(e["key"])}</span>')
    out.append('<div class=refbody>')
    if authors:
        sep = "" if authors.endswith(".") else "."
        out.append(f'<span class=refauth>{html.escape(authors)}{sep}</span> ')
    out.append(f'<span class=reftitle>{title}.</span>')
    if bits:
        out.append(f' <span class=refmeta>{". ".join(bits)}.</span>')
    if links:
        out.append(f' {" &middot; ".join(links)}')
    out.append(extra)
    out.append('</div></div>')
    return "".join(out)


def references_page(entries):
    """Page listing every bib entry, with the codes that cite each one."""
    # which on-board codes cite each key
    citers = {e["key"]: [] for e in REFS}
    for ent in entries:
        for r in ent["doc"]["provenance"].get("references", []):
            k = resolve_ref(r)
            if k and ent["slug"] not in [c[0] for c in citers.get(k, [])]:
                citers.setdefault(k, []).append(
                    (ent["slug"], ent["n"], ent["k"], ent["d"]))
    P = [head("References | qLDPC Challenge", rel="")]
    P.append('<div class=wrap>')
    P.append('<a class=back href="index.html">&larr; back to the board</a>')
    P.append('<h1 style="margin:.4rem 0 0">References</h1>')
    P.append('<p style="color:var(--mut);max-width:60ch">Every paper and tool '
             'the challenge cites. Submissions reference an entry by its arXiv '
             'id or DOI; verified codes that cite each one are listed beneath '
             'it. The machine-readable source is '
             f'<a href="{REPO}/refs.bib">refs.bib</a>.</p>')
    for e in REFS:
        cs = citers.get(e["key"], [])
        extra = ""
        if cs:
            links = "".join(f'<a href="codes/{s}.html">[[{n},{k},{d}]]</a>'
                            for s, n, k, d in
                            sorted(cs, key=lambda c: (c[2], -c[3], c[1])))
            extra = (f'<div class=refcited><span>cited by {len(cs)}</span>'
                     f'{links}</div>')
        P.append(fmt_citation(e, extra))
    P.append('</div></body></html>')
    return "\n".join(P)


def track_anchor(t):
    """Stable HTML id for a track's section, used to link the progress panel
    rows to the track tables below."""
    return "track-" + re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def progress_panel(entries, tracks, n_exact, best_eff):
    """A distinct status-of-progress panel: headline diagnostics plus a
    per-track breakdown. This is the single home for the board's numbers (the
    hero carries none). Contributors counts GitHub-handle authors only (the
    paper baseline source is not a contributor)."""
    n_base = sum(1 for e in entries if e["origin"] == "baseline")
    n_contrib = len(entries) - n_base
    metrics = [
        (str(n_contrib), "new codes",
         "new codes found and submitted through the challenge"),
        (str(n_base), "literature baselines",
         "published codes seeded as the bar to beat"),
        (str(n_exact), "certified exact",
         "distance proven exact by server-side certification (d =)"),
        (f"{best_eff:g}", "best kd&sup2;/n", ""),
    ]
    mhtml = "".join(f'<div class="pm{" hero" if i == 0 else ""}"'
                    f'{f" title=\"{t}\"" if t else ""}>'
                    f'<span class=pmn>{v}</span>'
                    f'<span class=pml>{lab}</span></div>'
                    for i, (v, lab, t) in enumerate(metrics))
    rows = []
    for t in sorted(tracks):
        te = [entries[i] for i in tracks[t]]
        fr = len(pareto(te))
        ex = sum(1 for e in te if e["tier"] == "exact")
        rows.append(f'<tr><td><a href="#{track_anchor(t)}">{html.escape(t)}</a>'
                    f'</td><td>{len(te)}</td>'
                    f'<td>{fr}</td><td>{ex}</td></tr>')
    return ('<section class=progress><h2 class=ph>Progress</h2>'
            f'<div class=pmetrics>{mhtml}</div>'
            '<table class=ptracks><thead><tr><th>track</th>'
            '<th>codes</th><th>on frontier</th>'
            '<th>certified exact</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></section>')


def contributors_panel(entries, tracks):
    """A leaderboard of who has found the codes on the board. Ranks GitHub-handle
    authors of contributed (non-baseline) codes by how many they have on the
    board, then by how many sit on a track frontier, then by best kd2/n. The
    seeded literature authors are not contributors and are excluded."""
    front_slugs = set()
    for idxs in tracks.values():
        te = [entries[i] for i in idxs]
        for j in pareto(te):
            front_slugs.add(te[j]["slug"])
    stats = {}
    for e in entries:
        if e["origin"] == "baseline":
            continue
        for a in e["authors_list"]:
            h = a.strip()
            if not (h.startswith("@") and re.fullmatch(r"@[A-Za-z0-9-]+", h)):
                continue
            s = stats.setdefault(h, {"codes": 0, "front": 0, "exact": 0,
                                     "eff": 0.0})
            s["codes"] += 1
            s["front"] += e["slug"] in front_slugs
            s["exact"] += e["tier"] == "exact"
            s["eff"] = max(s["eff"], e["eff"])
    if not stats:
        return ""
    order = sorted(stats.items(),
                   key=lambda kv: (-kv[1]["codes"], -kv[1]["front"],
                                   -kv[1]["eff"], kv[0]))
    n_codes = sum(1 for e in entries if e["origin"] != "baseline")

    def metric(v, lab):
        return (f'<span class=lbm><b>{v}</b>'
                f'<span class=lbml>{lab}</span></span>')

    rows = []
    for r, (h, s) in enumerate(order, 1):
        crown = ' <span class=lbcrown title="top contributor">&#128081;</span>' \
            if r == 1 else ''
        rows.append(
            f'<a class=lbrow href="https://github.com/{h[1:]}">'
            f'<span class=lbrank>{r}</span>'
            f'<img class=lbav loading=lazy alt="" '
            f'src="https://github.com/{h[1:]}.png?size=64">'
            f'<span class=lbname>{html.escape(h)}{crown}</span>'
            + metric(s["codes"], "codes")
            + metric(s["front"], "on frontier")
            + metric(s["exact"], "exact")
            + metric(f'{s["eff"]:g}', "best kd&sup2;/n")
            + '</a>')
    return ('<section class=lb id=leaderboard><div class=lbhead>'
            '<div><h2 class=lbh>Leaderboard</h2>'
            f'<p class=lbsub>{len(order)} contributor'
            f'{"" if len(order) == 1 else "s"} &middot; {n_codes} codes found '
            'through the challenge</p></div>'
            f'<a class=lbcta href="{REPO}/CONTRIBUTING.md">Add yours</a>'
            '</div>'
            f'<div class=lblist>{"".join(rows)}</div></section>')


FAQ = [
    ("What is a qLDPC code?",
     "A quantum low-density parity-check code. As in classical LDPC codes, the "
     "parity checks are sparse: each check involves only a few qubits and each "
     "qubit appears in only a few checks. It is a stabilizer code (here CSS), "
     "so it has two commuting sets of checks, X-type and Z-type. A code is "
     "summarized as [[n,k,d]]: n physical qubits encode k logical qubits, and "
     "the distance d is the lowest weight of an error that can go undetected."),
    ("Where are qLDPC codes useful?",
     "Fault-tolerant quantum computing. The surface code works but spends a "
     "large number of physical qubits per logical qubit. qLDPC codes can encode "
     "more logical qubits at higher distance for the same number of physical "
     "qubits, while keeping the checks sparse and low-weight so syndrome "
     "extraction stays manageable. They are a leading route to lowering the "
     "qubit overhead of error correction."),
    ("Why does this page exist?",
     "To collect the best known qLDPC codes in one place, with every entry's "
     "parameters checked automatically instead of taken on trust. The "
     "literature is scattered; this gathers codes, verifies them, and ranks "
     "them per track on a Pareto frontier, so it is easy to see the current "
     "state of the art and where there is room to do better."),
    ("What counts as a better code?",
     "Each track ranks codes on a Pareto frontier over (n, k, d). A submission "
     "earns a place by beating that frontier: fewer physical qubits n, more "
     "logical qubits k, or a higher distance d than the codes currently on it. "
     "The board holds the best we know of in each track so you know what to aim "
     "past; it is the bar to beat, not a catalog of every code."),
    ("Why is it hard to find good qLDPC codes?",
     "The checks have to commute (the CSS condition) and stay sparse, which "
     "constrains the construction. You want high k, high d, and low n at the "
     "same time, and those pull against each other. Computing the distance d is "
     "NP-hard, so even measuring how good a candidate is can be expensive. Good "
     "codes tend to come from algebraic constructions (bicycle, product, "
     "lifted) whose parameters are hard to predict, so improving on them is "
     "largely search."),
    ("What does “verified” mean here?",
     "CI runs a verifier on every submission. It recomputes n and k over GF(2), "
     "checks the CSS commutation and the check weights, and confirms the "
     "distance witness is a genuine nontrivial logical operator of the claimed "
     "weight. That certifies the distance as an upper bound (d &le;) with no "
     "trust required. A code shows d= (certified exact) only when an "
     "independent certificate proves no shorter logical operator exists."),
    ("What do d= and d&le; mean, and how is the distance found?",
     "Distance d is the weight of the lightest nontrivial logical operator. "
     "d&le; (upper bound) means a submission exhibits an explicit logical "
     "operator of that weight, found by a decoder-based search (BP+OSD random "
     "coset, or heuristics like QDistEvol); the verifier confirms it is a "
     "genuine logical, so the distance is at most that weight. d= (certified "
     "exact) means a server-side integer program has proven no lighter logical "
     "exists. Exact certification is NP-hard and does not scale, so large codes "
     "carry a tight upper bound while small and moderate codes are certified "
     "exact. A d&le; record is provisional: if the true distance turns out "
     "lower, the entry is corrected."),
    ("What is the difference between the decoding tables?",
     "All three rank codes by per-logical-qubit logical error rate (lower is "
     "better), computed by the server so the number cannot be claimed by the "
     "submitter, but under increasingly realistic noise. Code-capacity: errors "
     "on the data, one perfect round of syndrome extraction; it measures the "
     "code in isolation. Phenomenological: several rounds of stabilizer "
     "measurement where the measurements themselves can be wrong, then a "
     "perfect readout; it adds the time dimension and measurement faults. "
     "Circuit-level: an explicit gate-by-gate syndrome-extraction circuit with "
     "noise on every CX, reset, idle step, and measurement. The circuit table "
     "is a single-basis Z-memory (only the Z stabilizers are extracted, the "
     "ones that catch the errors that flip the Z logical), so it does not "
     "include the X-extraction depth a device also pays. Each step up can "
     "reorder codes the lighter model ties."),
    ("What do I get if I find a new code?",
     "Bragging rights, chiefly. Your code lands on the board under your GitHub "
     "handle with a permanent link you can wave around, and if it advances a "
     "track's frontier it earns the record star (&#9733;). This is an open "
     "community leaderboard, so the rewards are accolades, a citable verified "
     "record, and the quiet respect of the few people who know what a good "
     "kd&sup2;/n means. No prize money, sorry."),
    ("How do I submit?",
     "Add one JSON file under <code>codes/</code> following the schema and open "
     "a pull request; CI verifies it automatically. See "
     f"<a href=\"{REPO}/CONTRIBUTING.md\">CONTRIBUTING</a> and "
     f"<a href=\"{REPO}/schema/SCHEMA.md\">the schema</a>. The "
     "<a href=\"https://github.com/qLDPCOrg/qLDPC\">qLDPC library</a> is a "
     "convenient way to build a code and export its parity checks."),
]


def faq_page():
    P = [head("FAQ | qLDPC Challenge", rel="")]
    P.append('<div class=wrap>')
    P.append('<a class=back href="index.html">&larr; back to the board</a>')
    P.append('<h1 style="margin:.4rem 0 0">FAQ</h1>')
    for q, a in FAQ:
        P.append(f'<div class=faq><h3>{html.escape(q)}</h3><p>{a}</p></div>')
    P.append('</div></body></html>')
    return "\n".join(P)


def decoding_results(name="results.json"):
    p = os.path.join(ROOT, "decode", name)
    if os.path.exists(p):
        try:
            with open(p) as f:
                return json.load(f)
        except Exception:
            return None
    return None


def _dec_rank_items(entries, dec):
    """Sorted (per_logical_ler, entry, result) list for a decoding result set."""
    by_slug = {e["slug"]: e for e in entries}
    items = []
    for slug, r in dec["results"].items():
        e = by_slug.get(slug)
        if e:
            items.append((r["per_logical_ler"], e, r))
    items.sort(key=lambda x: x[0])
    return items


def _dec_rows(items, p_lo):
    def low_cell(r):
        if not p_lo or "per_logical_ler_low" not in r:
            return ""
        return f'<td>{r["per_logical_ler_low"]:.4f}</td>'
    return "".join(
        f'<tr><td class=lbrank>{i}</td>'
        f'<td><a href="codes/{e["slug"]}.html"><span class=mono>'
        f'[[{e["n"]},{e["k"]},{e["d"]}]]</span></a></td>'
        f'<td>{e["k"]}</td><td>{pl:.4f}</td>{low_cell(r)}</tr>'
        for i, (pl, e, r) in enumerate(items, 1))


def _dec_subtable(entries, dec, ref_dec, ref_label, title, intro):
    """A secondary decoding table (phenomenological or circuit-level) ranked by
    the same per-logical metric, with a note on the biggest rank move versus a
    reference ranking (ref_dec), which is the point of the heavier model."""
    if not dec or not dec.get("results"):
        return ""
    proto = dec.get("protocol", {})
    p_hi, p_lo = proto.get("p", "?"), proto.get("p_low")
    items = _dec_rank_items(entries, dec)
    if not items:
        return ""
    move = ""
    if ref_dec and ref_dec.get("results"):
        ref_rank = {e["slug"]: i for i, (_, e, _)
                    in enumerate(_dec_rank_items(entries, ref_dec), 1)}
        cur_rank = {e["slug"]: i for i, (_, e, _) in enumerate(items, 1)}
        both = [e for _, e, _ in items if e["slug"] in ref_rank]
        if both:
            e = max(both, key=lambda e: abs(ref_rank[e["slug"]]
                                            - cur_rank[e["slug"]]))
            if abs(ref_rank[e["slug"]] - cur_rank[e["slug"]]) >= 2:
                move = (f' Versus {ref_label}, [[{e["n"]},{e["k"]},{e["d"]}]] '
                        f'moves from #{ref_rank[e["slug"]]} to '
                        f'#{cur_rank[e["slug"]]}.')
    rows = _dec_rows(items, p_lo)
    lo_hdr = (f'<th>per-logical LER (p={p_lo})</th>' if p_lo else '')
    # Secondary tables collapse by default so the section stays compact.
    return (f'<details class=decsub><summary>{title} '
            f'<span class=decn>({len(items)} codes)</span></summary>'
            f'<p class=decnote>{intro}{move} Ranked at p={p_hi}; the p={p_lo} '
            'column shows scaling.</p>'
            '<div class=decwrap><table class=ptracks><thead><tr><th>#</th>'
            '<th>code</th><th>k</th>'
            f'<th>per-logical LER (p={p_hi})</th>{lo_hdr}'
            '</tr></thead>'
            f'<tbody>{rows}</tbody></table></div></details>')


def phenom_table(entries, dec, cc_dec):
    rnd = (dec or {}).get("protocol", {}).get("rounds", "?")
    intro = (f'The same per-logical metric under phenomenological noise: {rnd} '
             'rounds of stabilizer measurement with measurement faults, then a '
             'perfect readout, decoded by BP+OSD over the circuit detector '
             'error model. This adds the time dimension and measurement errors '
             'that code-capacity ignores.')
    return _dec_subtable(entries, dec, cc_dec, "code-capacity",
                         "Phenomenological (multi-round)", intro)


def circuit_table(entries, dec, ref_dec):
    intro = ('The same per-logical metric under circuit-level noise: an '
             'explicit Z-memory syndrome-extraction circuit with depolarizing '
             'noise on every CX, reset, idle step, and measurement, decoded by '
             'BP+OSD over the circuit detector error model. Single-basis: only '
             'the Z stabilizers are extracted (the errors that flip the Z '
             'logical), so it does not include the X-extraction depth a device '
             'also pays.')
    return _dec_subtable(entries, dec, ref_dec, "phenomenological",
                         "Circuit-level (Z-memory)", intro)


def decoding_leaderboard(entries, dec, phenom=None, circuit=None):
    """Operational ranking by per-logical-qubit logical error rate, computed
    server-side under the pinned code-capacity protocol (decode/results.json)."""
    if not dec or not dec.get("results"):
        return ""
    by_slug = {e["slug"]: e for e in entries}
    proto = dec.get("protocol", {})
    items = []
    for slug, r in dec["results"].items():
        e = by_slug.get(slug)
        if e:
            items.append((r["per_logical_ler"], e, r))
    items.sort(key=lambda x: x[0])
    p_hi, p_lo = proto.get("p", "?"), proto.get("p_low")

    # Concrete evidence that decoding is a separate axis: find the code whose
    # parameter rank (kd^2/n) and decoding rank diverge the most.
    def _eff(e):
        return e["k"] * e["d"] ** 2 / e["n"]
    dec_rank = {e["slug"]: i for i, (_, e, _) in enumerate(items, 1)}
    par_order = sorted((e for _, e, _ in items), key=_eff, reverse=True)
    par_rank = {e["slug"]: i for i, e in enumerate(par_order, 1)}
    divnote = ""
    if len(items) >= 4:
        e = max((e for _, e, _ in items),
                key=lambda e: abs(par_rank[e["slug"]] - dec_rank[e["slug"]]))
        divnote = (
            f' For example [[{e["n"]},{e["k"]},{e["d"]}]] is '
            f'#{par_rank[e["slug"]]} by kd²/n but #{dec_rank[e["slug"]]} '
            f'of {len(items)} here.')

    def low_cell(r):
        if not p_lo or "per_logical_ler_low" not in r:
            return ""
        return f'<td>{r["per_logical_ler_low"]:.4f}</td>'
    rows = "".join(
        f'<tr><td class=lbrank>{i}</td>'
        f'<td><a href="codes/{e["slug"]}.html"><span class=mono>'
        f'[[{e["n"]},{e["k"]},{e["d"]}]]</span></a></td>'
        f'<td>{e["k"]}</td><td>{pl:.4f}</td>{low_cell(r)}'
        f'<td>{r["block_ler"]:.4f}</td></tr>'
        for i, (pl, e, r) in enumerate(items, 1))
    lo_hdr = (f'<th title="per logical qubit at the lower noise rate">'
              f'per-logical LER (p={p_lo})</th>' if p_lo else '')
    return ('<section class=progress id=decoding><h2 class=ph>Decoding</h2>'
            '<p class=decnote>Per-logical-qubit logical error rate under '
            f'code-capacity noise, decoded by '
            f'{html.escape(proto.get("decoder", "BP+OSD"))}. Ranked at '
            f'p={p_hi}; the p={p_lo} column shows how the error rate scales. '
            'Lower is better. This ranks codes by how well they protect '
            'information, a separate axis from (n, k, d): great parameters do '
            f'not imply good decoding.{divnote} The simulation is run here, not claimed '
            'by the submitter, so the number cannot be gamed. Code-capacity, '
            'not circuit-level.</p>'
            '<div class=decwrap><table class=ptracks><thead><tr><th>#</th>'
            '<th>code</th><th>k</th>'
            f'<th title="per logical qubit at the ranking rate">per-logical '
            f'LER (p={p_hi})</th>{lo_hdr}'
            '<th>block LER</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>'
            f'{phenom_table(entries, phenom, dec)}'
            f'{circuit_table(entries, circuit, phenom or dec)}</section>')


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
             '<div class=brand>'
             '<span class=brandmark>'
             f'<svg width=52 height=52 viewBox="0 0 64 64" '
             f'aria-label="qLDPC Challenge logo">{MARK}</svg>'
             '<h1>qLDPC Challenge</h1></span></div>'
             '<p>Find better quantum LDPC codes. '
             '<a href="planar_code_challenge.pdf">Read the whitepaper.</a></p>'
             '<nav class=topnav>'
             '<a href="faq.html">FAQ</a>'
             f'<a href="{REPO}/CONTRIBUTING.md">How to contribute</a>'
             '<a href="#leaderboard">Leaderboard</a>'
             '<a href="#decoding">Decoding</a>'
             f'<a href="{REPO}/TRACKS.md">Tracks</a>'
             '<a href="references.html">References</a>'
             f'<a href="{REPO_ROOT}">{GH_ICON}GitHub</a>'
             '</nav>'
             '</div></header>')
    P.append('<div class=wrap>')
    P.append(progress_panel(entries, tracks, n_exact, best_eff))
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
    P.append(contributors_panel(entries, tracks))
    P.append('<div class=legend>'
             '<span class=legbreak><span class=swatch></span>&#9733; '
             '<b>frontier</b> (shaded rows): no other code beats it on all '
             'of (n, k, d). Plain (unshaded) rows are dominated.</span>'
             '<span><span class="dot ex"></span> certified exact '
             '(<span class="b exact">d =</span>)</span>'
             '<span><span class="dot ac"></span> upper bound '
             '(<span class="b ub">d &le;</span>)</span>'
             '<span><span class="dot ho"></span> open point = dominated</span>'
             f'<span><span class=hexwrap style="margin-left:0">{HEX_MARK}</span> '
             'found through the challenge (unmarked = literature baseline)</span>'
             '<span class=collegend><b>columns:</b> '
             '<b>n</b> physical qubits &middot; <b>k</b> logical qubits '
             '&middot; <b>d</b> distance (smallest undetectable error) '
             '&middot; <b>kd&sup2;/n</b> figure of merit, higher is better '
             '&middot; <b>w</b> max check weight</span>'
             '</div>')
    for t in sorted(tracks):
        te = [entries[i] for i in tracks[t]]
        fr = pareto(te)
        P.append('<section class=tracksec>')
        P.append(f'<h2 class=track id="{track_anchor(t)}">{html.escape(t)} '
                 f'<span class=tcount>&middot; {len(te)} codes, '
                 f'{len(fr)} on the frontier</span></h2>')
        if t.startswith("2d-local"):
            P.append('<p class=tracknote>For 2D-local codes kd&sup2;/n is '
                     'capped by a constant (Bravyi-Poulin-Terhal), unlike '
                     'general qLDPC codes where it can grow with n. The exact '
                     'constant is open. Best known so far: kd&sup2;/n &asymp; '
                     '9.75, the [[323,14,15]] tile code '
                     '(<a href="https://arxiv.org/abs/2606.19482">arXiv:'
                     '2606.19482</a>), the bar to beat on this track.</p>')
        P.append(table(te, fr))
        P.append(f'<div class=trackbody><div class=gridcol>{cell_grid(te)}'
                 f'</div>{svg(te, fr)}</div>')
        P.append('</section>')
    P.append(decoding_leaderboard(entries, decoding_results(),
                                  decoding_results("phenom_results.json"),
                                  decoding_results("circuit_results.json")))
    P.append('</div>')  # close the main content wrap; footer is full-width
    P.append(
        '<footer class=foot><div class=footmain>'
        '<div class=footbrand><div class=fb>'
        f'<svg width=34 height=34 viewBox="0 0 64 64" aria-hidden="true">{MARK}'
        '</svg><span>qLDPC Challenge</span></div>'
        '<p>An open, automatically verified leaderboard for quantum '
        'low-density parity-check codes.</p></div>'
        '<nav class=footlinks>'
        f'<a href="{REPO_ROOT}">{GH_ICON}GitHub</a>'
        f'<a href="{REPO}/CONTRIBUTING.md">Contribute</a>'
        f'<a href="{REPO}/schema/SCHEMA.md">Schema</a>'
        f'<a href="{REPO}/TRACKS.md">Tracks</a>'
        '<a href="faq.html">FAQ</a>'
        '<a href="references.html">References</a>'
        '<a href="planar_code_challenge.pdf">Whitepaper</a>'
        '</nav></div>'
        '<div class=footbar>&copy; 2026 &middot; Built by '
        '<a href="https://unitary.foundation">Unitary Foundation</a> '
        f'&middot; <a href="{REPO}/LICENSE">Apache 2.0</a></div></footer>')
    P.append('<div id=tip></div>')
    P.append(f'<script>{JS}</script></body></html>')

    os.makedirs(os.path.join(DOCS, "codes"), exist_ok=True)
    # serve the raw static files on GitHub Pages without Jekyll processing
    open(os.path.join(DOCS, ".nojekyll"), "w").close()
    with open(os.path.join(DOCS, "index.html"), "w") as f:
        f.write("\n".join(P))
    with open(os.path.join(DOCS, "favicon.svg"), "w") as f:
        f.write(FAVICON)
    with open(os.path.join(DOCS, "references.html"), "w") as f:
        f.write(references_page(entries))
    with open(os.path.join(DOCS, "faq.html"), "w") as f:
        f.write(faq_page())
    slugs = {e["slug"] for e in entries}
    dec_cc = decoding_results()
    dec_ph = decoding_results("phenom_results.json")
    dec_ci = decoding_results("circuit_results.json")
    for e in entries:
        with open(os.path.join(DOCS, "codes", e["slug"] + ".html"), "w") as f:
            f.write(detail_page(e, dec_cc, dec_ph, dec_ci))
    # prune orphan detail pages left behind when a code is removed
    for f in glob.glob(os.path.join(DOCS, "codes", "*.html")):
        if os.path.splitext(os.path.basename(f))[0] not in slugs:
            os.remove(f)

    # machine-readable stats; the README badges (shields.io dynamic JSON) read
    # this file from the live site, so there is no committed badge image to fall
    # out of sync.
    stats = {"verified_codes": len(entries), "certified_exact": n_exact,
             "tracks": len(tracks), "best_kd2_over_n": best_eff}
    with open(os.path.join(DOCS, "stats.json"), "w") as f:
        json.dump(stats, f, indent=2)
    print(f"wrote docs/index.html + {len(entries)} detail pages + "
          f"references.html ({len(REFS)} refs), "
          f"{len(tracks)} tracks, {n_exact} certified exact")


if __name__ == "__main__":
    build()
