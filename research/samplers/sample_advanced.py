import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kit"))
from group_algebra import dihedral, build_2bga, metacyclic

def sample_dihedral(num, m_range=(30, 80), weight=4, seed=0):
    """Sample Generalized Bicycles on Dihedral groups D_m.
    n = 2 * (2m) = 4m.
    """
    rng = np.random.default_rng(seed)
    for _ in range(num):
        m = int(rng.integers(m_range[0], m_range[1] + 1))
        order = 2 * m
        mul, elems = dihedral(m)
        
        # Pick random supports of size `weight`
        a = list(rng.choice(order, size=weight, replace=False))
        b = list(rng.choice(order, size=weight, replace=False))
        
        HX, HZ = build_2bga(mul, a, b)
        spec = {"family": "2bga-dihedral", "m": m, "a": [int(x) for x in a], "b": [int(x) for x in b]}
        yield (spec, HX, HZ)

def sample_metacyclic(num, order_range=(60, 160), weight=4, seed=0):
    """Sample Generalized Bicycles on Metacyclic groups."""
    rng = np.random.default_rng(seed)
    
    # Pre-generate valid (n, k, r) metacyclic parameters
    valid_params = []
    for n in range(5, 60):
        for k in range(2, 20):
            if order_range[0] <= n * k <= order_range[1]:
                for r in range(2, n):
                    if pow(r, k, n) == 1:
                        valid_params.append((n, k, r))
                        
    for _ in range(num):
        if not valid_params:
            break
        n, k, r = valid_params[rng.choice(len(valid_params))]
        order = n * k
        mul, elems = metacyclic(n, k, r)
        
        a = list(rng.choice(order, size=weight, replace=False))
        b = list(rng.choice(order, size=weight, replace=False))
        
        HX, HZ = build_2bga(mul, a, b)
        spec = {"family": "2bga-metacyclic", "n": int(n), "k_m": int(k), "r": int(r), 
                "a": [int(x) for x in a], "b": [int(x) for x in b]}
        yield (spec, HX, HZ)

if __name__ == "__main__":
    from search import screen, update_leaderboard, pareto_frontier
    print("Screening Dihedral codes...")
    d_recs = screen(sample_dihedral(200, weight=4, seed=42), min_k=6, min_d=6, trials=100)
    print("Screening Metacyclic codes...")
    m_recs = screen(sample_metacyclic(200, weight=4, seed=42), min_k=6, min_d=6, trials=100)
    
    all_recs = d_recs + m_recs
    all_recs = sorted(all_recs, key=lambda r: r["efficiency"], reverse=True)
    
    print("\nTop 5 Candidates by Efficiency:")
    for r in all_recs[:5]:
        print(f"  [[{r['n']},{r['k']},{r['d']}]]  eff={r['efficiency']:.3f} {r['spec']}")
        
    update_leaderboard("board_advanced.json", all_recs)
