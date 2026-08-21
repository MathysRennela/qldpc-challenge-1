import random, sys
from pathlib import Path
import numpy as np
from sympy import Poly,gcd,symbols
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'research'/'kit'))
from css import kernel_basis
N=337
A0=(0,1,12,24,27,69,93,113,128,143,149,162,262,269,294,309)
def circ(s):
 H=np.zeros((N,N),dtype=np.int8)
 for i in range(N): H[i,[(i+x)%N for x in s]]=1
 return H
def main():
 x=symbols('x');p=Poly(x**N+1,x,modulus=2);g=gcd(p,Poly(sum(x**i for i in A0),x,modulus=2));gs=tuple(i for i,b in enumerate(g.all_coeffs()[::-1]) if int(b)&1);H=kernel_basis(circ(gs))
 rng=random.Random(20260816); blocks=[list(range(i*84,min((i+1)*84,N))) for i in range(4)]
 found=set(); samples=250000
 for rep in range(4):
  left={};right={}
  for _ in range(samples):
   s=tuple(sorted(rng.sample(blocks[0],4))); v=np.zeros(N,dtype=np.int8);v[list(s)]=1; syn=tuple((H@v)%2);left.setdefault(syn,s)
   s=tuple(sorted(rng.sample(blocks[1],4))); v=np.zeros(N,dtype=np.int8);v[list(s)]=1; syn=tuple((H@v)%2);right.setdefault(syn,s)
  for key,s1 in left.items():
   if key in right:
    c=tuple(sorted(s1+right[key]));
    if len(set(c))==8 and not np.any((H[:,c].sum(axis=1)%2)):found.add(c)
  print('round',rep,'tables',len(left),len(right),'found8',len(found),flush=True)
 print('done found',len(found),flush=True)
if __name__=='__main__':main()
