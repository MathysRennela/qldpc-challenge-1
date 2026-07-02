"""Phase A: re-mine board_advanced.json specs with honest, escalating trials.

The old leaderboard screened at trials=100 (wildly optimistic at n~300). Rebuild
each spec, re-estimate in stages (2k -> 20k trials), and keep only candidates
whose ESTIMATE (still an upper bound!) is non-dominated vs the current board in
their own track cell. Output a shortlist for gating + deep refutation.
"""
import json, os, sys, time, glob

sys.path.insert(0, 'research')
sys.path.insert(0, 'verify')
import numpy as np
from group_algebra import dihedral, metacyclic, build_2bga
from css import compute_k, verify_css
from surrogate import distance_rand, lightest_logical

W_ORDER = {"weight-4": 0, "weight-6": 1, "weight-8": 2, "weight-9plus": 3}

def weight_class(HX, HZ):
    w = max(int(HX.sum(1).max()), int(HZ.sum(1).max()))
    return "weight-4" if w <= 4 else "weight-6" if w <= 6 else "weight-8" if w <= 8 else "weight-9plus"

def board_rows():
    rows = []
    for p in sorted(glob.glob('codes/*.json')):
        d = json.load(open(p))
        w = max(max(len(c) for c in d['checks']['X']), max(len(c) for c in d['checks']['Z']))
        wc = "weight-4" if w <= 4 else "weight-6" if w <= 6 else "weight-8" if w <= 8 else "weight-9plus"
        loc = 'local' if d.get('locality') else 'unrestricted'
        rows.append((wc, loc, d['n'], d['k'], d['distance']['d']))
    return rows

BOARD = board_rows()

def dominated(wc, n, k, d):
    # same cell semantics as validate_candidate: a board code competes iff its
    # weight class is <= ours (unrestricted locality assumed for all candidates)
    for bwc, bloc, bn, bk, bd in BOARD:
        if bloc != 'unrestricted':
            continue
        if W_ORDER[bwc] <= W_ORDER[wc]:
            if bn <= n and bk >= k and bd >= d and (bn < n or bk > k or bd > d):
                return True
    return False

def rebuild(spec):
    fam = spec['family']
    if fam == '2bga-dihedral':
        mul, _ = dihedral(spec['m'])
    elif fam == '2bga-metacyclic':
        mul, _ = metacyclic(spec['n'], spec['k_m'], spec['r'])
    else:
        return None
    return build_2bga(mul, spec['a'], spec['b'])

recs = json.load(open('research/board_advanced.json'))
recs = recs if isinstance(recs, list) else recs.get('records', recs)
print(f"loaded {len(recs)} old leaderboard specs", flush=True)

# ---- stage 1: rebuild + 2k-trial estimate, drop dominated ----
stage1 = []
t0 = time.time()
for i, r in enumerate(recs):
    spec = r.get('spec', {})
    try:
        built = rebuild(spec)
        if built is None:
            continue
        HX, HZ = built
        if not verify_css(HX, HZ):
            continue
        n = HX.shape[1]; k = compute_k(HX, HZ)
        if k < 4:
            continue
        wc = weight_class(HX, HZ)
        d_est = distance_rand(HX, HZ, trials=2000)
        if d_est is None or dominated(wc, n, k, d_est):
            continue
        stage1.append({'spec': spec, 'n': n, 'k': k, 'd_est2k': int(d_est), 'wc': wc})
        print(f"  survivor [[{n},{k},<= {d_est}]] {wc} (old claim d={r.get('d')})", flush=True)
    except Exception as e:
        print(f"  spec {i} failed: {e}", flush=True)
print(f"stage1: {len(stage1)} survivors of {len(recs)} ({time.time()-t0:.0f}s)", flush=True)

# ---- stage 2: 20k-trial estimate on survivors, drop dominated ----
final = []
for s in sorted(stage1, key=lambda s: -s['k'] * s['d_est2k']**2 / s['n']):
    if time.time() - t0 > 2400:
        print("time box hit in stage 2; stopping escalation", flush=True)
        break
    HX, HZ = rebuild(s['spec'])
    d20 = distance_rand(HX, HZ, trials=20000)
    s['d_est20k'] = int(d20)
    if dominated(s['wc'], s['n'], s['k'], d20):
        print(f"  dropped [[{s['n']},{s['k']},<= {d20}]] (dominated at 20k trials)", flush=True)
        continue
    print(f"  FINALIST [[{s['n']},{s['k']},<= {d20}]] {s['wc']} eff<= {s['k']*d20**2/s['n']:.2f}", flush=True)
    final.append(s)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'phaseA_shortlist.json')
json.dump(final, open(out, 'w'), indent=1)
print(f"\n{len(final)} finalists -> {out} ({time.time()-t0:.0f}s total)", flush=True)
