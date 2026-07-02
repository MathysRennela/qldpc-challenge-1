"""Finalize autoresearch candidates: deep-search honest witnesses, package, gate, stage.

For each shortlisted spec:
  1. rebuild (HX, HZ)
  2. deep per-side witness search with the TRUSTED engine (verify/heuristic_distance.
     ris_min_logical), 2 seeds x 30k trials per side, plus the surrogate's 8k pass
     from make_submission -- claim the LIGHTEST witness anyone found (the Antigravity
     lesson: self-refute before claiming, so CI's deep gate has nothing left to find)
  3. package with make_submission, override the distance block with the deepest witnesses
  4. validate_candidate (trusted gate); keep passed=true AND board_advancing
  5. stage doc + verdict under research/candidates/sweep-2026-07-02/

Usage: uv run python finalize.py shortlist1.json [shortlist2.json ...]
"""
import json, os, sys, time

REPO = '/Users/farrokhlabib/Documents/github/qldpc-challenge'
os.chdir(REPO)
# research/ is mid-refactor into research/kit/; support both layouts
for sub in ('research', 'research/kit', 'research/samplers', 'verify'):
    p = os.path.join(REPO, sub)
    if os.path.isdir(p):
        sys.path.insert(0, p)
import numpy as np
from bb import build_bb
from group_algebra import dihedral, metacyclic, build_2bga
from submit import make_submission
from validate_candidate import validate_candidate
import heuristic_distance as H
import qldpc_verify

STAGE = 'research/candidates/sweep-2026-07-02'
os.makedirs(STAGE, exist_ok=True)
DEEP_TRIALS = 30000
DEEP_SEEDS = (11, 12)

def rebuild(spec):
    fam = spec['family']
    if fam == 'bb':
        return build_bb(spec['l'], spec['m'],
                        [tuple(t) for t in spec['A']], [tuple(t) for t in spec['B']]), \
               'bivariate-bicycle', f"Bivariate bicycle on Z_{spec['l']} x Z_{spec['m']}, A={spec['A']}, B={spec['B']}"
    if fam == '2bga-dihedral':
        mul, _ = dihedral(spec['m'])
        return build_2bga(mul, spec['a'], spec['b']), 'generalized-bicycle', \
               f"2BGA on dihedral group D_{spec['m']}, a={spec['a']}, b={spec['b']}"
    if fam.startswith('2bga-metacyclic'):
        mul, _ = metacyclic(spec['n'], spec['k_m'], spec['r'])
        return build_2bga(mul, spec['a'], spec['b']), 'generalized-bicycle', \
               f"2BGA on metacyclic group (n={spec['n']}, k={spec['k_m']}, r={spec['r']}), a={spec['a']}, b={spec['b']}"
    raise ValueError(fam)

def deep_side(Hown, Hopp, tag):
    best = (None, None)
    for s in DEEP_SEEDS:
        w, wit = H.ris_min_logical(Hown, Hopp, DEEP_TRIALS, s)
        if w is not None and (best[0] is None or w < best[0]):
            best = (int(w), sorted(int(i) for i in np.nonzero(wit)[0]))
        print(f"    {tag} seed {s}: lightest {w}", flush=True)
    return best

seen_sigs = {}
staged = []
t0 = time.time()
for path in sys.argv[1:]:
    if not os.path.exists(path):
        print(f"skip {path} (missing)", flush=True)
        continue
    for cand in json.load(open(path)):
        spec = cand['spec']
        (HX, HZ), family, construction = rebuild(spec)
        n = HX.shape[1]
        print(f"\n=== [[{n},{cand['k']},?]] {spec['family']} (screen est {cand.get('d_est20k', cand.get('d_est8k'))}) ===", flush=True)

        doc = make_submission(
            HX, HZ, name="placeholder", construction=construction,
            authors=["Claude-autoresearch", "@FarLab"], family=family,
            references=["autoresearch sweep 2026-07-02"],
            confidence="upper_bound", trials=8000, seed=3)

        wx, witx = deep_side(HX, HZ, "X")
        wz, witz = deep_side(HZ, HX, "Z")
        for side, w, wit in (("X", wx, witx), ("Z", wz, witz)):
            if w is not None and w < doc['distance'][side]['value']:
                print(f"    deep search beat packaged {side}: {doc['distance'][side]['value']} -> {w}", flush=True)
                doc['distance'][side] = {'value': w, 'confidence': 'upper_bound', 'witness': wit}
        d = min(doc['distance']['X']['value'], doc['distance']['Z']['value'])
        doc['distance']['d'] = d
        k = doc['k']
        doc['name'] = f"[[{n},{k},{d}]] {spec['family']} autoresearch"
        doc['provenance']['notes'] = (
            f"Autoresearch sweep 2026-07-02. Claimed d is the lightest logical found by "
            f"deep self-refutation ({len(DEEP_SEEDS)} seeds x {DEEP_TRIALS} RIS trials per side "
            f"on the trusted engine) -- upper bound only. spec: {json.dumps(spec)}")

        # dedup among this run's own candidates by WL signature
        rep = qldpc_verify.verify(doc, refute=False)
        sig = rep.get('signature', {}).get('hash')
        if sig in seen_sigs:
            print(f"    SKIP: same WL signature as staged {seen_sigs[sig]}", flush=True)
            continue

        verdict = validate_candidate(doc, seed=99)
        adv = verdict['gates'].get('novelty', {}).get('board_advancing', False)
        print(f"    gate: passed={verdict['passed']} advancing={adv} labels={verdict['labels']}", flush=True)
        if not (verdict['passed'] and adv):
            continue
        seen_sigs[sig] = doc['name']
        slug = f"{n}-{k}-{d}"
        json.dump(doc, open(f"{STAGE}/{slug}.json", 'w'), indent=1)
        json.dump(verdict, open(f"{STAGE}/{slug}.verdict.json", 'w'), indent=1)
        staged.append((n, k, d, k*d*d/n, spec['family']))
        print(f"    STAGED {slug} (eff {k*d*d/n:.2f})", flush=True)

print(f"\n==== staged {len(staged)} candidates ({(time.time()-t0)/60:.1f} min) ====", flush=True)
for n, k, d, eff, fam in sorted(staged, key=lambda s: -s[3]):
    print(f"  [[{n},{k},{d}]] eff={eff:.2f} {fam}", flush=True)
