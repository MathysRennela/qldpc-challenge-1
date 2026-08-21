"""Trivariate tricycle (TT) codes on ``G = Z_l x Z_m x Z_p``.

This is the trivariate construction of arXiv:2508.08191v2.  For three
permutation-polynomials A, B, and C in the group algebra of G, the CSS
matrices are

    H_X = [ A | B | C ]
    H_Z = [[ 0   C.T B.T ],
           [ C.T 0   A.T ],
           [ B.T A.T 0   ]].

All sums are over GF(2).  CSS commutation is automatic: the permutation
matrices are translations in the abelian group, and hence A, B, and C
commute pairwise.

Conventions
-----------
The group-algebra basis is ordered lexicographically as ``(i, j, k)`` with
flat index ``i * (m*p) + j*p + k``.  The cyclic shift is the same convention
as ``research/kit/bb.py``: ``S[r, (r+1) % order] = 1``.  Thus the monomial
``x**a * y**b * z**c`` is the permutation matrix with ones at

    P[row=(i,j,k), col=(i+a, j+b, k+c)].

Exponents may be any integers; they are reduced modulo the corresponding
cyclic order.  Repeated terms cancel, as they should for a polynomial over
GF(2).
"""

import numpy as np


def _validate_shape(l, m, p):
    """Return the group shape after checking that all orders are positive."""
    shape = (l, m, p)
    if any(not isinstance(order, (int, np.integer)) or order <= 0 for order in shape):
        raise ValueError("l, m, and p must be positive integers")
    return tuple(int(order) for order in shape)


def monomial_matrix(l, m, p, exponent):
    """Build the permutation matrix for one exponent triple.

    ``exponent`` is ``(a, b, c)`` and the result has shape
    ``(l*m*p, l*m*p)`` and dtype ``int8``.
    """
    shape = _validate_shape(l, m, p)
    try:
        exponent = tuple(exponent)
    except TypeError as exc:
        raise ValueError("exponent must be a length-3 iterable") from exc
    if len(exponent) != 3:
        raise ValueError("exponent must contain exactly three entries")
    if any(not isinstance(value, (int, np.integer)) for value in exponent):
        raise ValueError("exponent entries must be integers")

    size = int(np.prod(shape))
    coordinates = np.indices(shape, sparse=True)
    shifted = tuple(
        (coordinates[axis] + int(exponent[axis])) % shape[axis]
        for axis in range(3)
    )
    columns = np.ravel_multi_index(shifted, shape).ravel()
    rows = np.arange(size)

    matrix = np.zeros((size, size), dtype=np.int8)
    matrix[rows, columns] = 1
    return matrix


def permutation_polynomial(l, m, p, terms):
    """Build a GF(2) sum of monomials from a sequence of exponent triples."""
    shape = _validate_shape(l, m, p)
    matrix = np.zeros((int(np.prod(shape)), int(np.prod(shape))), dtype=np.int8)
    for exponent in terms:
        matrix ^= monomial_matrix(*shape, exponent)
    return matrix


# ``poly_matrix`` mirrors the helper name in ``bb.py`` and is convenient when
# switching a search between bivariate and trivariate constructors.
poly_matrix = permutation_polynomial


def build_tt(l, m, p, A_terms, B_terms, C_terms):
    """Build a TT CSS code on ``Z_l x Z_m x Z_p``.

    Parameters
    ----------
    l, m, p : int
        Orders of the three cyclic factors.
    A_terms, B_terms, C_terms : iterable of (a, b, c)
        Supports of the three permutation-polynomials.

    Returns
    -------
    HX, HZ : numpy.ndarray
        ``HX`` has shape ``(l*m*p, 3*l*m*p)`` and ``HZ`` has shape
        ``(3*l*m*p, 3*l*m*p)``.  Both arrays contain GF(2) entries as int8.
    """
    A = permutation_polynomial(l, m, p, A_terms)
    B = permutation_polynomial(l, m, p, B_terms)
    C = permutation_polynomial(l, m, p, C_terms)
    size = A.shape[0]
    zero = np.zeros((size, size), dtype=np.int8)

    HX = np.concatenate((A, B, C), axis=1).astype(np.int8)
    HZ = np.block(
        [
            [zero, C.T, B.T],
            [C.T, zero, A.T],
            [B.T, A.T, zero],
        ]
    ).astype(np.int8)
    return HX, HZ


if __name__ == "__main__":
    # A construction-level smoke test only; no distance search is performed.
    from css import verify_css

    HX, HZ = build_tt(
        2,
        3,
        2,
        A_terms=[(0, 0, 0), (1, 0, 0)],
        B_terms=[(0, 1, 0), (0, 0, 1)],
        C_terms=[(1, 1, 1), (0, 0, 0)],
    )
    group_size = 2 * 3 * 2
    assert HX.shape == (group_size, 3 * group_size)
    assert HZ.shape == (3 * group_size, 3 * group_size)
    assert verify_css(HX, HZ)
    print("TT smoke test passed")
