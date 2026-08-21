"""Quantum Tanner (QT) codes via the lifting construction.

Implements the "lifted QT code" construction of Leverrier-Rozendaal-Zemor
(arXiv:2512.20532) as used by Mian et al., "Quantum Tanner Codes at Moderate
Blocklength" (arXiv:2608.12509), Eq. (34).

The construction starts from a *base* CSS code on an nA x nB grid of qubits,
defined by two pairs of classical codes C0, C1 <= F2^{nA} and C0', C1' <= F2^{nB}
with parity-check matrices H0, H1 and generator matrices G0, G1 (resp. primed).
The base code is then *lifted* through commuting left/right actions of a finite
group G: each base qubit (i, j) becomes a fiber of |G| qubits indexed by
g in G, and the parity checks become block matrices built from the left- and
right-regular representations of G.

The lifted parity checks are (arXiv:2608.12509, Eq. 34):

    HX^lifted = [ H0 (x) G0' (x) I
                  (H1 (x) G1' (x) I) LA RB ]
    HZ^lifted = [ (G0 (x) H1' (x) I) RB
                  (G1 (x) H0' (x) I) LA ]

where LA and RB are block-diagonal permutation matrices encoding the left action
of the multiset A and the right action of the multiset B, and the column
permutations pi_A, pi_B relate H1 to H0 and H1' to H0'.

The qubit array is the 3D grid (i, j, g) with i in [0,nA), j in [0,nB),
g in [0,|G|); the full qubit index is ((i*nB + j)*N + g). Per Appendix D of the
paper, LA = blockdiag over (i,j) of lambda_{a_i} and RB = blockdiag over (i,j)
of rho_{b_j}, where lambda_a and rho_b are the left- and right-regular-rep
permutation matrices of the group element.

The construction is CSS by construction (left and right regular actions
commute); we still assert it numerically.
"""

import numpy as np

from css import compute_k, verify_css
from group_algebra import L_rep, R_rep


def _k3(A, B, C):
    """Kronecker product A (x) B (x) C as a numpy array."""
    return np.kron(np.kron(A, B), C)


def _blockdiag_LA(mul, A, nB):
    """LA = blockdiag over (i,j) of lambda_{a_i}, shape (nA*nB*N)^2."""
    N = mul.shape[0]
    nA = len(A)
    total = nA * nB * N
    LA = np.zeros((total, total), dtype=np.int8)
    for i in range(nA):
        lam = L_rep(mul, A[i])
        for j in range(nB):
            r0 = (i * nB + j) * N
            LA[r0:r0+N, r0:r0+N] = lam
    return LA


def _action_blocks_RB(mul, B, nA):
    """RB = blockdiag over (i,j) of rho_{b_j}, shape (nA*nB*N)^2."""
    N = mul.shape[0]
    nB = len(B)
    total = nA * nB * N
    RB = np.zeros((total, total), dtype=np.int8)
    for i in range(nA):
        for j in range(nB):
            rho = R_rep(mul, B[j])
            r0 = (i * nB + j) * N
            RB[r0:r0+N, r0:r0+N] = rho
    return RB


def build_qt_lift(mul, A, B, H0, G0, H0p, G0p, pi_A=None, pi_B=None,
                  check_css=True):
    """Build a lifted QT code.

    Parameters
    ----------
    mul : (N, N) int array
        Cayley table of the group G (identity at index 0).
    A, B : list of int
        Multisets of element indices of G (length nA and nB respectively).
    H0, G0 : (m, nA) / (kA, nA) int arrays
        Parity-check and generator matrices of the A-side base code.
    H0p, G0p : (m', nB) / (kB, nB) int arrays
        Same for the B-side base code.
    pi_A, pi_B : list of int, optional
        Column permutations relating H1 to H0 (resp. H1' to H0'). Defaults to
        the identity permutation.
    check_css : bool
        If True (default), assert CSS commutation before returning.

    Returns
    -------
    (HX, HZ) : (num_checks, n) int8 arrays
    """
    N = mul.shape[0]
    nA, nB = len(A), len(B)
    n = nA * nB * N

    if pi_A is None:
        pi_A = list(range(nA))
    if pi_B is None:
        pi_B = list(range(nB))
    assert sorted(pi_A) == list(range(nA)), "pi_A not a permutation of 0..nA-1"
    assert sorted(pi_B) == list(range(nB)), "pi_B not a permutation of 0..nB-1"

    # Derived local codes via the column permutations
    H1 = H0[:, pi_A]
    G1 = G0[:, pi_A]
    H1p = H0p[:, pi_B]
    G1p = G0p[:, pi_B]

    LA = _action_blocks(mul, A, nB, side="L")
    RB = _action_blocks(mul, B, nA, side="R")

    I = np.eye(N, dtype=np.int8)

    # HX = [ H0 x G0' x I ; (H1 x G1' x I) LA RB ]
    HX_top = _k3(H0, G0p, I)
    HX_bot = _k3(H1, G1p, I) @ (LA @ RB)
    HX = np.vstack([HX_top, HX_bot])

    # HZ = [ (G0 x H1' x I) RB ; (G1 x H0' x I) LA ]
    HZ_top = _k3(G0, H1p, I) @ RB
    HZ_bot = _k3(G1, H0p, I) @ LA
    HZ = np.vstack([HZ_top, HZ_bot])

    HX = np.asarray(HX, dtype=np.int8) % 2
    HZ = np.asarray(HZ, dtype=np.int8) % 2
    assert HX.shape[1] == n and HZ.shape[1] == n, "n mismatch"
    if check_css:
        assert verify_css(HX, HZ), "CSS commutation failed"
    return HX, HZ


def _action_blocks(mul, multiset, other_dim, side):
    """Block-diagonal action matrix over the (i,j) grid.

    The qubit index is ((i*nB + j)*N + g): i is the outer (A-side) index,
    j the inner (B-side) index.  So
      side='L': block (i,j) = lambda_{a_i}  (left-regular rep of A[i]);
      side='R': block (i,j) = rho_{b_j}     (right-regular rep of B[j]).
    """
    N = mul.shape[0]
    if side == "L":
        nA, nB = len(multiset), other_dim
        total = nA * nB * N
        M = np.zeros((total, total), dtype=np.int8)
        for i in range(nA):
            rep = L_rep(mul, multiset[i])
            for j in range(nB):
                r0 = (i * nB + j) * N
                M[r0:r0+N, r0:r0+N] = rep
        return M
    else:
        nA, nB = other_dim, len(multiset)
        total = nA * nB * N
        M = np.zeros((total, total), dtype=np.int8)
        for i in range(nA):
            for j in range(nB):
                rep = R_rep(mul, multiset[j])
                r0 = (i * nB + j) * N
                M[r0:r0+N, r0:r0+N] = rep
        return M


# ---------------------------------------------------------------------------
#  Local codes the paper found most effective
# ---------------------------------------------------------------------------
def hamming_8_4_4():
    """Parity-check matrix of the [8,4,4] extended Hamming code."""
    return np.array([
        [1, 0, 0, 0, 1, 1, 0, 1],
        [0, 1, 0, 0, 1, 0, 1, 1],
        [0, 0, 1, 0, 1, 1, 1, 0],
        [0, 0, 0, 1, 0, 1, 1, 1],
    ], dtype=np.int8)


def hamming_7_3_4():
    """Parity-check matrix of the [7,3,4] simplex code."""
    return np.array([
        [1, 0, 0, 0, 1, 1, 1],
        [0, 1, 0, 1, 0, 1, 1],
        [0, 0, 1, 1, 1, 0, 1],
    ], dtype=np.int8)


def hamming_6_3_3():
    """Parity-check matrix of the [6,3,3] code (shortened Hamming)."""
    return np.array([
        [1, 0, 0, 0, 1, 1],
        [0, 1, 0, 1, 0, 1],
        [0, 0, 1, 1, 1, 0],
    ], dtype=np.int8)


def generator_from_parity(H):
    """A generator matrix G with G H^T = 0 mod 2 (a basis of ker(H))."""
    from css import kernel_basis
    return kernel_basis(np.asarray(H, dtype=np.int8) % 2)


if __name__ == "__main__":
    from group_algebra import cyclic_product

    # Sanity check: reproduce the paper's Appendix D [[8,2,2]] example.
    # G = C2, nA = nB = 2, all local codes = [1 1] repetition.
    mul2, _ = cyclic_product(2)
    rep = np.array([[1, 1]], dtype=np.int8)
    A = [0, 1]
    B = [0, 1]
    HX, HZ = build_qt_lift(mul2, A, B, rep, rep, rep, rep)
    n = HX.shape[1]
    k = compute_k(HX, HZ)
    print(f"Appendix D check: n={n} k={k} css={verify_css(HX, HZ)} "
          f"(paper says [[8,2,2]])")