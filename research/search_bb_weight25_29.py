#!/usr/bin/env python3
"""Search native bivariate-bicycle tori at raw check weights 25..29."""
from __future__ import annotations
import hashlib,json,random,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'research/kit'),str(ROOT/'verify')]
from bb import build_bb
from css import compute_k
from surrogate import distance_rand
from submit import make_submission
from validate_candidate import validate_candidate
OUT=ROOT/'research/candidates'

def main():
 rng=random.Random(20260818)
 records=[]; seen=set()
 for _ in range(1200):
  l=rng.randint(4,20); m=rng.randint(3,20); N=l*m
  w=rng.randint(25,29); na=rng.randint(max(3,w-18),min(18,w-3)); nb=w-na
  if na>N or nb>N: continue
  grid=[(i,j) for i in range(l) for j in range(m)]
  A=tuple(sorted(rng.sample(grid,na))); B=tuple(sorted(rng.sample(grid,nb)))
  HX,HZ=build_bb(l,m,A,B); k=compute_k(HX,HZ)
  if k>=4: records.append((k,w,l,m,A,B,HX,HZ))
 print('rank survivors',len(records),flush=True)
 records.sort(key=lambda z:(-z[0],z[2]*z[3]))
 for i,(k,w,l,m,A,B,HX,HZ) in enumerate(records[:100]):
  seed=20260818+i*1009
  d=distance_rand(HX,HZ,trials=1500,seed=seed,backend='auto',threads=8)
  n=2*l*m; eff=k*d*d/n
  print(f'[[{n},{k},{d}]] w={w} l={l} m={m} eff={eff:.3f}',flush=True)
  # Preserve promising candidates relative to the known w=25/28 bars.
  if (w==25 and not (n<=57 and k>=18 and d>=4)) or (w==28 and not (n<=73 and k>=37 and d>=6)):
   if w in (25,28): continue
  doc=make_submission(HX,HZ,name=f'[[{n},{k},d<=screen]] BB weight-{w}',construction=f'Bivariate bicycle on Z_{l} x Z_{m}; A={list(A)}, B={list(B)}.',authors=['@mathysrennela'],family='bivariate-bicycle',confidence='upper_bound',trials=1500,seed=seed)
  fp=hashlib.sha256(json.dumps(doc['checks'],sort_keys=True).encode()).hexdigest()[:16]
  stem=f'bb-weight{w}-{n}-{doc["k"]}-{doc["distance"]["d"]}-{fp}'
  (OUT/f'{stem}.json').write_text(json.dumps(doc,indent=2)+'\n')
  verdict=validate_candidate(doc,seed=seed+900000,refute=True)
  (OUT/f'{stem}.verdict.json').write_text(json.dumps(verdict,indent=2)+'\n')
  print('staged',stem,'passed=',verdict['passed'],'labels=',verdict['labels'],flush=True)
 print('search complete',flush=True)
if __name__=='__main__': main()
