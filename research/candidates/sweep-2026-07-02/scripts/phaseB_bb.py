"""Phase B: BB sweep of the weight-6 x unrestricted gap n in (144, 288).

Board frontier there: [[144,12,12]] then nothing until [[288,12,18]]. A BB code
with n=2*l*m in (150, 286) needs (roughly) k >= 8 and d >= 13, or k >= 12 and
d >= 13, to be non-dominated. Screen broadly at 400 trials, escalate the top
by-efficiency survivors to 8k, then 20k trials; keep non-dominated estimates.

Phase C piggybacked: a support-5 2BGA sweep for the near-empty weight-9plus cell.
"""
import json, os, sys, time

sys.path.insert(0, 'research')
import numpy as np
from search import screen, sample_bb
from bb import build_bb
from group_algebra import metacyclic, dihedral, build_2bga
from css import compute_k, verify_css
from surrogate import distance_rand

BOARD_W6_UNR = [(56,2,8),(66,5,5),(72,12,6),(90,8,10),(120,8,12),(144,12,12),(288,12,18),
                (42,8,3),(45,5,4),(25,1,5),(16,2,4),(64,2,8),(36,2,6)]  # w<=6 unrestricted incl. w4

def dominated_w6(n, k, d):
    for bn, bk, bd in BOARD_W6_UNR:
        if bn <= n and bk >= k and bd >= d and (bn < n or bk > k or bd > d):
            return True
    return False

t0 = time.time()
HERE = os.path.dirname(os.path.abspath(__file__))

# ---- weight-6 BB sweep: l*m in (75, 143) => n in (150, 286) ----
print("screening BB weight-6, n in (150,286)...", flush=True)
cands = sample_bb(1200, l_range=(6, 16), m_range=(5, 13), weight=3, seed=20260702)
sized = ((s, HX, HZ) for (s, HX, HZ) in cands if 150 <= HX.shape[1] <= 286)
recs = screen(sized, min_k=8, min_d=10, trials=400, seed=1)
print(f"screen: {len(recs)} passed min_k=8 min_d=10 ({time.time()-t0:.0f}s)", flush=True)

survivors = []
for r in sorted(recs, key=lambda r: -r['efficiency'])[:20]:
    # rebuild from spec (screen stores spec only)
    HX, HZ = build_bb(r['spec']['l'], r['spec']['m'],
                      [tuple(t) for t in r['spec']['A']], [tuple(t) for t in r['spec']['B']])
    d8 = distance_rand(HX, HZ, trials=8000)
    if dominated_w6(r['n'], r['k'], d8):
        continue
    print(f"  escalated [[{r['n']},{r['k']},<= {d8}]] (screen said {r['d']})", flush=True)
    survivors.append({'spec': r['spec'], 'n': r['n'], 'k': r['k'], 'd_est8k': int(d8), 'wc': 'weight-6'})
    if time.time() - t0 > 1500:
        print("time box hit in BB escalation", flush=True)
        break

final = []
for s in survivors:
    HX, HZ = build_bb(s['spec']['l'], s['spec']['m'],
                      [tuple(t) for t in s['spec']['A']], [tuple(t) for t in s['spec']['B']])
    d20 = distance_rand(HX, HZ, trials=20000)
    s['d_est20k'] = int(d20)
    if not dominated_w6(s['n'], s['k'], d20):
        print(f"  FINALIST [[{s['n']},{s['k']},<= {d20}]] eff<= {s['k']*d20**2/s['n']:.2f}", flush=True)
        final.append(s)

json.dump(final, open(os.path.join(HERE, 'phaseB_shortlist.json'), 'w'), indent=1)
print(f"phase B: {len(final)} finalists ({time.time()-t0:.0f}s)", flush=True)

# ---- Phase C: weight-9plus (support-5 2BGA metacyclic), incumbent [[126,28,8]] eff 14.2 ----
print("\nscreening support-5 2BGA (weight-10 class)...", flush=True)
rng = np.random.default_rng(7)
paramset = [(n, kk, r) for n in range(5, 40) for kk in range(2, 16)
            for r in range(2, n) if 60 <= n*kk <= 200 and pow(r, kk, n) == 1]
c_final = []
tried = 0
for _ in range(300):
    if time.time() - t0 > 2700:
        print("time box hit in phase C", flush=True)
        break
    n_, kk, r_ = paramset[rng.choice(len(paramset))]
    order = n_ * kk
    mul, _ = metacyclic(n_, kk, r_)
    a = [int(x) for x in rng.choice(order, size=5, replace=False)]
    b = [int(x) for x in rng.choice(order, size=5, replace=False)]
    HX, HZ = build_2bga(mul, a, b)
    if not verify_css(HX, HZ):
        continue
    n = HX.shape[1]; k = compute_k(HX, HZ)
    tried += 1
    if k < 8:
        continue
    d_est = distance_rand(HX, HZ, trials=600)
    # incumbent cell: every unrestricted board code competes (weight-9plus is loosest)
    # crude filter: beat [[126,28,8]]-ish territory or advance elsewhere; keep if eff promising
    if d_est and k * d_est**2 / n > 12 and d_est >= 9:
        d8 = distance_rand(HX, HZ, trials=8000)
        if k * d8**2 / n > 12 and d8 >= 9:
            spec = {'family': '2bga-metacyclic-w10', 'n': n_, 'k_m': kk, 'r': r_, 'a': a, 'b': b}
            c_final.append({'spec': spec, 'n': n, 'k': k, 'd_est8k': int(d8), 'wc': 'weight-9plus'})
            print(f"  w10 candidate [[{n},{k},<= {d8}]] eff<= {k*d8**2/n:.2f}", flush=True)

json.dump(c_final, open(os.path.join(HERE, 'phaseC_shortlist.json'), 'w'), indent=1)
print(f"phase C: {len(c_final)} candidates from {tried} built ({time.time()-t0:.0f}s total)", flush=True)
