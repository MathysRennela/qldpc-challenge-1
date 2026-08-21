#!/usr/bin/env python3
"""Prange-style information-set search for low-weight words in the N=337 ideal."""
from __future__ import annotations
import itertools, random, sys
from pathlib import Path
import numpy as np
from sympy import Poly, gcd, symbols
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research'/'kit'))
from css import kernel_basis
from group_algebra import build_2bga, cyclic_product
from submit import make_submission, save_submission
from surrogate import distance_rand
from validate_candidate import validate_candidate
N=337
A0=(0,1,12,24,27,69,93,113,128,143,149,162,262,269,294,309)
B0=(17,36,38,50,64,79,81,82,83,144,145,247,291,325)
def circulant(s):
 H=np.zeros((N,N),dtype=np.int8)
 for i in range(N):
  H[i,list((i+x)%N for x in s)]=1
 return H
def solve(A,b):
 A=np.concatenate([A,b[:,None]],axis=1).astype(np.int8)
 r=0
 for c in range(A.shape[1]-1):
  q=np.flatnonzero(A[r:,c])
  if not len(q): continue
  q=r+q[0]; A[[r,q]]=A[[q,r]]
  nz=np.flatnonzero(A[:,c]); nz=nz[nz!=r]
  A[nz]^=A[r]
  r+=1
  if r==A.shape[0]: break
 if r<A.shape[0] or not np.all(A[r:,-1]==0): return None
 return A[:,-1]
def main():
 x=symbols('x'); p=Poly(x**N+1,x,modulus=2); pa=Poly(sum(x**i for i in A0),x,modulus=2); g=gcd(p,pa)
 gs=tuple(i for i,b in enumerate(g.all_coeffs()[::-1]) if int(b)&1)
 G=circulant(gs); H=kernel_basis(G); assert H.shape==(64,N)
 rng=random.Random(20260816); found=set(); attempts=0
 for trial in range(50000):
  I=sorted(rng.sample(range(N),64)); J=[j for j in range(N) if j not in I]
  A=H[:,I]
  if np.linalg.matrix_rank(A.astype(float))<64: continue
  # sample a low-weight pattern on the non-information coordinates
  t=rng.choice((4,5,6,7,8,9,10,11,12,13,14,15,16))
  eidx=rng.sample(J,t); rhs=(H[:,eidx].sum(axis=1)%2).astype(np.int8)
  ci=solve(A,rhs)
  if ci is None: continue
  c=np.zeros(N,dtype=np.int8); c[I]=ci; c[eidx]^=1; w=int(c.sum())
  attempts+=1
  if 0<w<=16:
   s=tuple(np.flatnonzero(c));
   if s in found: continue
   found.add(s); print('FOUND',w,s,flush=True)
 print('attempts',attempts,'found',len(found),flush=True)
 if len(found)<2:return
 mul,_=cyclic_product(N)
 for aa,bb in itertools.combinations_with_replacement(sorted(found),2):
  HX,HZ=build_2bga(mul,aa,bb); d=int(distance_rand(HX,HZ,trials=1000,seed=20260816)); print('PAIR',d,aa,bb,flush=True)
  if d<88:continue
  doc=make_submission(HX,HZ,name=f'[[674,128,d<={d}]] N337 ISD ideal',construction=f'N337 cyclic 2BGA from degree-64 ideal; Prange ISD low-weight ideal supports A={list(aa)}, B={list(bb)}.',authors=['@mathysrennela'],family='generalized-bicycle',confidence='upper_bound',trials=3000,seed=20260816)
  out=ROOT/'research'/'candidates';out.mkdir(exist_ok=True);stem=f'n337-isd-674-128-{doc["distance"]["d"]}';save_submission(doc,str(out/f'{stem}.json'));v=validate_candidate(doc,seed=20260816,refute=True);(out/f'{stem}.verdict.json').write_text(__import__('json').dumps(v,indent=2)+'\n');print(v,flush=True)
if __name__=='__main__':main()
