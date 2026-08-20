"""Verifier for measured logical-error-rate claims.

Usage:
    python verify/ler_verify.py codes/your-code.json [circuits-dir]

Exit code 0 iff every check passes for both bases. Prints a JSON report in the
shape of circuit_verify's. Needs ldpc (the `research` extra): a claim that
cannot be checked must not merge, so a missing decoder is a failure here, not
a skip.

An `ler` block rides inside `circuit`, so the circuit artifacts have already
passed circuit_verify in the same CI job; this file re-derives the DEM from
the committed .stim anyway (same pinned path) rather than trusting the .dem
on disk, so the two verifiers cannot be split apart by a later workflow edit.

Checks, per basis:
  arithmetic   ler_per_round and ci95 recompute exactly from (failures,
               shots, rounds) via the pinned conversion and Wilson interval;
               p equals the canonical reference rate; the decoder is the
               pinned one; shots meet the statistical floor
  replication  an independent re-sample (fresh seed, capped shots) decoded
               with the pinned decoder must agree with the claimed per-shot
               rate to within sampling error (|p_rep - p_claim| <= Z_GATE
               sigma under the claimed rate). Statistical by design: the
               sampler is seed-deterministic but BP is float arithmetic, so
               bit-exact replication across platforms is not a promise the
               board can keep. Z_GATE = 4 makes a false alarm on an honest
               claim a per-mille event while catching any misreport large
               enough to matter for ranking.

The claim is self-reported measurement, verified by re-measurement; there is
no clamp analogous to d_circ <= d because a rate has no code-level bound to
clamp to. The gaming direction is claiming a rate LOWER than the circuit
earns, and that is exactly what the replication test detects.
"""

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import circuit_tools as ct
import ler_tools as lt

REPLICA_SHOTS_CAP = 100_000
REPLICA_SEED_SALT = 0x5EED1E12
Z_GATE = 4.0


def verify_ler(doc, circuits_dir):
    """Check the doc's circuit.ler block; returns a report dict, report['ok']
    is the verdict."""
    report = {"ok": True, "checks": [], "computed": {}}

    def record(label, ok, detail=""):
        report["checks"].append({"check": label, "ok": bool(ok),
                                 "detail": detail})
        if not ok:
            report["ok"] = False

    circ = doc.get("circuit") or {}
    ler = circ.get("ler")
    if not ler:
        record("ler_block_present", False, "no circuit.ler block")
        return report
    try:
        import ldpc  # noqa: F401
    except ImportError:
        record("decoder_available", False,
               "ldpc is not installed; an ler claim cannot be verified "
               "(install the `research` extra)")
        return report
    rounds = circ.get("rounds")

    for side in ("X", "Z"):
        claim = ler.get(side)
        if claim is None:
            record(f"{side}_ler_claimed", False, "side missing")
            continue

        # -- arithmetic: the block must be internally exact ------------------
        errs = []
        if claim.get("p") != ct.P_REF:
            errs.append(f"p={claim.get('p')} is not the canonical reference "
                        f"rate {ct.P_REF}")
        if claim.get("decoder") != lt.DECODER_ID:
            errs.append(f"decoder={claim.get('decoder')!r} is not the pinned "
                        f"{lt.DECODER_ID!r}")
        shots, failures = claim.get("shots", 0), claim.get("failures", -1)
        if shots < lt.MIN_SHOTS:
            errs.append(f"shots={shots} below the statistical floor "
                        f"{lt.MIN_SHOTS}")
        if not 0 <= failures <= shots:
            errs.append(f"failures={failures} outside [0, shots]")
        if not errs:
            p_shot = failures / shots
            want = round(lt.per_round(p_shot, rounds), 9)
            lo, hi = lt.wilson_ci(failures, shots)
            want_ci = [round(lt.per_round(lo, rounds), 9),
                       round(lt.per_round(hi, rounds), 9)]
            if abs(claim.get("ler_per_round", -1) - want) > 1e-9:
                errs.append(f"ler_per_round={claim.get('ler_per_round')} "
                            f"does not recompute ({want} from "
                            f"failures/shots/rounds)")
            got_ci = claim.get("ci95") or [-1, -1]
            if (abs(got_ci[0] - want_ci[0]) > 1e-9
                    or abs(got_ci[1] - want_ci[1]) > 1e-9):
                errs.append(f"ci95={got_ci} does not recompute ({want_ci})")
        record(f"{side}_ler_arithmetic", not errs, "; ".join(errs) or
               f"block recomputes exactly from failures={failures}, "
               f"shots={shots}, rounds={rounds}")
        if errs:
            continue

        # -- replication: re-measure with an independent seed ----------------
        base = os.path.join(circuits_dir, {"X": "memory_x", "Z": "memory_z"}[side])
        try:
            import stim
            circuit = stim.Circuit.from_file(base + ".stim")
        except Exception as e:
            record(f"{side}_ler_replicated", False,
                   f"could not load committed circuit: {e}")
            continue
        dem = ct.derive_dem(circuit)
        rep_shots = min(shots, REPLICA_SHOTS_CAP)
        rep_seed = (claim["seed"] ^ REPLICA_SEED_SALT) & 0x7FFFFFFF
        rep_fail = lt.measure_failures(dem, rep_shots, rep_seed)
        p_claim = failures / shots
        p_rep = rep_fail / rep_shots
        sigma = math.sqrt(max(p_claim * (1 - p_claim), 1.0 / shots)
                          / rep_shots)
        ok = abs(p_rep - p_claim) <= Z_GATE * sigma
        record(f"{side}_ler_replicated", ok,
               f"claimed p_shot={p_claim:.6g}, replica {rep_fail}/{rep_shots}"
               f" = {p_rep:.6g} (|diff| {'<=' if ok else '>'} "
               f"{Z_GATE:g} sigma = {Z_GATE * sigma:.3g})")
        report["computed"][side] = {
            "replica_shots": rep_shots, "replica_seed": rep_seed,
            "replica_failures": rep_fail}
    return report


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    path = argv[0]
    doc = json.load(open(path))
    slug = os.path.splitext(os.path.basename(path))[0]
    circuits_dir = (argv[1] if len(argv) > 1 else
                    os.path.join(os.path.dirname(os.path.abspath(path)),
                                 "..", "circuits", slug))
    report = verify_ler(doc, circuits_dir)
    print(json.dumps(report, indent=1))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
