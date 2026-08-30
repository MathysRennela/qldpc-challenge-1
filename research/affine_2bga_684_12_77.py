"""Reproducible generator for the submitted affine 2BGA candidate.

The code is the two-block CSS construction H_X=[L(a)|R(b)] and
H_Z=[R(b)^T|L(a)^T] over Aff(F_19)=C_19 semidirect C_18, with the
non-abelian action r=2.  The element index is (x exponent)*18 + (y exponent),
matching research/kit/group_algebra.metacyclic.
"""
from __future__ import annotations

import numpy as np
from group_algebra import L_rep, R_rep, metacyclic

GROUP = (19, 18, 2)
A = (182, 323, 322, 217)
B = (176, 208, 142, 68)


def build():
    """Return (H_X, H_Z) as dense int8 GF(2) arrays."""
    ell1, ell2, q = GROUP
    mul, _ = metacyclic(ell1, ell2, q)
    left = np.bitwise_xor.reduce(
        np.asarray([L_rep(mul, g) for g in A], dtype=np.int8), axis=0)
    right = np.bitwise_xor.reduce(
        np.asarray([R_rep(mul, g) for g in B], dtype=np.int8), axis=0)
    return (np.hstack((left, right)).astype(np.int8),
            np.hstack((right.T, left.T)).astype(np.int8))


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "verify")
    from gf2 import rank
    HX, HZ = build()
    print({"n": HX.shape[1], "k": HX.shape[1] - rank(HX) - rank(HZ),
           "max_check_weight": int(max(HX.sum(1).max(), HZ.sum(1).max()))})
