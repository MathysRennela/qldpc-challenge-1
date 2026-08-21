"""Reconstruct the Lin--Pryadko database row [[64,18,8]].

Source: arXiv:2306.16400v1, Table 1, and the authors' public database
QEC-pages/2BGA-codes at commit 403d194c3f98f0cadc236aecbc4a8b6139ccf23c.

The database lists non-identity supports using 1-based GAP positions. This
script adds the identity and converts to the repository's zero-based Cayley
-table convention, then packages the witnesses under local ignored staging.
Requires GAP on PATH.
"""
import ast
import os
import subprocess
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "kit"))

from group_algebra import build_2bga  # noqa: E402
from submit import make_submission, save_submission  # noqa: E402

GROUP_ORDER = 32
GAP_GROUP_ID = 21
# 1-based GAP positions from the public database, excluding the identity.
A_DATABASE = [2, 3, 17]
B_DATABASE = [7, 22, 31]


def cayley_table():
    gap_source = """
 g:=SmallGroup(%d,%d); e:=Elements(g);
 Print("[");
 for i in [1..Length(e)] do
   Print("[");
   for j in [1..Length(e)] do
     Print(Position(e,e[i]*e[j])-1);
     if j<Length(e) then Print(","); fi;
   od;
   Print("]");
   if i<Length(e) then Print(","); fi;
 od;
 Print("]\\n");
 QUIT;
""" % (GROUP_ORDER, GAP_GROUP_ID)
    with tempfile.NamedTemporaryFile("w", suffix=".g", delete=False) as handle:
        handle.write(gap_source)
        path = handle.name
    try:
        result = subprocess.run(
            ["gap", "-q", path], check=True, capture_output=True, text=True
        )
    finally:
        os.unlink(path)
    return np.asarray(ast.literal_eval(result.stdout.strip()), dtype=np.int64)


def main():
    mul = cayley_table()
    # The paper/database positions are 1-based and omit the identity.
    a = [0] + [position - 1 for position in A_DATABASE]
    b = [0] + [position - 1 for position in B_DATABASE]
    hx, hz = build_2bga(mul, a, b)
    doc = make_submission(
        hx,
        hz,
        name="[[64,18,8]] 2BGA on SmallGroup(32,21)",
        construction=(
            "2BGA from Lin--Pryadko Table 1 / public database: GAP "
            "SmallGroup(32,21), a=1+g2+g3+g17, b=1+g7+g22+g31."
        ),
        authors=["@mathysrennela"],
        family="generalized-bicycle",
        references=[
            "arXiv:2306.16400v1",
            "https://github.com/QEC-pages/2BGA-codes",
        ],
        notes=(
            "Reconstructed from the authors' public database at commit "
            "403d194c3f98f0cadc236aecbc4a8b6139ccf23c; the paper reports "
            "exact d=8; this repository record is witness-backed upper_bound."
        ),
        confidence="upper_bound",
        trials=8000,
        seed=230616400,
    )
    output = os.path.join(HERE, "candidates", "64-18-8-arxiv-2306-16400.json")
    print("schema errors:", save_submission(doc, output) or "none")
    print("wrote:", output)
    print("parameters:", doc["n"], doc["k"], doc["distance"]["d"])


if __name__ == "__main__":
    main()
