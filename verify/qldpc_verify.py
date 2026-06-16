"""
qldpc-challenge submission verifier (Phase 0: structural + cheap semantic +
self-certifying distance upper bounds).

Usage:
    python verify/qldpc_verify.py examples/72-6-6.json

Exit code 0 if every required check passes, 1 otherwise. Prints a JSON report
to stdout. This covers the *trustless* tier: everything here is either a hard
arithmetic fact (CSS commutation, rank/k, witness validity) or a layout
measurement. It does NOT attempt to prove distance lower bounds / exactness;
that is the server-certification tier (Phase 5, separate solver stack).

What "verified" means per field:
  n           matches the qubit count implied by the checks
  k           = n - rank(H_X) - rank(H_Z), matches the claim exactly
  CSS         H_X H_Z^T = 0 over GF(2)
  distance    each provided side witness is a nontrivial logical operator of
              the claimed Pauli type and weight -> certifies d_side <= value
              as an UPPER BOUND. 'exact' claims are downgraded to upper_bound
              here and flagged for server certification.
  locality    coordinates present for all n qubits; measured interaction
              radius (max check diameter) <= claim.
"""

import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import gf2

_HERE = os.path.dirname(os.path.abspath(__file__))
_SCHEMA_PATH = os.path.join(_HERE, "..", "schema", "code.schema.json")
try:
    import jsonschema
    with open(_SCHEMA_PATH) as _f:
        _SCHEMA = json.load(_f)
except Exception:
    jsonschema = None
    _SCHEMA = None

# minimal required structure, used when jsonschema is unavailable
_REQUIRED = ["schema_version", "name", "code_type", "n", "k", "checks",
             "distance", "provenance", "tracks"]


def structure_errors(doc):
    """Return a list of human-readable structural problems, or [] if the doc
    conforms. Uses jsonschema when installed, else a minimal key/type check."""
    if not isinstance(doc, dict):
        return ["top-level value is not a JSON object"]
    if jsonschema is not None and _SCHEMA is not None:
        v = jsonschema.Draft202012Validator(_SCHEMA)
        return [f"{'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}"
                for e in sorted(v.iter_errors(doc), key=lambda e: list(e.path))]
    errs = [f"missing field: {k}" for k in _REQUIRED if k not in doc]
    if "checks" in doc and not (isinstance(doc["checks"], dict)
                                and "X" in doc["checks"] and "Z" in doc["checks"]):
        errs.append("checks must have X and Z support lists")
    return errs


def signature(doc):
    """Permutation-invariant fingerprint. Two codes equal up to a qubit
    permutation must share this; differing signatures are provably distinct
    codes. Equal signatures only FLAG a possible duplicate (necessary, not
    sufficient). Full code equivalence is not auto-decided."""
    n = doc["n"]
    X, Z = doc["checks"]["X"], doc["checks"]["Z"]
    xw = sorted(len(s) for s in X)
    zw = sorted(len(s) for s in Z)
    xdeg = [0] * n
    zdeg = [0] * n
    for s in X:
        for q in s:
            xdeg[q] += 1
    for s in Z:
        for q in s:
            zdeg[q] += 1
    qtypes = sorted(zip(xdeg, zdeg))
    payload = json.dumps([n, doc["k"], doc["distance"]["d"], xw, zw, qtypes],
                         sort_keys=True)
    import hashlib
    return {"hash": hashlib.sha256(payload.encode()).hexdigest()[:16],
            "n": n, "k": doc["k"], "d": doc["distance"]["d"]}


def _matrix(support_list, n):
    H = np.zeros((len(support_list), n), dtype=np.int8)
    for r, sup in enumerate(support_list):
        for q in sup:
            H[r, q] ^= 1
    return H


def _vec(support, n):
    v = np.zeros(n, dtype=np.int8)
    for q in support:
        v[q] ^= 1
    return v


def verify(doc):
    report = {"name": doc.get("name") if isinstance(doc, dict) else None,
              "checks": [], "ok": True, "computed": {}, "earned_distance": {}}

    def record(label, ok, detail=""):
        report["checks"].append({"check": label, "ok": bool(ok),
                                  "detail": detail})
        if not ok:
            report["ok"] = False

    # structural validation first: a malformed doc fails cleanly here rather
    # than crashing the arithmetic below.
    serr = structure_errors(doc)
    record("schema_valid", not serr, "; ".join(serr[:4]))
    if serr:
        return report
    try:
        report["signature"] = signature(doc)
        return _verify_semantic(doc, report, record)
    except Exception as e:  # never crash on a hostile submission
        record("verifier_ran", False, f"{type(e).__name__}: {e}")
        return report


def _verify_semantic(doc, report, record):

    n = doc["n"]
    HX = _matrix(doc["checks"]["X"], n)
    HZ = _matrix(doc["checks"]["Z"], n)

    # 1. index bounds / implied n
    max_idx = max((max(s) for s in doc["checks"]["X"] + doc["checks"]["Z"]
                   if s), default=-1)
    record("qubit_indices_in_range", max_idx < n,
           f"max index {max_idx}, n={n}")

    # 2. checks have distinct supports per row (no repeated qubit within a row
    #    would have been XORed away; flag any that collapsed)
    empty_rows = [i for i, s in enumerate(doc["checks"]["X"] + doc["checks"]["Z"])
                  if len(set(s)) != len(s)]
    record("no_repeated_qubits_in_a_check", not empty_rows,
           f"rows with repeats: {empty_rows[:5]}")

    # 3. CSS commutation
    css = not bool(((HX @ HZ.T) % 2).any())
    record("css_commutation", css, "H_X H_Z^T = 0 over GF(2)")

    # 4. logical dimension k
    rx, rz = gf2.rank(HX), gf2.rank(HZ)
    k_computed = n - rx - rz
    report["computed"].update(n=n, rank_HX=rx, rank_HZ=rz, k=k_computed)
    record("k_matches_claim", k_computed == doc["k"],
           f"computed k={k_computed}, claimed {doc['k']}")

    # 5. check weights (for the weight-bounded tracks)
    wmax = max((len(s) for s in doc["checks"]["X"] + doc["checks"]["Z"]),
               default=0)
    report["computed"]["max_check_weight"] = wmax

    # 6. distance witnesses (self-certifying upper bounds)
    dist = doc["distance"]
    earned_d = []
    for side, opp_H, own_H in (("X", HZ, HX), ("Z", HX, HZ)):
        if side not in dist:
            continue
        sd = dist[side]
        v = _vec(sd["witness"], n)
        wt = int(v.sum())
        in_ker = gf2.commutes(v, opp_H)          # commutes with opposite checks
        nontrivial = not gf2.in_rowspace(v, own_H)  # not a stabilizer product
        good = (wt == sd["value"]) and in_ker and nontrivial
        record(f"distance_{side}_witness", good,
               f"weight={wt} (claim {sd['value']}), in_ker={in_ker}, "
               f"nontrivial={nontrivial}")
        if good:
            tier = "upper_bound"  # 'exact' must be earned by server cert
            report["earned_distance"][side] = {"value": sd["value"],
                                               "tier": tier}
            earned_d.append(sd["value"])
            if sd["confidence"] == "exact":
                record(f"distance_{side}_exact_flagged", True,
                       "exact claim accepted as upper_bound pending server "
                       "certification")

    # 7. code distance consistency
    if earned_d:
        d_earned = min(earned_d)
        record("d_matches_min_side", d_earned == dist["d"],
               f"min earned side = {d_earned}, claimed d = {dist['d']}")
        report["earned_distance"]["d"] = {"value": dist["d"],
                                          "tier": "upper_bound"}

    # 8. locality (optional)
    if "locality" in doc:
        loc = doc["locality"]
        coords = loc["coordinates"]
        record("coordinates_cover_all_qubits", len(coords) == n,
               f"{len(coords)} coords, n={n}")
        if len(coords) == n:
            def diam(sup):
                pts = [coords[q] for q in sup]
                return max((math.dist(a, b) for a in pts for b in pts),
                           default=0.0)
            radius = max((diam(s) for s in doc["checks"]["X"]
                          + doc["checks"]["Z"]), default=0.0)
            report["computed"]["interaction_radius"] = round(radius, 4)
            if "interaction_radius" in loc:
                record("interaction_radius_within_claim",
                       radius <= loc["interaction_radius"] + 1e-9,
                       f"measured {radius:.4f} <= claim "
                       f"{loc['interaction_radius']}")
            report["computed"]["layers"] = loc.get("layers")

    return report


def main(path):
    with open(path) as f:
        doc = json.load(f)
    report = verify(doc)
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python qldpc_verify.py <submission.json>",
              file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
