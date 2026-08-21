import itertools,random,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'research'/'kit'))
from group_algebra import build_2bga,cyclic_product
from css import compute_k
from surrogate import distance_rand
N=337
A=(0,1,12,24,27,69,93,113,128,143,149,162,262,269,294,309)
B=(17,36,38,50,64,79,81,82,83,144,145,247,291,325)
def m(s):return sum(1<<i for i in s)
def r(x,s):return ((x<<s)|(x>>(N-s)))&((1<<N)-1) if s else x
def main():
 rng=random.Random(20260816);ma,mb=m(A),m(B);pool=[r(ma,s) for s in range(N)]+[r(mb,s) for s in range(N)];seen=set();cand=[]
 for t in range(2000000):
  q=0
  for z in rng.sample(pool,rng.randint(2,12)):q^=z
  if q==ma or q==mb:continue
  w=q.bit_count()
  if 10<=w<=16 and q not in seen:seen.add(q);cand.append(tuple(i for i in range(N) if q>>i&1))
 print('supports',len(cand),flush=True)
 mul,_=cyclic_product(N);rng.shuffle(cand);best=0
 for aa,bb in itertools.islice(itertools.combinations_with_replacement(cand,2),10000):
  HX,HZ=build_2bga(mul,aa,bb)
  if compute_k(HX,HZ)!=128:continue
  d=int(distance_rand(HX,HZ,trials=300,seed=20260816+len(cand)));best=max(best,d)
  if d>=88:print('PROMISING',d,aa,bb,flush=True)
 print('best',best,flush=True)
if __name__=='__main__':main()
