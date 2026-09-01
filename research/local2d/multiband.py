#!/usr/bin/env python
"""Generalized multi-band dense-packing builder (manifold-mapping tool).

Reconstructs the raised-pitch multi-band family on the board
([[126,6,5]] .. [[676,36,5]], [[418,10,7]], [[615,15,7]], [[666,10,9]],
[[398,54,3]], [[570,78,3]], ...) as rows x m x pitch, generalizing
research/build_dense_surface.py (the rows=2, pitch=d-1, m=3 case).

Mask rule (per band r at y0 = r*pitch, patch centers x0 = j*Px (even r)
or d+1 + j*Px (odd r), Px = 2d+2), occupancy is the UNION over bands of:
  1. window interiors [x0+1, x0+2d-1] x [y0+1, y0+2d-1] with (x+y) % 2 == 0
  2. vertical edge columns {x0, x0+2d} x rows [y0+2, y0+2d-2]
     with (x+y) % 4 == (0 if r even else 2)
  3. horizontal edge rows {y0, y0+2d} x columns [x0+2, x0+2d-1]
     with (x+y) % 4 == (2 if r even else 0)
Data qubits: odd/odd sites. Ancillas: (x+y) % 4 == 2 -> X-check (HX row),
else Z-check (HZ row); support = the diagonal data neighbours present.

Validation: validate() must reproduce build_dense_surface.build bit-exactly
at (d=5, rows=2, m=3, pitch=4) and the (n, k) of every board member of the
family before anything downstream is trusted.
"""
import numpy as np


def multiband_mask(d, rows, m, pitch):
    Px = 2 * d + 2
    sites = set()
    for r in range(rows):
        y0 = r * pitch
        if r % 2 == 0:
            xs = [j * Px for j in range(m)]
        else:
            xs = [d + 1 + j * Px for j in range(m - 1)]
        phase_v = 0 if r % 2 == 0 else 2
        phase_h = 2 if r % 2 == 0 else 0
        for x0 in xs:
            for y in range(y0 + 1, y0 + 2 * d):
                for x in range(x0 + 1, x0 + 2 * d):
                    if (x + y) % 2 == 0:
                        sites.add((x, y))
            for x in (x0, x0 + 2 * d):
                for y in range(y0 + 2, y0 + 2 * d - 1):
                    if (x + y) % 4 == phase_v:
                        sites.add((x, y))
            for x in range(x0 + 2, x0 + 2 * d):
                for y in (y0, y0 + 2 * d):
                    if (x + y) % 4 == phase_h:
                        sites.add((x, y))
    return sites


def build_from_mask(sites):
    """Published conventions: data odd/odd, (x+y)%4==2 ancilla -> X-check."""
    data = sorted(s for s in sites if s[0] % 2 == 1 and s[1] % 2 == 1)
    d2i = {c: j for j, c in enumerate(data)}
    HXs, HZs = [], []
    for (x, y) in sorted(sites):
        if (x, y) in d2i:
            continue
        ns = sorted(d2i[(x + dx, y + dy)]
                    for dx, dy in ((-1, -1), (-1, 1), (1, -1), (1, 1))
                    if (x + dx, y + dy) in d2i)
        if (x + y) % 4 == 2:
            HXs.append(ns)
        else:
            HZs.append(ns)
    n = len(data)
    HX = np.zeros((len(HXs), n), dtype=np.int8)
    HZ = np.zeros((len(HZs), n), dtype=np.int8)
    for r, s in enumerate(HXs):
        HX[r, s] = 1
    for r, s in enumerate(HZs):
        HZ[r, s] = 1
    xy = np.array(data, dtype=float) / 2.0
    return HX, HZ, xy


def build(d, rows, m, pitch):
    return build_from_mask(multiband_mask(d, rows, m, pitch))


def gf2_rank(A):
    A = (A % 2).copy().astype(np.uint8)
    m_, c = A.shape
    r = 0
    for col in range(c):
        piv = np.nonzero(A[r:, col])[0]
        if len(piv) == 0:
            continue
        piv = piv[0] + r
        A[[r, piv]] = A[[piv, r]]
        for rr in range(m_):
            if rr != r and A[rr, col]:
                A[rr] ^= A[r]
        r += 1
        if r == m_:
            break
    return r


def code_stats(HX, HZ):
    n = HX.shape[1]
    css = not bool(((HX @ HZ.T) % 2).any())
    rx, rz = gf2_rank(HX), gf2_rank(HZ)
    k = n - rx - rz
    wmax = int(max(HX.sum(1).max(), HZ.sum(1).max())) if HX.size else 0
    wmin = int(min(HX.sum(1).min(), HZ.sum(1).min())) if HX.size else 0
    # Tanner components: qubits joined by sharing any check, either side
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for H in (HX, HZ):
        for row in H:
            idx = np.nonzero(row)[0]
            for q in idx[1:]:
                a, b = find(idx[0]), find(q)
                if a != b:
                    parent[a] = b
    comps = len({find(q) for q in range(n)})
    return dict(n=n, k=k, css=css, wmax=wmax, wmin=wmin, components=comps)


def expected_k(rows, m):
    return rows * m - rows // 2


def validate():
    """Bit-exact vs published builder + (n,k) vs every board member."""
    import sys
    sys.path.insert(0, "research")
    from build_dense_surface import build as pub_build

    ok = True
    # 1. bit-exact site match with the published rows=2/pitch=d-1 builder
    for d in (3, 5, 7):
        pub = pub_build(d)
        # published grid: offset = 6d+5 columns, 3d rows; extract its site set
        HXp, HZp, xyp, datap, allp = pub
        pub_sites = {(int(x * 2), int(y * 2)) for x, y in
                     (allp[q] for q in datap)}
        # published data coords are the odd/odd sites it lists; reconstruct
        # its full occupied set from its ancilla bookkeeping instead:
        # simpler: compare data coordinate sets and check supports.
        HX, HZ, xy = build(d, 2, 3, d - 1)
        same_data = {(int(x * 2), int(y * 2)) for x, y in xy} == pub_sites
        # check supports as data-coordinate frozensets
        coord_of_pub = {j: (int(allp[q][0]), int(allp[q][1]))
                        for j, q in enumerate(datap)}
        pub_checks = {frozenset(coord_of_pub[q] for q in np.nonzero(row)[0])
                      for row in HXp}
        pub_checks |= {frozenset(coord_of_pub[q] for q in np.nonzero(row)[0])
                       for row in HZp}
        my_checks = set()
        for row in HX:
            my_checks.add(frozenset((int(xy[i][0] * 2), int(xy[i][1] * 2))
                                    for i in np.nonzero(row)[0]))
        for row in HZ:
            my_checks.add(frozenset((int(xy[i][0] * 2), int(xy[i][1] * 2))
                                    for i in np.nonzero(row)[0]))
        match = same_data and pub_checks == my_checks
        print(f"d={d} rows=2 m=3 pitch=d-1: data_match={same_data} "
              f"checks_match={pub_checks == my_checks}")
        ok &= match

    # 2. (n, k) vs board members: (d, rows, m, pitch) -> (n, k)
    board = [
        (5, 2, 4, 4, 139, 7), (5, 2, 5, 4, 177, 9), (5, 2, 6, 4, 215, 11),
        (5, 2, 7, 4, 253, 13), (5, 2, 10, 4, 367, 19),
        (5, 4, 2, 6, 126, 6), (5, 3, 3, 6, 168, 8), (5, 4, 3, 6, 202, 10),
        (5, 4, 4, 6, 278, 14), (5, 8, 5, 6, 676, 36),
        (7, 4, 3, 10, 418, 10), (7, 6, 3, 10, 615, 15),
        (9, 4, 3, 12, 666, 10),
        (3, 12, 5, 4, 398, 54), (3, 12, 7, 4, 570, 78),
    ]
    for d, rows, m, p, n_exp, k_exp in board:
        HX, HZ, _ = build(d, rows, m, p)
        st = code_stats(HX, HZ)
        good = (st["n"] == n_exp and st["k"] == k_exp and st["css"]
                and st["wmax"] == 4 and st["components"] == 1
                and st["k"] == expected_k(rows, m))
        print(f"d={d} rows={rows} m={m} pitch={p}: got n={st['n']} k={st['k']} "
              f"css={st['css']} w=[{st['wmin']},{st['wmax']}] "
              f"comps={st['components']} expected ({n_exp},{k_exp}) "
              f"{'OK' if good else 'MISMATCH'}")
        ok &= good
    print("ALL VALIDATIONS PASSED" if ok else "VALIDATION FAILURES PRESENT")
    return ok


if __name__ == "__main__":
    validate()
