import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
CODES = os.path.join(os.path.dirname(HERE), "codes")

files = {
    "216-8-18.json": "Quantum Tanner code on a left-right Cayley complex over C6; A- and B-side local codes both [6,3,3] shortened Hamming; matrices verbatim from arXiv:2512.20532 auxiliary files.",
    "432-20-22.json": "Quantum Tanner code on a left-right Cayley complex over C6xC2; A- and B-side local codes both [6,3,3] shortened Hamming; matrices verbatim from arXiv:2512.20532 auxiliary files.",
    "576-28-24.json": "Quantum Tanner code on a left-right Cayley complex over C4rC4; A- and B-side local codes both [6,3,3] shortened Hamming; matrices verbatim from arXiv:2512.20532 auxiliary files.",
}

for fn, construction in files.items():
    p = os.path.join(CODES, fn)
    doc = json.load(open(p))
    doc["provenance"]["novelty"] = "known_parameters"
    doc["provenance"]["references"] = ["arXiv:2512.20532"]
    doc["provenance"]["notes"] = (
        "Reproduction of a published quantum Tanner code from arXiv:2512.20532 "
        "(Table 1b). Parity-check matrices taken verbatim from the paper's "
        "auxiliary files. Distance is witness-backed upper_bound; the paper "
        "reports a QDistRnd upper bound."
    )
    with open(p, "w") as f:
        json.dump(doc, f, indent=1)
        f.write("\n")
    print("updated", fn)
