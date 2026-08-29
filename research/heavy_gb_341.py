"""Heavy-band generalized-bicycle search on Z_341 (n = 682).

The board's headline family is two-block circulant GB codes at n near 700 with
row weight in the 28-32 band: [[666,150,76]] (m = 333) and the current leader
[[674,170,76]] (m = 337, score 1456.85). Both campaigns mined m with a coarse
divisor grid (ord_m(2) = 36 and 21). This module mines m = 341 = 11 * 31,
which has ord_341(2) = 10: x^341 - 1 splits into 6 factors of degree 5 and
31 of degree 10 (plus x - 1), so divisor degrees exist at every multiple of 5
(and +1), and the divisor lattice has ~2^37 elements. That gives fine control
of k = 2 * deg gcd(a, b, x^341 - 1) in exactly the k = 170..220 region where
the score bar (beat 1456.85 at n = 682) drops from d >= 77 down to d >= 68.

Pipeline (each phase is a function; the CLI at the bottom drives them):
  factors_341()        GF(1024) algebra: the 38 irreducible factors, by coset
  probe(degrees)       fertility: which divisor degrees admit weight<=16 words
  mine(divisor)        collect light codewords of C_g via gf2_fast RIS
  build(a, b)          the GB pair HX = [A|B], HZ = [B^T|A^T]
  sweep(...)           divisors -> word pairs -> 4k screen, ranked
  ladder(...)          200k -> 2M -> 20M rungs with sound kill bars

Everything that judges a candidate is an upper-bound screen; the only gate
that decides anything is verify/validate_candidate.py, run in phase `stage`.
"""
import json
import os
import sys
import time
import itertools
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "kit"))
sys.path.insert(0, os.path.join(_HERE, "..", "verify"))

import gf2_fast
from css import compute_k, verify_css

M = 341
N = 2 * M
SCORE_BAR = 1456.85          # current board best kd^2/n ([[674,170,76]])
MAX_ROW_WEIGHT = 32          # schema cap on check weight = |a| + |b|
STAGE_DIR = os.path.join(_HERE, "candidates", "heavy341")


# ---------------------------------------------------------------- GF(1024)
_PRIM = (1 << 10) | (1 << 3) | 1      # x^10 + x^3 + 1, primitive


def _gf_mul(a, b):
    r = 0
    while b:
        if b & 1:
            r ^= a
        b >>= 1
        a <<= 1
        if a & (1 << 10):
            a ^= _PRIM
    return r


def cosets_mod_m():
    seen, out = set(), []
    for s in range(M):
        if s in seen:
            continue
        c, x = [], s
        while x not in c:
            c.append(x)
            x = (2 * x) % M
        seen.update(c)
        out.append(tuple(sorted(c)))
    return out


def factors_341():
    """The irreducible factors of x^341 - 1 over GF(2), keyed by coset.

    Returns a list of (coset, coeffs) with coeffs a GF(2) uint8 array,
    lowest degree first. Verified: the product of all factors is x^341 + 1.
    """
    # beta = alpha^3 has order 1023/3 = 341 in GF(1024)*
    alpha_pows = [1]
    for _ in range(1022):
        alpha_pows.append(_gf_mul(alpha_pows[-1], 2))
    beta = alpha_pows[3]
    beta_pows = [1]
    for _ in range(340):
        beta_pows.append(_gf_mul(beta_pows[-1], beta))
    out = []
    for coset in cosets_mod_m():
        poly = [1]                       # product of (x - beta^i), i in coset
        for i in coset:
            root = beta_pows[i]
            nxt = [0] * (len(poly) + 1)
            for j, c in enumerate(poly):
                nxt[j + 1] ^= c          # x * c
                nxt[j] ^= _gf_mul(root, c)
            poly = nxt
        assert all(c in (0, 1) for c in poly), "factor not over GF(2)"
        out.append((coset, np.array(poly, dtype=np.uint8)))
    prod = np.array([1], dtype=np.uint8)
    for _, f in out:
        prod = np.convolve(prod, f) % 2
    want = np.zeros(M + 1, dtype=np.uint8)
    want[0] = want[M] = 1
    assert np.array_equal(prod, want), "factor product != x^341 + 1"
    return out


def divisor_poly(factors, idxs):
    g = np.array([1], dtype=np.uint8)
    for i in idxs:
        g = np.convolve(g, factors[i][1]) % 2
    return g


# ------------------------------------------------------------- cyclic code
def circulant(support):
    A = np.zeros((M, M), dtype=np.int8)
    for i in range(M):
        for e in support:
            A[i, (i + e) % M] = 1
    return A


def parity_check_of_ideal(g):
    """Parity-check matrix of C_g = {c : g | c} (dim M - deg g)."""
    G = np.zeros((M, M), dtype=np.int8)
    for s in range(M):
        for j, c in enumerate(g):
            if c:
                G[s, (s + j) % M] = 1
    K = gf2_fast.kernel_basis(G)
    return np.asarray(K, dtype=np.int8)


_E11, _E31 = 155, 187      # CRT idempotents: q = 155 i + 187 j mod 341


def crt(i, j):
    return (_E11 * int(i) + _E31 * int(j)) % M


def rectangle_mask_rows(rng, rows=5):
    """L rows that exclude every subgroup-lift word but pass generic words.

    A 2x2 combinatorial rectangle {i1,i2} x {j1,j2} in Z_11 x Z_31 meets every
    mod-11 fiber and every mod-31 fiber an even number of times, so its inner
    product with any N_31- or N_11-lift (the norm-word subspace that caps
    distance) is 0; dem_rand_witness's L e != 0 then never returns those
    words. A generic light word overlaps some row oddly with fair probability,
    so stacking a few independent rectangle-sums keeps coverage high.
    Each row is the XOR of two random rectangles (weight <= 8).
    """
    L = np.zeros((rows, M), dtype=np.int8)
    for r in range(rows):
        for _ in range(2):
            i1, i2 = rng.choice(11, size=2, replace=False)
            j1, j2 = rng.choice(31, size=2, replace=False)
            for i in (i1, i2):
                for j in (j1, j2):
                    L[r, crt(i, j)] ^= 1
    return L


def _accept_word(Hg, w, supp, min_weight, max_weight, require_clean=True):
    if w is None or not (min_weight <= w <= max_weight):
        return None
    supp = tuple(sorted(int(q) for q in supp))
    v = np.zeros(M, dtype=np.int8)
    v[list(supp)] = 1
    if (Hg @ v % 2).any():
        raise RuntimeError("RIS returned a non-codeword")
    if require_clean and not word_is_clean(supp):
        return None
    return supp


def orbit_rep(supp):
    """Canonical representative of the cyclic-shift orbit of a support."""
    best = None
    supp = sorted(supp)
    for q0 in supp:
        cand = tuple(sorted((q - q0) % M for q in supp))
        if best is None or cand < best:
            best = cand
    return best


def _norm_ideal_rows():
    """Generator-matrix rows of the two norm-word ideals (the subgroup-lift
    subspace that both masks and exclusion must always avoid)."""
    n31 = [31 * i for i in range(11)]
    n11 = [11 * j for j in range(31)]
    return np.concatenate([circulant(n31), circulant(n11)], axis=0)


def mine_light_words(Hg, budget=500_000, per_call=25_000, min_weight=13,
                     max_weight=18, seed0=0, threads=14, mask_rows=6,
                     max_orbits=12):
    """Collect distinct clean codeword orbits of ker(Hg), light-first, with
    iterative ideal exclusion.

    A plain minimum-weight search keeps returning the ideal's lightest
    stratum, and the structure that makes words light also makes them share
    factors (observed: five weight-16 orbits of one deg-95 divisor all inside
    a common deg-141 subideal -- every pair screens at k=282, d<=12). So
    after each find the word's whole generated ideal joins an exclusion space
    E (seeded with the two norm-word ideals), and the L masks for
    gf2_fast.dem_rand_witness (min |e| with He=0, Le!=0) are drawn from
    E-perp: each mask row is orthogonal to everything in E, so already-found
    strata can never be returned again, while a generic new word passes some
    row with probability 1 - 2^-mask_rows. Successive finds are therefore
    structurally independent, which is exactly what a GB pair needs
    (gcd close to the designed core, k = 2 deg gcd small).

    Every word is revalidated against Hg in numpy; dirty words (subgroup
    quotient ceilings) are dropped but still excluded from later probes.
    """
    rng = np.random.default_rng(seed0)
    E_rows = [_norm_ideal_rows()]
    orbits = {}
    spent = 0
    while spent < budget and len(orbits) < max_orbits:
        E = np.concatenate(E_rows, axis=0) % 2
        K = np.asarray(gf2_fast.kernel_basis(E.astype(np.int8)), dtype=np.int8)
        if K.shape[0] < mask_rows + 2:
            break                          # exclusion space nearly full
        L = np.zeros((mask_rows, M), dtype=np.int8)
        for r in range(mask_rows):
            picks = rng.integers(0, 2, size=K.shape[0]).astype(np.int8)
            if not picks.any():
                picks[rng.integers(K.shape[0])] = 1
            L[r] = picks @ K % 2
        w, supp = gf2_fast.dem_rand_witness(
            H=Hg, L=L, trials=int(per_call), seed=int(rng.integers(1 << 30)),
            pair_depth=24, threads=int(threads))
        spent += per_call
        if w is None:
            continue
        raw = tuple(sorted(int(q) for q in supp))
        if int(w) <= max_weight + 2:
            # exclude this word's whole generated ideal from later probes
            # (found or not, clean or junk): linear masks cannot exclude a
            # single shift-orbit, and re-finding any stratum is pure waste
            C = circulant(raw)
            E_rows.append(C)
            supp = _accept_word(Hg, w, raw, min_weight, max_weight)
            if supp is not None and orbit_rep(supp) not in orbits:
                gcd_deg = M - int(gf2_fast.gf2_rank(C.astype(np.int8)))
                orbits[orbit_rep(supp)] = (supp, gcd_deg)
    return sorted(orbits.values(), key=lambda t: len(t[0]), reverse=True)


# ----------------------------------------------------------------- GB code
def build_gb(a_supp, b_supp):
    A, B = circulant(a_supp), circulant(b_supp)
    HX = np.concatenate([A, B], axis=1).astype(np.int8)
    HZ = np.concatenate([B.T, A.T], axis=1).astype(np.int8)
    return HX, HZ


def needed_d(k, n=N, bar=SCORE_BAR):
    d = int(np.ceil(np.sqrt(bar * n / k)))
    while k * d * d / n <= bar:
        d += 1
    return d


def screen_pair(a_supp, b_supp, trials=4000, seed=0, threads=14):
    HX, HZ = build_gb(a_supp, b_supp)
    k = gf2_fast.compute_k(HX, HZ)
    if k <= 0:
        return k, None
    w, side, supp = gf2_fast.distance_rand_witness(
        HX, HZ, trials=int(trials), seed=int(seed), pair_depth=10,
        threads=int(threads))
    d = int(w) if int(w) <= N else None
    return k, d


def unstructured(supp, min_res11=5, min_res31=8):
    """Reject subgroup/product-structured words (e.g. the weight-11 norm word
    of the Z_31 subgroup, which lies in most divisor ideals and yields
    degenerate codes): a genuinely random light word spreads across many CRT
    residues mod 11 and mod 31."""
    r11 = len({q % 11 for q in supp})
    r31 = len({q % 31 for q in supp})
    return r11 >= min_res11 and r31 >= min_res31


# ------------------------------------------------- subgroup-quotient poison
# Z_341 has two proper subgroups, <31> ~ Z_11 and <11> ~ Z_31. For a GB pair
# a, b the vectors (u, 0) with a*u = 0 (and (0, v) with b*v = 0) live in
# ker H_X, and u can be built from the subgroup norm words:
#   u = N_31-lift of s in F2[Z_31] needs abar * s = 0, |u| = 11 |s|,
#   u = N_11-lift of s in F2[Z_11] needs atil * s = 0, |u| = 31 |s|,
# where abar/atil are a's projections to the quotient group rings. So a word
# whose projection has a large gcd with x^31 - 1 (resp. x^11 - 1) caps the
# code's distance at 11 (resp. 31) times the annihilator ideal's minimum
# weight. Keep gcd(abar, x^31-1) at degree <= 11 (two deg-5 factors + (x-1))
# and gcd(atil, x^11-1) at degree <= 1 and every such cap sits above ~110,
# safely over any score bar in play here. The same rule constrains divisor
# choice: never include the Z_11-quotient deg-10 factor (coset of multiples
# of 31), and include at most two of the six deg-5 factors.

def _proj_gcd_deg(supp, quot, sub_order):
    """Degree of gcd(projection of the word to F2[Z_quot], x^quot - 1).

    quot * sub_order = 341; the projection of q is q mod quot after CRT
    reindexing -- since <sub_order... the subgroup <quot>-cosets are indexed
    by residues mod quot when gcd(quot, sub_order) = 1, which holds here.
    """
    proj = np.zeros(quot, dtype=np.int8)
    for q in supp:
        proj[q % quot] ^= 1
    if not proj.any():
        return quot
    # gcd degree = quot - rank of the circulant of proj
    C = np.zeros((quot, quot), dtype=np.int8)
    for s in range(quot):
        for j in np.nonzero(proj)[0]:
            C[s, (s + int(j)) % quot] = 1
    return quot - int(gf2_fast.gf2_rank(C))


def word_is_clean(supp, max31=11, max11=1):
    """True iff the word's quotient projections leave no low subgroup ceiling."""
    return (_proj_gcd_deg(supp, 31, 11) <= max31 and
            _proj_gcd_deg(supp, 11, 31) <= max11)


# ------------------------------------------------------------------ phases
def classify_factors(factors):
    """Split the 38 factors into (x-1), the six deg-5 (Z_31-side), the one
    poisoned deg-10 (Phi_11, coset of multiples of 31), and the 30 free
    deg-10 factors."""
    one = deg5 = None
    deg5s, free10 = [], []
    poison10 = None
    for i, (coset, f) in enumerate(factors):
        deg = len(f) - 1
        if deg == 1:
            one = i
        elif deg == 5:
            deg5s.append(i)
        elif all(q % 31 == 0 for q in coset):
            poison10 = i
        else:
            free10.append(i)
    assert len(deg5s) == 6 and poison10 is not None and len(free10) == 30
    return one, deg5s, poison10, free10


def sample_clean_divisor(rng, deg, factors, parts):
    """A random divisor of x^341 - 1 of the given degree obeying the poison
    rules: only free deg-10 factors, at most two deg-5, optional (x - 1)."""
    one, deg5s, _, free10 = parts
    for n5 in rng.permutation(3):
        for eps in rng.permutation(2):
            rest = deg - 5 * int(n5) - int(eps)
            if rest % 10 == 0 and 0 <= rest // 10 <= len(free10):
                picks = list(rng.choice(free10, size=rest // 10, replace=False))
                picks += list(rng.choice(deg5s, size=int(n5), replace=False))
                if eps:
                    picks.append(one)
                return sorted(int(i) for i in picks)
    raise ValueError(f"degree {deg} unreachable under the poison rules")


def phase_probe(degrees=(85, 90, 95, 100), per_degree=12,
                budget=400_000, seed0=0, threads=14):
    """Fertility probe on clean divisors: how many clean band orbits found."""
    factors = factors_341()
    parts = classify_factors(factors)
    rng = np.random.default_rng(seed0)
    report = {}
    for D in degrees:
        rows = []
        for t in range(per_degree):
            picks = sample_clean_divisor(rng, D, factors, parts)
            g = divisor_poly(factors, picks)
            Hg = parity_check_of_ideal(g)
            words = mine_light_words(Hg, budget=budget,
                                     seed0=int(rng.integers(1 << 30)),
                                     threads=threads)
            rows.append((len(words), sorted(len(w) for w, _ in words), picks))
        report[D] = rows
        fertile = sum(1 for r in rows if r[0] >= 1)
        print(f"deg {D} (k>={2*D}, need d>={needed_d(2*D)}): "
              f"{fertile}/{len(rows)} divisors fertile; word weights "
              f"{[r[1] for r in rows if r[0]]}", flush=True)
    return report


def phase_sweep(core_deg=85, n_cores=8, ext_per_core=8,
                mine_budget=600_000, screen_trials=4000,
                seed0=1, threads=14, out=None):
    """Core-family search: mine a clean core divisor and its single-factor
    extensions, pool the words, screen every admissible pair.

    Any word of any extension ideal is a multiple of the core, so every pair
    across the family shares at least the core: k = 2 deg gcd(a, b, x^341-1)
    >= 2 * core_deg without needing two rare orbits in one ideal. Extra
    shared factors only raise k (and lower the score bar). Emits records
    {core, a, b, k, d4k, need, margin}, ranked by margin.
    """
    factors = factors_341()
    parts = classify_factors(factors)
    one, deg5s, _, free10 = parts
    rng = np.random.default_rng(seed0)
    records, seen_pairs = [], set()
    t_start = time.time()
    for c in range(n_cores):
        core = sample_clean_divisor(rng, core_deg, factors, parts)
        n5_core = sum(1 for i in core if i in deg5s)
        exts = [None]                       # the core itself
        ext_pool = [i for i in free10 if i not in core]
        if n5_core < 2:
            ext_pool += [i for i in deg5s if i not in core]
        if one not in core:
            ext_pool.append(one)
        exts += list(rng.permutation(ext_pool))[:ext_per_core]
        pool = {}                           # supp -> ext used (provenance)
        for ext in exts:
            picks = core if ext is None else sorted(core + [int(ext)])
            g = divisor_poly(factors, picks)
            Hg = parity_check_of_ideal(g)
            for wsupp, _gdeg in mine_light_words(
                    Hg, budget=mine_budget,
                    seed0=int(rng.integers(1 << 30)), threads=threads):
                pool.setdefault(wsupp, picks)
        print(f"[core {c}] deg {core_deg}: {len(pool)} pooled words "
              f"(weights {sorted(len(w) for w in pool)}) "
              f"{time.time()-t_start:.0f}s", flush=True)
        for a, b in itertools.combinations(sorted(pool, key=len, reverse=True), 2):
            if len(a) + len(b) > MAX_ROW_WEIGHT:
                continue
            key = (a, b)
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            k, d4k = screen_pair(a, b, trials=screen_trials,
                                 seed=int(rng.integers(1 << 30)),
                                 threads=threads)
            if d4k is None or k < 2 * core_deg:
                continue
            need = needed_d(k)
            rec = {"core": core, "a": list(a), "b": list(b), "k": int(k),
                   "d4k": int(d4k), "need": int(need),
                   "margin": int(d4k) - int(need),
                   "deg": core_deg, "factor_idxs": core}
            records.append(rec)
            print(f"  k={k} |a|={len(a)} |b|={len(b)} d4k<={d4k} "
                  f"need>={need} margin={rec['margin']:+d}", flush=True)
        records.sort(key=lambda r: -r["margin"])
        if out:
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out, "w") as fh:
                json.dump(records, fh, indent=1)
    print(f"[sweep] done: {len(records)} records, "
          f"{time.time()-t_start:.0f}s", flush=True)
    return records


def phase_harvest(probe_path, out=None, budget_per_ideal=400_000,
                  ext_per_divisor=6, screen_trials=4000, seed0=7,
                  threads=14, genuine_slack=12):
    """Mine each fertile probe divisor plus a few extensions with the
    exclusion miner; pool genuine words per family; screen every pair.

    A word is *genuine* when its own divisor degree is within genuine_slack
    of the family core (junk strata carry far more shared structure and
    screen at tiny d). Pairs obey the row-weight cap; k is recomputed
    exactly by the screen. Records go to `out`, ranked by margin.
    """
    factors = factors_341()
    parts = classify_factors(factors)
    one, deg5s, _, free10 = parts
    with open(probe_path) as fh:
        probe = json.load(fh)
    jobs = []
    for D, rows in sorted(probe.items(), key=lambda kv: int(kv[0])):
        for nwords, weights, picks in rows:
            light = sum(1 for w in weights if w <= 16)
            if nwords >= 1:
                jobs.append((int(D), light, nwords, picks))
    jobs.sort(key=lambda j: (-j[1], -j[2], -j[0]))
    rng = np.random.default_rng(seed0)
    records, t0 = [], time.time()
    for D, light, nwords, picks in jobs:
        n5 = sum(1 for i in picks if i in deg5s)
        ext_pool = [i for i in free10 if i not in picks]
        if n5 < 2:
            ext_pool += [i for i in deg5s if i not in picks]
        if one not in picks:
            ext_pool.append(one)
        ideals = [picks] + [sorted(picks + [int(e)]) for e in
                            list(rng.permutation(ext_pool))[:ext_per_divisor]]
        pool = {}
        for ideal_picks in ideals:
            g = divisor_poly(factors, ideal_picks)
            Hg = parity_check_of_ideal(g)
            for supp, gdeg in mine_light_words(
                    Hg, budget=budget_per_ideal,
                    seed0=int(rng.integers(1 << 30)), threads=threads):
                if gdeg <= D + genuine_slack:
                    pool.setdefault(orbit_rep(supp), (supp, gdeg))
        words = [supp for supp, _ in pool.values()]
        pairs = [(a, b) for a, b in itertools.combinations(words, 2)
                 if len(a) + len(b) <= MAX_ROW_WEIGHT]
        print(f"[deg {D}] {len(words)} genuine orbits "
              f"({sorted(len(w) for w in words)}), {len(pairs)} pairs "
              f"{time.time()-t0:.0f}s", flush=True)
        if out and pool:
            # the pool is the campaign's most expensive data: persist every
            # genuine orbit even when it pairs with nothing yet (a later
            # star-phase mine around it can still produce its partner)
            pool_path = out + ".pool.jsonl"
            with open(pool_path, "a") as fh:
                for supp, gdeg in pool.values():
                    fh.write(json.dumps({"deg": D, "factor_idxs": picks,
                                         "supp": list(supp),
                                         "gcd_deg": int(gdeg)}) + "\n")
        for a, b in pairs:
            k, d4k = screen_pair(a, b, trials=screen_trials,
                                 seed=int(rng.integers(1 << 30)),
                                 threads=threads)
            if d4k is None:
                continue
            need = needed_d(k)
            rec = {"deg": D, "factor_idxs": picks, "a": list(a), "b": list(b),
                   "k": int(k), "d4k": int(d4k), "need": int(need),
                   "margin": int(d4k) - int(need)}
            records.append(rec)
            print(f"  k={k} |a|={len(a)} |b|={len(b)} d4k<={d4k} "
                  f"need>={need} margin={rec['margin']:+d}", flush=True)
            records.sort(key=lambda r: -r["margin"])
            if out:
                os.makedirs(os.path.dirname(out), exist_ok=True)
                with open(out, "w") as fh:
                    json.dump(records, fh, indent=1)
    print(f"[harvest] {len(records)} records, {time.time()-t0:.0f}s",
          flush=True)
    return records


def word_factor_idxs(supp, factors, beta_pows=None):
    """Indices of the irreducible factors of x^341 - 1 dividing the word,
    by GF(1024) evaluation at one root per coset (cheap and exact)."""
    if beta_pows is None:
        alpha_pows = [1]
        for _ in range(1022):
            alpha_pows.append(_gf_mul(alpha_pows[-1], 2))
        beta = alpha_pows[3]
        beta_pows = [1]
        for _ in range(340):
            beta_pows.append(_gf_mul(beta_pows[-1], beta))
    out = []
    for i, (coset, f) in enumerate(factors):
        s = coset[0]
        acc = 0
        for q in supp:
            acc ^= beta_pows[(s * q) % M]
        if acc == 0:
            out.append(i)
    return out


def phase_trawl(n_divisors=60, deg=85, budget=600_000, star_budget=400_000,
                max_star_ideals=8, screen_trials=4000, seed0=11, threads=14,
                out=None):
    """The main funnel: trawl fresh clean deg-85 divisors for genuine
    weight<=16 orbits; around each hit, star-mine subset divisors of the
    hit's own gcd for partners; screen every admissible pair.

    Rationale (measured, see JOURNAL.md): genuine light words above deg ~87
    essentially do not exist under the row-weight cap, so the campaign lives
    at k = 170-172 and the kill bar is d >= 77; weight-16 orbits appear in
    a fraction of divisors and their <=16 partners are the scarce resource.
    A hit's gcd typically has degree 86-100, so its own subset divisors of
    degree >= 85 are fresh ideals whose every genuine word pairs with it.
    """
    factors = factors_341()
    parts = classify_factors(factors)
    rng = np.random.default_rng(seed0)
    # precompute beta powers once for factor membership
    alpha_pows = [1]
    for _ in range(1022):
        alpha_pows.append(_gf_mul(alpha_pows[-1], 2))
    beta = alpha_pows[3]
    beta_pows = [1]
    for _ in range(340):
        beta_pows.append(_gf_mul(beta_pows[-1], beta))

    pool = {}            # orbit_rep -> (supp, frozenset(factor idxs))
    records, seen_divisors = [], set()
    t0 = time.time()

    def note_word(supp):
        rep = orbit_rep(supp)
        if rep in pool:
            return False
        fidx = frozenset(word_factor_idxs(supp, factors, beta_pows))
        pool[rep] = (supp, fidx)
        if out:
            with open(out + ".pool.jsonl", "a") as fh:
                fh.write(json.dumps({"supp": list(supp),
                                     "factor_idxs": sorted(fidx)}) + "\n")
        return True

    def screen_new_pairs():
        fresh = []
        items = list(pool.values())
        degsum = {i: len(f) - 1 for i, (c, f) in enumerate(factors)}
        for (a, fa), (b, fb) in itertools.combinations(items, 2):
            if len(a) + len(b) > MAX_ROW_WEIGHT:
                continue
            shared = sum(degsum[i] for i in fa & fb)
            if shared < 85:
                continue
            key = tuple(sorted((a, b)))
            if key in seen_divisors:
                continue
            seen_divisors.add(key)
            k, d4k = screen_pair(a, b, trials=screen_trials,
                                 seed=int(rng.integers(1 << 30)),
                                 threads=threads)
            if d4k is None:
                continue
            need = needed_d(k)
            rec = {"a": list(a), "b": list(b), "k": int(k), "d4k": int(d4k),
                   "need": int(need), "margin": int(d4k) - int(need),
                   "deg": int(shared), "factor_idxs": sorted(fa & fb)}
            records.append(rec)
            fresh.append(rec)
            print(f"  PAIR k={k} |a|={len(a)} |b|={len(b)} d4k<={d4k} "
                  f"need>={need} margin={rec['margin']:+d}", flush=True)
        if fresh and out:
            records.sort(key=lambda r: -r["margin"])
            with open(out, "w") as fh:
                json.dump(records, fh, indent=1)
        return fresh

    degsum = {i: len(f) - 1 for i, (c, f) in enumerate(factors)}
    for it in range(n_divisors):
        picks = sample_clean_divisor(rng, deg, factors, parts)
        g = divisor_poly(factors, picks)
        Hg = parity_check_of_ideal(g)
        found = mine_light_words(Hg, budget=budget, min_weight=13,
                                 max_weight=16,
                                 seed0=int(rng.integers(1 << 30)),
                                 threads=threads)
        hits = []
        for supp, gdeg in found:
            if gdeg <= deg + 15 and note_word(supp):
                hits.append(supp)
        if hits:
            print(f"[trawl {it}] {len(hits)} genuine "
                  f"({[len(h) for h in hits]}) {time.time()-t0:.0f}s",
                  flush=True)
        # star-mine subset divisors of each hit's gcd for partners
        for w1 in hits:
            f1 = sorted(pool[orbit_rep(w1)][1])
            total = sum(degsum[i] for i in f1)
            subs = []
            for r in range(1, len(f1) + 1):
                for drop in itertools.combinations(f1, r):
                    if total - sum(degsum[i] for i in drop) >= 85:
                        subs.append([i for i in f1 if i not in drop])
                if len(subs) >= max_star_ideals:
                    break
            for S in subs[:max_star_ideals]:
                gS = divisor_poly(factors, S)
                HS = parity_check_of_ideal(gS)
                for supp, gdeg in mine_light_words(
                        HS, budget=star_budget, min_weight=13,
                        max_weight=MAX_ROW_WEIGHT - len(w1),
                        seed0=int(rng.integers(1 << 30)), threads=threads):
                    if gdeg <= sum(degsum[i] for i in S) + 15:
                        note_word(supp)
        screen_new_pairs()
    print(f"[trawl] {len(pool)} pooled words, {len(records)} pair records, "
          f"{time.time()-t0:.0f}s", flush=True)
    return records


def phase_ladder(records_path, out=None, threads=16,
                 rungs=((200_000, 2), (2_000_000, 0), (20_000_000, 0)),
                 top=20, salt=0):
    """Deepen the screen on the best sweep records with sound kill bars.

    Each rung is (trials, slack): a candidate is killed when its upper-bound
    reading drops below needed_d(k) + slack. Killing on a low reading is sound
    (every reading proves d <= reading); the slack on early rungs only prices
    in the observed 4k->20M deflation (~11 at 4k, ~4 at 200k, ~1 at 2M on the
    m=337 campaign). Survivors of all rungs are ready for phase `stage`.
    """
    with open(records_path) as fh:
        records = json.load(fh)
    records.sort(key=lambda r: -r["margin"])
    live = records[:top]
    for trials, slack in rungs:
        nxt = []
        for rec in live:
            HX, HZ = build_gb(rec["a"], rec["b"])
            seed = (hash((tuple(rec["a"]), tuple(rec["b"]), trials, salt))
                    & 0x7fffffff)
            t0 = time.time()
            w, side, supp = gf2_fast.distance_rand_witness(
                HX, HZ, trials=trials, seed=seed, pair_depth=10,
                threads=threads)
            d = int(w)
            rec.setdefault("ladder", {})[str(trials)] = d
            # a found low-weight logical is the campaign's most expensive
            # data -- keep the best witness with the record, never lose it
            if d <= N and d <= rec.get("witness", {}).get("weight", N + 1):
                rec["witness"] = {"weight": d, "side": str(side),
                                  "support": [int(q) for q in supp],
                                  "trials": int(trials), "seed": int(seed)}
            bar = rec["need"] + slack
            verdict = "keep" if d >= bar else "KILL"
            print(f"  [{trials:>8}] k={rec['k']} |a|={len(rec['a'])} "
                  f"|b|={len(rec['b'])} d<={d} (need {rec['need']}, "
                  f"bar {bar}) {verdict}  {time.time()-t0:.0f}s", flush=True)
            if d >= bar:
                rec["score_at_reading"] = rec["k"] * d * d / N
                nxt.append(rec)
            if out:
                with open(out, "w") as fh:
                    json.dump(records, fh, indent=1)
        live = nxt
        print(f"[ladder] rung {trials}: {len(live)} survive", flush=True)
        if not live:
            break
    return live


def phase_stage(records_path, index, authors, out_dir=STAGE_DIR,
                base_trials=1500, threads=16):
    """Package one ladder survivor via the kit path and run the trusted gate.

    Uses submit.make_submission (the kit path: schema assembly, CSS assert,
    baseline witness search), then upgrades both distance witnesses to the
    record's deep ladder witness: the family's block-swap + index-reversal
    symmetry maps an X-logical (u|v) to a Z-logical (rev(v)|rev(u)) of equal
    weight (verified per witness against the verifier's own criteria), so
    d_X = d_Z and one deep find covers both sides. Writes the submission
    JSON and the full validate_candidate verdict. Never touches codes/.
    """
    from submit import make_submission, save_submission
    from css import commutes, in_rowspace
    sys.path.insert(0, os.path.join(_HERE, "..", "verify"))
    from validate_candidate import validate_candidate
    with open(records_path) as fh:
        records = json.load(fh)
    rec = records[index]
    wit = rec.get("witness")
    if not wit:
        raise ValueError("record has no deep witness; run the ladder first")
    HX, HZ = build_gb(rec["a"], rec["b"])
    k = gf2_fast.compute_k(HX, HZ)
    doc = make_submission(
        HX, HZ,
        name=f"[[{N},{k},d<={wit['weight']}]] generalized-bicycle code",
        construction=(
            "Generalized bicycle on Z_341 = Z_11 x Z_31 (n = 2*341): "
            "H_X = [A|B], H_Z = [B^T|A^T] with circulant A, B built from "
            f"exponent supports a = {list(rec['a'])} (weight {len(rec['a'])}) "
            f"and b = {list(rec['b'])} (weight {len(rec['b'])}); row i of a "
            "circulant has a 1 in column (i + e) mod 341 for each exponent "
            "e. Both supports are codewords of a designed divisor ideal of "
            "x^341 - 1, mined by masked randomized-information-set search "
            "with subgroup-quotient cleanliness filters; "
            f"k = 2 deg gcd(a(x), b(x), x^341 - 1) = {k}."),
        authors=authors,
        family="generalized-bicycle",
        references=["arXiv:1904.02703"],
        confidence="upper_bound",
        trials=base_trials,
    )
    # upgrade to the deep ladder witness on both sides via the symmetry
    v = np.zeros(N, dtype=np.int8)
    v[wit["support"]] = 1
    u1, u2 = v[:M], v[M:]
    ridx = np.concatenate(([0], np.arange(M - 1, 0, -1)))
    z = np.concatenate([u2[ridx], u1[ridx]])
    x_vec, z_vec = (v, z) if wit["side"] == "X" else (z, v)
    assert commutes(x_vec, HZ) and not in_rowspace(x_vec, HX), "X witness"
    assert commutes(z_vec, HX) and not in_rowspace(z_vec, HZ), "Z witness"
    xwit = sorted(int(q) for q in np.where(x_vec)[0])
    zwit = sorted(int(q) for q in np.where(z_vec)[0])
    w = int(wit["weight"])
    assert len(xwit) == len(zwit) == w
    doc["distance"] = {
        "d": w,
        "X": {"value": w, "confidence": "upper_bound", "witness": xwit},
        "Z": {"value": w, "confidence": "upper_bound", "witness": zwit},
    }
    doc["provenance"]["notes"] = (
        "Witness-backed upper bound, not an exact-distance claim. Screening "
        "ladder (randomized information-set trials -> lightest logical): "
        + ", ".join(f"{t} -> d<={d}" for t, d in
                    sorted(rec.get("ladder", {}).items(), key=lambda kv: int(kv[0])))
        + f". Both witnesses have weight {w}: the family's block-swap plus "
        "index-reversal symmetry maps an X-logical to a Z-logical of equal "
        "weight, and both were revalidated independently against the "
        "verifier's criteria (in the correct kernel, outside the opposite "
        "stabilizer rowspace).")
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.join(out_dir, f"{N}-{k}-{w}")
    errs = save_submission(doc, base + ".json")
    if errs:
        raise RuntimeError(f"schema violations: {errs}")
    with open(base + ".json") as fh:
        verdict = validate_candidate(json.load(fh))
    with open(base + ".verdict.json", "w") as fh:
        json.dump(verdict, fh, indent=1, default=str)
    print(json.dumps({"passed": verdict.get("passed"),
                      "labels": verdict.get("labels"),
                      "file": base + ".json"}, indent=1, default=str))
    return verdict


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["selftest", "probe", "sweep", "harvest",
                                      "trawl", "ladder", "stage"])
    ap.add_argument("--out", default=None)
    ap.add_argument("--records", default=None)
    ap.add_argument("--probe", default=None)
    ap.add_argument("--index", type=int, default=0)
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--salt", type=int, default=0)
    ap.add_argument("--authors", default=None)
    args = ap.parse_args()
    if args.phase == "selftest":
        fs = factors_341()
        sizes = sorted(len(c) for c, _ in fs)
        print("factors:", len(fs), "coset sizes ok:",
              sizes.count(5) == 6 and sizes.count(10) == 31)
        # toy check of the light-word miner on a known ideal: g = x + 1
        g = np.array([1, 1], dtype=np.uint8)
        Hg = parity_check_of_ideal(g)
        words = mine_light_words(Hg, max_weight=4, seeds=range(2), trials=200)
        print("g=x+1 lightest words (expect weight 2):",
              [len(w) for w in words[:4]])
        # rebuild the m=337 champion and confirm k on our build path
        # (structure identical, only m differs)
        print("selftest done")
    elif args.phase == "probe":
        rep = phase_probe()
        if args.out:
            os.makedirs(os.path.dirname(args.out), exist_ok=True)
            with open(args.out, "w") as fh:
                json.dump({str(k): [[n, ws, [int(x) for x in p]]
                                    for n, ws, p in v]
                           for k, v in rep.items()}, fh)
            print("wrote", args.out)
    elif args.phase == "sweep":
        phase_sweep(out=args.out)
    elif args.phase == "harvest":
        phase_harvest(args.probe, out=args.out)
    elif args.phase == "trawl":
        phase_trawl(out=args.out)
    elif args.phase == "ladder":
        phase_ladder(args.records, out=args.out, top=args.top, salt=args.salt)
    elif args.phase == "stage":
        phase_stage(args.records, args.index,
                    [a.strip() for a in (args.authors or "").split(",") if a.strip()])
