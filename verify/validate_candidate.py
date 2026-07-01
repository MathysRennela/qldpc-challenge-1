"""validate_candidate -- the trusted gate an autoresearch agent must pass to claim a code.

This is the *conscience* of the autoresearch loop. An agent may explore freely and
write its own code, but every distance/quality CLAIM has to survive this gate, which
it must not be able to weaken.

TRUST MODEL
-----------
1. This file depends ONLY on the trusted verifier stack in ``verify/`` (the verifier,
   the RIS search, the refuter, the WL signature). It imports NOTHING from
   ``research/`` -- the agent's playground -- so an agent cannot soften the gate by
   editing, say, ``research/surrogate.py``; it would have to edit this file.
2. Editing THIS file cannot be prevented on a machine the agent controls, so it is
   not the root of trust. The authoritative run is CI, executing this file from the
   protected ``main`` branch against the submitted candidate. A local run is a fast
   preview. Every verdict is stamped with this file's source hash
   (``validator.source_sha256``) so a verdict produced by a tampered local copy is
   detectable downstream.

The gate, per candidate (a schema-shaped submission ``doc``):
  verify   -- the real verifier passes (schema + n/k/CSS/weight + witnesses)
  converge -- the surrogate distance, raised over a trial ladder, does not drop
              below the claim (a claim above the converged value is an over-claim)
  refute   -- the independent random-seed RIS refuter finds nothing lighter
  dedup    -- not an exact duplicate of a board entry (WL-equivalent is flagged)
  novelty  -- LABEL only: does it advance its own primary-track cell? (literature
              novelty is out of scope here)

``passed`` is True iff verify holds AND the claim is not over-claimed AND not refuted
AND not an exact board duplicate. Novelty is a label, not a pass condition.
"""
import functools
import glob
import hashlib
import json
import os
import secrets
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)                       # trusted verify/ only
import gf2
import qldpc_verify
import heuristic_distance

_REPO = os.path.dirname(_HERE)
_CODES = os.path.join(_REPO, "codes")

# nesting order (stricter -> looser); a code competes in its class and every looser one
_WEIGHT_ORDER = {"weight-4": 0, "weight-6": 1, "weight-8": 2, "weight-9plus": 3}
_LOCAL_ORDER = {"local-2d-single": 0, "local-2d-bilayer": 1, "unrestricted": 2}


def source_sha256():
    """SHA-256 of this validator's own source -- the provenance stamp CI checks."""
    with open(os.path.abspath(__file__), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _matrix(supports, n):
    H = np.zeros((len(supports), n), dtype=np.int8)
    for r, sup in enumerate(supports):
        for q in sup:
            H[r, q] ^= 1
    return H


def _fingerprint(HX, HZ):
    """Exact-duplicate key: RREF pins the stabilizer group (same convention the
    verifier uses). Equal fingerprint => identical code, not merely equivalent."""
    fp = gf2.rref(HX)[0].tobytes() + b"|" + gf2.rref(HZ)[0].tobytes()
    return hashlib.sha256(fp).hexdigest()[:16]


def _board_stamp():
    """A cheap key that changes iff the board files change (name/mtime/size), so the
    scan below can be cached within a session but never goes stale."""
    return tuple((os.path.basename(p), os.path.getmtime(p), os.path.getsize(p))
                 for p in sorted(glob.glob(os.path.join(_CODES, "*.json"))))


@functools.lru_cache(maxsize=4)
def _board_entries_cached(_stamp):
    out = []
    for p in sorted(glob.glob(os.path.join(_CODES, "*.json"))):
        try:
            doc = json.load(open(p))
            rep = qldpc_verify.verify(doc, refute=False)
            comp = rep.get("computed", {})
            out.append({
                "name": os.path.basename(p),
                "n": doc["n"], "k": doc["k"], "d": doc["distance"]["d"],
                "fingerprint": rep.get("fingerprint"),
                "sig": rep.get("signature", {}).get("hash"),
                "weight_class": comp.get("weight_class"),
                "locality_class": comp.get("locality_class"),
            })
        except Exception:
            continue                            # a broken board file never blocks a candidate
    return out


def _board_entries():
    """Trusted read of the current board: (name, n, k, d, fingerprint, sig_hash,
    weight_class, locality_class) for each codes/*.json, all via verify/. Cached
    per board state so validating many candidates does not rescan every time."""
    return _board_entries_cached(_board_stamp())


def _converge_distance(doc, seed, ladder=(5000, 20000)):
    """Raise the RIS search over a trial ladder; return (converged_d, per-step list).
    A converged value that is < the claim means the claim is over-stated."""
    steps = []
    for t in ladder:
        res = heuristic_distance.estimate(doc, trials=t, seed=seed, fast_trials=0)
        steps.append(res["d_heuristic"])
    converged = steps[-1]
    stable = len(steps) >= 2 and steps[-1] == steps[-2]
    return converged, stable, steps


def validate_candidate(doc, *, seed=None, converge_ladder=(5000, 20000)):
    """Run the full trusted gate on a candidate submission ``doc``.

    Returns a structured verdict (JSON-serializable). ``passed`` is the honest
    bottom line; the ``gates`` block is the evidence for each check, and ``labels``
    are the human-facing tags an agent should surface with the candidate.
    """
    if seed is None:
        seed = secrets.randbelow(2**31)         # refutation is non-deterministic by design
    claimed_d = int(doc["distance"]["d"]) if "distance" in doc else None

    verdict = {
        "passed": False,
        "candidate": {"n": doc.get("n"), "k": doc.get("k"), "d": claimed_d,
                      "family": doc.get("family")},
        "gates": {},
        "labels": [],
        "validator": {"source_sha256": source_sha256(), "seed": seed},
    }
    g = verdict["gates"]

    # 1. VERIFY -- the real verifier (schema + n/k/CSS/weight + witnesses).
    rep = qldpc_verify.verify(doc, refute=False)
    failed = [c["check"] for c in rep["checks"] if not c["ok"]]
    comp = rep.get("computed", {})
    g["verify"] = {"ok": rep["ok"], "failed_checks": failed,
                   "weight_class": comp.get("weight_class"),
                   "locality_class": comp.get("locality_class")}
    verdict["candidate"]["weight_class"] = comp.get("weight_class")
    verdict["candidate"]["locality_class"] = comp.get("locality_class")
    if not rep["ok"]:
        verdict["labels"].append("invalid: verifier rejected")
        return verdict                          # nothing else is meaningful if it doesn't verify

    # 2. CONVERGE -- surrogate distance raised over a ladder must not drop below the claim.
    converged, stable, steps = _converge_distance(doc, seed, converge_ladder)
    over_claimed = converged is not None and converged < claimed_d
    g["converge"] = {"claimed_d": claimed_d, "converged_d": converged,
                     "stable": stable, "ladder": list(converge_ladder),
                     "steps": steps, "over_claimed": over_claimed}
    if over_claimed:
        verdict["labels"].append(
            f"over-claimed: distance converges to <= {converged}, below claim {claimed_d}")

    # 3. REFUTE -- independent random-seed RIS refuter must find nothing lighter.
    refuted, d_found, wit, trials = heuristic_distance.refute_check(doc, seed=seed)
    g["refute"] = {"refuted": bool(refuted), "d_found": d_found, "seed": seed,
                   "trials": trials, "witness": wit}
    if refuted:
        verdict["labels"].append(
            f"refuted: found weight-{d_found} logical < claim {claimed_d} (seed {seed})")

    # 4. DEDUP -- compare against the board by exact fingerprint and WL signature.
    HX = _matrix(doc["checks"]["X"], doc["n"])
    HZ = _matrix(doc["checks"]["Z"], doc["n"])
    cand_fp = _fingerprint(HX, HZ)
    cand_sig = rep.get("signature", {}).get("hash")
    board = _board_entries()
    exact_dup = next((b["name"] for b in board if b["fingerprint"] == cand_fp), None)
    wl_equiv = next((b["name"] for b in board
                     if b["sig"] == cand_sig and b["fingerprint"] != cand_fp), None)
    g["dedup"] = {"exact_duplicate_of": exact_dup, "wl_equivalent_of": wl_equiv}
    if exact_dup:
        verdict["labels"].append(f"duplicate: identical to board entry {exact_dup}")
    elif wl_equiv:
        verdict["labels"].append(f"possibly equivalent (same WL signature) to {wl_equiv}")

    # 5. NOVELTY (label only) -- non-dominated within the candidate's own track cell?
    wc, lc = comp.get("weight_class"), comp.get("locality_class")
    n, k, d = doc["n"], doc["k"], claimed_d
    dominators = []
    for b in board:
        # a board code shares the candidate's cell iff it is stricter-or-equal on both axes
        if (_WEIGHT_ORDER.get(b["weight_class"], 9) <= _WEIGHT_ORDER.get(wc, 9)
                and _LOCAL_ORDER.get(b["locality_class"], 9) <= _LOCAL_ORDER.get(lc, 9)):
            if (b["n"] <= n and b["k"] >= k and b["d"] >= d
                    and (b["n"] < n or b["k"] > k or b["d"] > d)):
                dominators.append(f"[[{b['n']},{b['k']},{b['d']}]] {b['name']}")
    board_advancing = not dominators and not exact_dup
    g["novelty"] = {"cell": [wc, lc], "board_advancing": board_advancing,
                    "dominated_by": dominators, "literature_novelty": "unverified"}
    verdict["labels"].append(
        f"advances the {wc} x {lc} board" if board_advancing
        else "does not advance its board cell")
    verdict["labels"].append("literature novelty UNVERIFIED")

    # bottom line
    verdict["passed"] = bool(
        rep["ok"] and not over_claimed and not refuted and not exact_dup)
    return verdict


def main(argv):
    if not argv:
        print("usage: python verify/validate_candidate.py <submission.json>")
        return 2
    doc = json.load(open(argv[0]))
    verdict = validate_candidate(doc)
    print(json.dumps(verdict, indent=2))
    return 0 if verdict["passed"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
