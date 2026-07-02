import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kit"))
from group_algebra import metacyclic, build_2bga

def is_prime(n):
    if n <= 1: return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

def primitive_root(q):
    if not is_prime(q):
        return None
    for r in range(2, q):
        if pow(r, q-1, q) == 1:
            # Check if order is exactly q-1
            is_primitive = True
            for k in range(1, q-1):
                if pow(r, k, q) == 1:
                    is_primitive = False
                    break
            if is_primitive:
                return r
    return None

def sample_kasai_affine(num, q_range=(7, 19), weight=4, seed=0):
    """Sample Generalized Bicycles on Affine groups Aff(F_q) for prime q.
    This mimics the structure in Kasai's Affine-Coset paper.
    The order of the group is N = q(q-1). The code block size is n = 2N.
    """
    rng = np.random.default_rng(seed)
    
    # Pre-generate affine groups
    affine_groups = []
    for q in range(q_range[0], q_range[1] + 1):
        if is_prime(q):
            r = primitive_root(q)
            if r is not None:
                affine_groups.append((q, q-1, r))
                
    for _ in range(num):
        if not affine_groups:
            break
        q, k, r = affine_groups[rng.choice(len(affine_groups))]
        order = q * k
        mul, elems = metacyclic(q, k, r)
        
        a = list(rng.choice(order, size=weight, replace=False))
        b = list(rng.choice(order, size=weight, replace=False))
        
        HX, HZ = build_2bga(mul, a, b)
        spec = {"family": "2bga-affine", "q": int(q), "a": [int(x) for x in a], "b": [int(x) for x in b]}
        yield (spec, HX, HZ)

if __name__ == "__main__":
    from search import screen, update_leaderboard
    print("Screening Kasai Affine codes...")
    # Using trials=150 to get a slightly better bound, will push higher later
    recs = screen(sample_kasai_affine(300, weight=4, seed=123), min_k=6, min_d=6, trials=150)
    
    print("\nTop 5 Affine Candidates by Efficiency:")
    for r in recs[:5]:
        print(f"  [[{r['n']},{r['k']},{r['d']}]]  eff={r['efficiency']:.3f} {r['spec']}")
        
    update_leaderboard("board_advanced.json", recs)
