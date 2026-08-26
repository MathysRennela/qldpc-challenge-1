"""One-shot SAT probe: build the punctured-RSC CNF, solve ONCE, decode.
No enumeration, no blocking clauses, no post-hoc rejection loops."""
import sys, os, time, itertools
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "kit"))
import numpy as np
from pysat.solvers import Cadical153

def board(Lx, Ly):
    qubits = [(i, j) for i in range(Lx + 1) for j in range(Ly + 1)]
    anchors = [(i + 0.5, j + 0.5) for i in range(Lx) for j in range(Ly)]
    return qubits, anchors

def anchor_support(a, qset):
    ax, ay = a
    return [qset[(int(ax)+dx, int(ay)+dy)] for dx in (0,1) for dy in (0,1)
            if (int(ax)+dx, int(ay)+dy) in qset]

def atmost(lits, bound, A, tag):
    m = len(lits); cls = []
    if bound < 0:
        return [[l] for l in lits]          # unsatisfiable
    if bound == 0:
        return [[-l] for l in lits]
    if bound >= m:
        return []
    s = [[A(("s", tag, i, j)) for j in range(bound)] for i in range(m)]
    c = []
    c.append([-lits[0], s[0][0]]); c.append([-s[0][0], lits[0]])
    for j in range(1, bound): c.append([-s[0][j]])
    for i in range(1, m):
        c.append([s[i][0], -lits[i]]); c.append([s[i][0], -s[i-1][0]])
        c.append([-s[i][0], lits[i], s[i-1][0]])
        for j in range(1, bound):
            c.append([s[i][j], -lits[i], -s[i-1][j-1]])
            c.append([s[i][j], -s[i-1][j]])
            c.append([-s[i][j], s[i-1][j], lits[i]])
            c.append([-s[i][j], s[i-1][j], s[i-1][j-1]])
        c.append([-lits[i], -s[i-1][bound-1]])
    cls.extend(c)
    return cls

def atleast(lits, k, A, tag):
    if k <= 0: return []
    if k > len(lits): return [[l] for l in lits]  # UNSAT
    return atmost([-l for l in lits], len(lits)-k, A, tag)

def xor_chain(lits, A, tag):
    cls = []; prev = None
    for i, lit in enumerate(lits):
        cur = A((tag, i))
        if prev is None:
            cls += [[-cur, lit], [cur, -lit]]
        else:
            cls += [[-cur, prev, lit], [-cur, -prev, -lit],
                    [cur, -prev, lit], [cur, prev, -lit]]
        prev = cur
    return cls, prev

def main(Lx=4, Ly=4, t=2, min_present=None, timeout_s=60):
    qubits, anchors = board(Lx, Ly)
    n_max = len(qubits); qset = {p: i for i, p in enumerate(qubits)}
    aux = {}
    def A(n): return aux.setdefault(n, len(aux)+1)
    pres = {q: A(("pres", q)) for q in range(n_max)}
    sx = {a: A(("sx", a)) for a in anchors}
    sz = {a: A(("sz", a)) for a in anchors}
    sup = {a: anchor_support(a, qset) for a in anchors}
    # incidence = pres[q] & side[a]  (no truncation vars in v1 -- instead we
    # allow boundary checks to be weight-2/3 by DROPPING via a per-(a,q) var)
    drop_x = {(a, q): A(("drx", a, q)) for a in anchors for q in sup[a]}
    drop_z = {(a, q): A(("drz", a, q)) for a in anchors for q in sup[a]}
    inc_x = {(a, q): A(("ix", a, q)) for a in anchors for q in sup[a]}
    inc_z = {(a, q): A(("iz", a, q)) for a in anchors for q in sup[a]}
    cls = []

    # inc <-> side & !drop & pres
    for a in anchors:
        for q in sup[a]:
            ix, iz = inc_x[(a,q)], inc_z[(a,q)]
            cls += [[-ix, sx[a]], [-ix, -drop_x[(a,q)]], [-ix, pres[q]],
                    [ix, -sx[a], drop_x[(a,q)]]]
            cls += [[-iz, sz[a]], [-iz, -drop_z[(a,q)]], [-iz, pres[q]],
                    [iz, -sz[a], drop_z[(a,q)]]]
        # at most one side per anchor
        cls.append([-sx[a], -sz[a]])
        # weight >= 2 if check exists: block "all-but-one kept false"
        if len(sup[a]) >= 2:
            for q in sup[a]:
                cls.append([-sx[a]] + [inc_x[(a, r)] for r in sup[a] if r != q])
                cls.append([-sz[a]] + [inc_z[(a, r)] for r in sup[a] if r != q])

    # coverage: present -> some adjacent check exists (either side)
    for qi, p in enumerate(qubits):
        covers = []
        x0, y0 = int(p[0]), int(p[1])
        for a in ((x0-.5,y0-.5),(x0+.5,y0-.5),(x0-.5,y0+.5),(x0+.5,y0+.5)):
            if a in sx: covers += [sx[a], sz[a]]
        cls.append([-pres[qi]] + covers)

    # n >= min_present
    mp = min_present or 1
    cls += atleast(list(pres.values()), mp, A, ("n",))

    # commutation: opposite-side anchors sharing >=1 qubit need even overlap
    alist = list(anchors)
    for i in range(len(alist)):
        for j in range(i+1, len(alist)):
            a, b = alist[i], alist[j]
            shared = sorted(set(sup[a]) & set(sup[b]))
            if not shared: continue
            for sa, sb, inc_a, inc_b in ((sx[a], sz[b], inc_x, inc_z),
                                         (sz[a], sx[b], inc_z, inc_x)):
                lits = [inc_a[(a,q)] if False else A(("ov", sa, sb, q)) for q in shared]
                for idx, q in enumerate(shared):
                    ov = lits[idx]
                    ia, ib = inc_a[(a,q)], inc_b[(b,q)]
                    cls += [[-ov, ia], [-ov, ib],
                            [ov, -ia, -ib]]
                if len(lits) == 1:
                    cls.append([-lits[0]])
                else:
                    ch, out = xor_chain(lits, A, ("par", sa, sb))
                    cls += ch
                    cls.append([-out])

    # detection: error e supported on present qubits must be seen by some row
    errors = []
    for w in range(1, t+1):
        for support in itertools.combinations(range(n_max), w):
            for comps in itertools.product((1,2,3), repeat=w):
                xe = np.zeros(n_max, dtype=np.int8); ze = np.zeros(n_max, dtype=np.int8)
                for q, c in zip(support, comps):
                    if c in (1,3): xe[q]=1
                    if c in (2,3): ze[q]=1
                errors.append((xe, ze))
    print(f"errors to encode: {len(errors)}")
    t0 = time.time()
    for e_idx, (xe, ze) in enumerate(errors):
        support = [q for q in range(n_max) if xe[q] or ze[q]]
        dlits, zlits_all = [], []
        for a in alist:
            act = [q for q in sup[a] if ze[q]]
            if act:
                rl = []
                for q in act:
                    kv = A(("kvx", a, q, e_idx))
                    ia = inc_x[(a,q)]
                    cls += [[-kv, ia], [kv, -ia]]
                    rl.append(kv)
                out = rl[0] if len(rl)==1 else None
                if out is None:
                    ch, out = xor_chain(rl, A, ("px", a, e_idx)); cls += ch
                zlits_all.append(out)
            act = [q for q in sup[a] if xe[q]]
            if act:
                rl = []
                for q in act:
                    kv = A(("kvz", a, q, e_idx))
                    ia = inc_z[(a,q)]
                    cls += [[-kv, ia], [kv, -ia]]
                    rl.append(kv)
                out = rl[0] if len(rl)==1 else None
                if out is None:
                    ch, out = xor_chain(rl, A, ("pz", a, e_idx)); cls += ch
                zlits_all.append(out)
        # if any support qubit present -> OR of all row-parity lits
        if zlits_all:
            for q in support:
                cls.append([-pres[q]] + zlits_all)
        if time.time() - t0 > timeout_s:
            print("encoding timeout"); return

    s = Cadical153(bootstrap_with=cls)
    print(f"clauses={len(cls)} vars={len(aux)} solving...")
    t0 = time.time()
    r = s.solve()
    print(f"SAT={r} ({time.time()-t0:.1f}s)")
    if not r: return
    model = {abs(m): m > 0 for m in s.get_model()}
    present = [q for q in range(n_max) if model.get(pres[q], False)]
    remap = {q:i for i,q in enumerate(present)}
    HXr, HZr = [], []
    for a in alist:
        kx = [q for q in sup[a] if model.get(inc_x[(a,q)], False)]
        kz = [q for q in sup[a] if model.get(inc_z[(a,q)], False)]
        if len(kx) >= 2: HXr.append([remap[q] for q in kx])
        if len(kz) >= 2: HZr.append([remap[q] for q in kz])
    HX = np.zeros((len(HXr), len(present)), dtype=np.int8)
    HZ = np.zeros((len(HZr), len(present)), dtype=np.int8)
    for i,r_ in enumerate(HXr): HX[i, r_] = 1
    for i,r_ in enumerate(HZr): HZ[i, r_] = 1
    from css import verify_css, compute_k
    print(f"n={len(present)} rows X/Z={len(HXr)}/{len(HZr)} "
          f"css={verify_css(HX,HZ)} k={compute_k(HX,HZ)} "
          f"maxroww={max(HX.sum(1).max(), HZ.sum(1).max()) if len(HXr) and len(HZr) else 0}")
    # save for validation
    np.save("/tmp/probe_HX.npy", HX)
    np.save("/tmp/probe_HZ.npy", HZ)
    import json
    json.dump({"present": present,
               "coords": [qubits[q] for q in present]},
              open("/tmp/probe_meta.json", "w"))

if __name__ == "__main__":
    Lx = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    Ly = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    t = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    mp = int(sys.argv[4]) if len(sys.argv) > 4 else None
    main(Lx, Ly, t, mp)
