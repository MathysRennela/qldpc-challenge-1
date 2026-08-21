#!/usr/bin/env python3
from __future__ import annotations
import json, random, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'research/kit'),str(ROOT/'verify')]
from group_algebra import build_2bga, cyclic_product
from css import compute_k
N=333

def main():
 d=json.loads((ROOT/'research/candidates/mutated-666-150-95-67275d626f0a1342.json').read_text())
 x=d['checks']['X'][0]; a=tuple(i for i in x if i<N); b=tuple(i-N for i in x if i>=N)
 mul,_=cyclic_product(N); rng=random.Random(20260818)
 vals=[]
 def add(aa,bb,label):
  if not 25<=len(aa)+len(bb)<=29:return
  hx,hz=build_2bga(mul,aa,bb); k=compute_k(hx,hz); vals.append((k,len(aa)+len(bb),aa,bb,label))
 for side,base,other in [('a',a,b),('b',b,a)]:
  for old in base:
   for new in range(N):
    if new in base: continue
    v=tuple(sorted((set(base)-{old})|{new})); add(v,other,'swap') if side=='a' else add(other,v,'swap')
 for ia in range(len(a)):
  for ib in range(len(b)):
   add(a[:ia]+a[ia+1:],b[:ib]+b[ib+1:],'remove2')
 # random swaps/removals/additions, retaining support close to seed
 for _ in range(1500):
  aa=set(a);bb=set(b)
  for _ in range(rng.randrange(1,4)):
   if rng.random()<.5 and aa: aa.remove(rng.choice(tuple(aa)))
   elif len(aa)<18: aa.add(rng.randrange(N))
  for _ in range(rng.randrange(1,4)):
   if rng.random()<.5 and bb: bb.remove(rng.choice(tuple(bb)))
   elif len(bb)<18: bb.add(rng.randrange(N))
  add(tuple(sorted(aa)),tuple(sorted(bb)),'random')
 vals.sort(reverse=True,key=lambda z:z[0])
 print('tested',len(vals),'best:')
 for k,w,aa,bb,label in vals[:30]: print(k,w,len(aa),len(bb),label,list(aa),list(bb))

if __name__=='__main__':main()
