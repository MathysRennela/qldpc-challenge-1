#!/usr/bin/env python3
"""Targeted L=350 designed-divisor search; outputs only to research/candidates/."""
from __future__ import annotations
import hashlib, itertools, json, random, sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'research'),str(ROOT/'research'/'kit'),str(ROOT/'verify')]
from designed_divisor_search import factor_polynomial, poly_mul_mod2, low_weight_multiples, build_candidate
from css import compute_k, verify_css, rref
from surrogate import distance_rand
from submit import make_submission
from validate_candidate import validate_candidate

def product(fs):
    g=np.array([1],dtype=np.int8)
    for f in fs: g=poly_mul_mod2(g,f)
    return g

def choose(fs, degrees):
    out=[]
    used=[False]*len(fs)
    for d in degrees:
        for i,f in enumerate(fs):
            if not used[i] and len(f)-1==d:
                out.append(f); used[i]=True; break
    return out

def run(degrees, multiple_limit, pair_budget, seed, label):
    fs=factor_polynomial(350)
    g=product(choose(fs,degrees))
    multiples=low_weight_multiples(g,350,2,multiple_limit,30)
    print(label,'degrees',degrees,'gweight',int(g.sum()),'multiples',len(multiples),flush=True)
    rng=random.Random(seed)
    pairs=list(itertools.combinations_with_replacement(multiples,2))
    rng.shuffle(pairs); pairs=pairs[:pair_budget]
    records=[]; seen=set()
    for idx,(a,b) in enumerate(pairs):
        if len(a)+len(b)>32: continue
        HX,HZ=build_candidate(350,a,b)
        if not verify_css(HX,HZ): continue
        key=(a,b)
        if key in seen: continue
        seen.add(key); k=compute_k(HX,HZ)
        d=distance_rand(HX,HZ,trials=350,seed=seed+idx)
        records.append((float(d),int(k),len(a)+len(b),a,b,HX,HZ,key))
    records.sort(key=lambda r:(r[0]**2*r[1]/700,r[0],r[1]),reverse=True)
    print(label,'screened',len(records),'top',[(r[1],int(r[0]),r[2]) for r in records[:10]],flush=True)
    out=ROOT/'research'/'candidates'; out.mkdir(exist_ok=True)
    passed=0
    for rank,r in enumerate(records[:8]):
        d,k,w,a,b,HX,HZ,key=r
        code_seed=seed+rank*100003+int.from_bytes(hashlib.sha256(key).digest()[:4],'little')
        doc=make_submission(HX,HZ,name=f'[[700,{k},d<={int(d)}]] L350 designed-divisor GB',construction=(f'Cyclic generalized bicycle over Z_350; common divisor degree {sum(degrees)} assembled from GF(2) factors of x^350+1; A={list(a)}, B={list(b)}.'),authors=['@mathysrennela'],family='generalized-bicycle',confidence='upper_bound',trials=1500,seed=code_seed)
        verdict=validate_candidate(doc,seed=code_seed+700000,refute=True)
        fp=hashlib.sha256(key).hexdigest()[:16]
        stem=f'l350-{doc["n"]}-{doc["k"]}-{doc["distance"]["d"]}-{fp}'
        (out/(stem+'.json')).write_text(json.dumps(doc,indent=2)+'\n')
        (out/(stem+'.verdict.json')).write_text(json.dumps(verdict,indent=2)+'\n')
        print(label,'candidate',rank,'k',k,'d',doc['distance']['d'],'w',w,'passed',verdict['passed'],flush=True)
        passed+=int(verdict['passed'])
    return passed

if __name__=='__main__':
    total=run([3,12,60],100000,500,20260816,'k150')
    total+=run([12,12,20,20],100000,500,20261816,'k128')
    print('PASSED',total)
