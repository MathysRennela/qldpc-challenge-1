#!/usr/bin/env python3
"""Meet-in-the-middle sparse-multiple search in PR 580's degree-64 ideal."""
from __future__ import annotations
import itertools, json, random, sys
from pathlib import Path
from sympy import Poly, gcd, symbols
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research'/'kit'))
from css import compute_k
from group_algebra import build_2bga, cyclic_product
from submit import make_submission, save_submission
from surrogate import distance_rand
from validate_candidate import validate_candidate
N=337
A0=(0,1,12,24,27,69,93,113,128,143,149,162,262,269,294,309)
B0=(17,36,38,50,64,79,81,82,83,144,145,247,291,325)
def mask(s): return sum(1<<x for x in s)
def tup(m): return tuple(i for i in range(N) if m>>i&1)
def rot(m,s): return ((m<<s)|(m>>(N-s)))&((1<<N)-1) if s else m
def main():
 x=symbols('x'); p=Poly(x**N+1,x,modulus=2); pa=Poly(sum(x**i for i in A0),x,modulus=2)
 g= gcd(p,pa); gm=mask(tuple(i for i,b in enumerate(g.all_coeffs()[::-1]) if int(b)&1))
 print('degree',g.degree(),flush=True)
 shifts=[rot(gm,s) for s in range(N)]
 # First half of a weight-4 multiplier: XOR of two shifted copies.
 pairs=[(i,j,shifts[i]^shifts[j]) for i in range(N) for j in range(i+1,N)]
 rng=random.Random(20260816); sparse=set(); trials=0
 # Randomized MITM over the 56k x 56k implicit pair product.
 for _ in range(3000000):
  p1=rng.choice(pairs); p2=rng.choice(pairs)
  if p1[0]==p2[0] or p1[0]==p2[1] or p1[1]==p2[0] or p1[1]==p2[1]: continue
  out=p1[2]^p2[2]; trials+=1
  w=out.bit_count()
  if 0<w<=16:
   sparse.add(out)
 print('mitm trials',trials,'sparse',len(sparse),flush=True)
 # Include known seed only as a duplicate guard, never as a result.
 sparse.discard(mask(A0)); sparse.discard(mask(B0))
 supports=[tup(m) for m in sparse]
 if len(supports)<2:
  print('no pairable sparse outputs',flush=True); return
 mul,_=cyclic_product(N); seen=set(); accepted=[]
 rng.shuffle(supports)
 for aa,bb in itertools.combinations_with_replacement(supports,2):
  if (aa,bb) in seen: continue
  seen.add((aa,bb)); HX,HZ=build_2bga(mul,aa,bb); k=compute_k(HX,HZ)
  if k!=128: continue
  d=int(distance_rand(HX,HZ,trials=500,seed=20260816+len(accepted)))
  accepted.append((d,aa,bb)); print('candidate',d,len(aa),len(bb),flush=True)
  if d<88: continue
  doc=make_submission(HX,HZ,name=f'[[674,128,d<={d}]] N337 MITM ideal',construction=f'Z_337 cyclic 2BGA from a degree-64 common divisor; meet-in-the-middle four-shift multiplier search; A={list(aa)}, B={list(bb)}.',authors=['@mathysrennela'],family='generalized-bicycle',confidence='upper_bound',trials=3000,seed=20260816)
  out=ROOT/'research'/'candidates'; out.mkdir(exist_ok=True); stem=f'n337-mitm-674-128-{doc["distance"]["d"]}'; save_submission(doc,str(out/f'{stem}.json'))
  verdict=validate_candidate(doc,seed=20260816+len(accepted),refute=True); (out/f'{stem}.verdict.json').write_text(json.dumps(verdict,indent=2)+'\n'); print('VALIDATED',verdict,flush=True)
 print('accepted',len(accepted),'best',max((x[0] for x in accepted),default=None),flush=True)
if __name__=='__main__': main()
