"""Abelian multicycle (AMC) CSS constructor.

AMC codes are the middle boundary maps of the Koszul complex over
F_2[Z_{l_1} x ... x Z_{l_t}].  A polynomial is represented by a list of
exponent tuples; repeated monomials cancel over F_2.

For t=3, the code has n = 3*N qubits (N=prod(orders)); for t=4, it has
n = 6*N qubits.  The two CSS checks are consecutive Koszul boundary maps,
so commutation is structural.  This follows the MultivariateMulticycle
convention used by QuantumClifford.jl, including positive cyclic shifts.
"""
from itertools import combinations, product

import numpy as np


def _xor_support(support, orders):
    """Normalize monomials modulo the group and cancel duplicate terms."""
    t = len(orders)
    if any(len(e) != t for e in support):
        raise ValueError("every exponent must have one coordinate per group factor")
    parity = set()
    for exponent in support:
        e = tuple(int(a) % order for a, order in zip(exponent, orders))
        if e in parity:
            parity.remove(e)
        else:
            parity.add(e)
    return tuple(sorted(parity))


def _tuples(orders):
    return list(product(*[range(order) for order in orders]))


def _circulant(orders, support, elements):
    """Matrix for multiplication by a group-algebra polynomial."""
    index = {element: i for i, element in enumerate(elements)}
    n = len(elements)
    matrix = np.zeros((n, n), dtype=np.int8)
    for col, element in enumerate(elements):
        for monomial in support:
            target = tuple((a + b) % order
                           for a, b, order in zip(element, monomial, orders))
            matrix[index[target], col] ^= 1
    return matrix


def _boundary(orders, circulants, degree):
    """Build d_degree: C_degree -> C_(degree-1) over GF(2)."""
    t = len(orders)
    elements = _tuples(orders)
    N = len(elements)
    source = list(combinations(range(t), degree))
    target = list(combinations(range(t), degree - 1))
    target_index = {subset: i for i, subset in enumerate(target)}
    matrix = np.zeros((len(target) * N, len(source) * N), dtype=np.int8)
    for source_index, subset in enumerate(source):
        for removed in subset:
            remaining = tuple(i for i in subset if i != removed)
            target_index_value = target_index[remaining]
            block = circulants[removed]
            row = target_index_value * N
            col = source_index * N
            matrix[row:row + N, col:col + N] ^= block
    return matrix


def build_amc(orders, polynomial_supports):
    """Return ``(HX, HZ)`` for an AMC3 or AMC4 construction.

    ``orders`` has length 3 or 4. ``polynomial_supports`` contains one
    exponent-support list per variable.  For example, ``[(1,)]`` in AMC4
    means the polynomial ``1 + w`` when the first group factor has order 14;
    callers should pass ``[(0,0,0,0), (1,0,0,0)]`` for the unambiguous form.
    """
    orders = tuple(int(order) for order in orders)
    t = len(orders)
    if t not in (3, 4):
        raise ValueError("AMC constructor currently supports AMC3 and AMC4")
    if len(polynomial_supports) != t:
        raise ValueError("one polynomial support is required per variable")
    elements = _tuples(orders)
    supports = [_xor_support(support, orders) for support in polynomial_supports]
    circulants = [_circulant(orders, support, elements) for support in supports]
    middle = t // 2
    if t == 3:
        # Qubits are C_1: H_X=d_2^T and H_Z=d_1.
        hx = _boundary(orders, circulants, 2).T
        hz = _boundary(orders, circulants, 1)
    else:
        # Qubits are C_2: H_X=d_2 and H_Z=d_3^T.
        hx = _boundary(orders, circulants, 2)
        hz = _boundary(orders, circulants, 3).T
    if hx.shape[1] != hz.shape[1]:
        raise AssertionError("CSS matrices must have the same qubit count")
    if np.any((hx @ hz.T) % 2):
        raise AssertionError("Koszul boundary maps do not commute")
    return hx, hz


def shortest_quotient_cycle(orders, exponents):
    """Smallest subset of non-identity exponent tuples summing to 0 mod orders.

    A cheap structural prefilter for the AMC families (may reject, never
    promote): a relation of size <= 2 means the support contains a monomial
    pair that cancels under translation, which is structurally degenerate and
    cannot yield a large distance.  Returns the smallest subset size, or None
    if no subset of size >= 2 sums to zero.  ``exponents`` is a flat list of
    exponent tuples (e.g. the union of the non-identity monomials of all
    Koszul polynomials).
    """
    orders = tuple(int(o) for o in orders)
    t = len(orders)
    exps = [tuple(int(x) % o for x, o in zip(e, orders)) for e in exponents]
    n = len(exps)
    for size in range(2, n + 1):
        for combo in combinations(range(n), size):
            acc = [0] * t
            for i in combo:
                for j in range(t):
                    acc[j] = (acc[j] + exps[i][j]) % orders[j]
            if not any(acc):
                return size
    return None


if __name__ == "__main__":
    from css import compute_k, verify_css

    # Lin et al., Abelian multicycle codes, Table I: [[84, 6, 7]].
    zero = (0, 0, 0, 0)
    hx, hz = build_amc(
        (14, 1, 1, 1),
        [[zero, (1, 0, 0, 0)],
         [zero, (2, 0, 0, 0)],
         [zero, (5, 0, 0, 0)],
         [zero, (6, 0, 0, 0)]],
    )
    assert verify_css(hx, hz)
    assert hx.shape == (56, 84) and hz.shape == (56, 84)
    assert compute_k(hx, hz) == 6
    # Prefilter self-check: two identical monomials close a size-2 relation;
    # two independent unit vectors in Z_3^2 have no relation of size 2.
    assert shortest_quotient_cycle((2, 2, 2), [(1, 0, 0), (1, 0, 0)]) == 2
    assert shortest_quotient_cycle((3, 3, 3), [(1, 0, 0), (0, 1, 0)]) is None
    print("AMC4 calibration: [[84,6,7]] parameters and CSS commutation pass")
    print("quotient-lattice prefilter self-check passes")
