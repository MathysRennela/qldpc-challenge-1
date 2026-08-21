"""Reconstruct high-value rows from the Lin--Pryadko 2BGA database.

Source: arXiv:2306.16400v1 and QEC-pages/2BGA-codes at commit
403d194c3f98f0cadc236aecbc4a8b6139ccf23c.

The database lists non-identity supports using 1-based GAP positions. This
script adds the identity, converts to zero-based Cayley-table indices, and
packages each candidate under local ignored staging.
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

ROWS = [
    {
        "n": 70,
        "k": 8,
        "d": 10,
        "order": 35,
        "group_id": 1,
        "a": [3, 9, 27],
        "b": [5, 26, 32],
        "weight": 8,
        "tag": "abelian",
    },
    {
        "n": 72,
        "k": 10,
        "d": 9,
        "order": 36,
        "group_id": 2,
        "a": [2, 3, 16],
        "b": [6, 17, 21],
        "weight": 8,
        "tag": "abelian",
    },
    {
        "n": 72,
        "k": 8,
        "d": 10,
        "order": 36,
        "group_id": 2,
        "a": [2, 3, 26],
        "b": [6, 8, 31],
        "weight": 8,
        "tag": "abelian",
    },
    {
        "n": 196,
        "k": 12,
        "d": 17,
        "order": 98,
        "group_id": 3,
        "a": [3, 14],
        "b": [9, 10, 59],
        "weight": 7,
        "tag": "non-abelian",
    },
]


def cayley_table(order, group_id):
    source = """
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
""" % (order, group_id)
    with tempfile.NamedTemporaryFile("w", suffix=".g", delete=False) as handle:
        handle.write(source)
        path = handle.name
    try:
        result = subprocess.run(
            ["gap", "-q", path], check=True, capture_output=True, text=True
        )
    finally:
        os.unlink(path)
    return np.asarray(ast.literal_eval(result.stdout.strip()), dtype=np.int64)


def main():
    for row in ROWS:
        mul = cayley_table(row["order"], row["group_id"])
        # Database positions are 1-based and omit the identity.
        a = [0] + [position - 1 for position in row["a"]]
        b = [0] + [position - 1 for position in row["b"]]
        hx, hz = build_2bga(mul, a, b)
        stem = f"{row['n']}-{row['k']}-{row['d']}"
        doc = make_submission(
            hx,
            hz,
            name=f"[[{row['n']},{row['k']},{row['d']}]] 2BGA on SmallGroup({row['order']},{row['group_id']})",
            construction=(
                "2BGA from Lin--Pryadko Table 1 / public database: GAP "
                f"SmallGroup({row['order']},{row['group_id']}), "
                "a=1+" + "+".join(f"g{x}" for x in row["a"]) + ", "
                "b=1+" + "+".join(f"g{x}" for x in row["b"]) + "."
            ),
            authors=["@mathysrennela"],
            family="generalized-bicycle",
            references=[
                "arXiv:2306.16400v1",
                "https://github.com/QEC-pages/2BGA-codes",
            ],
            notes=(
                "Reconstructed from the authors' public database at commit "
                "403d194c3f98f0cadc236aecbc4a8b6139ccf23c. The paper's exact "
                "distance claim is retained separately; this repository record "
                "is witness-backed upper_bound."
            ),
            confidence="upper_bound",
            trials=8000,
            seed=230616400 + row["n"] + row["k"],
        )
        output = os.path.join(HERE, "candidates", f"{stem}-arxiv-2306-16400.json")
        print("schema errors:", save_submission(doc, output) or "none")
        print(stem, "reconstructed", "n/k/d=", doc["n"], doc["k"], doc["distance"]["d"], "->", output)


if __name__ == "__main__":
    main()
