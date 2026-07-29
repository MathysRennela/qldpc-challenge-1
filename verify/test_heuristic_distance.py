"""Validation for heuristic_distance.

1. Corroboration: over a pinned PANEL of exact-certified codes, the heuristic must
   find exactly the certified distance -- lighter would mean a search bug or a bad
   cert, and failing to reach it would mean the search got weaker (the panel is
   sized so the budget reliably reaches d on both the python and gf2_fast engines).
2. Refutation: an inflated (over-claimed) distance must be refuted.

The panel is fixed and small instead of the whole board on purpose: this test
validates the heuristic's LOGIC, and the 30th board entry exercises no code path
the panel doesn't, so board growth must not grow CI time. Auditing the DATA (a bad
cert on any entry) is the weekly refute_board.py cron's job -- it re-checks every
entry with a fresh random seed each run. `--all` sweeps the full board the old way
(tolerant of inconclusive verdicts on large codes) for manual audits.
"""
import argparse
import copy
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heuristic_distance as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Diverse in family, shape and code path: topological k=1 (smallest and larger),
# toric k=2, generalized-bicycle (low-k and the high-k [[126,28,8]]), and the BB
# gross code. Every member corroborates at trials=2500, seed=0 on BOTH engines
# (verified 2026-07-11); if one stops corroborating, the search regressed.
PANEL = ["7-1-3", "16-2-4", "24-6-4", "49-1-7", "72-6-6", "126-28-8"]


def check_code(slug, trials, require_corroboration):
    """Check one cert/code pair; returns (n_failures, report_line)."""
    codef = os.path.join(ROOT, "codes", slug + ".json")
    certf = os.path.join(ROOT, "certs", slug + ".json")
    if not (os.path.exists(codef) and os.path.exists(certf)):
        return 1, f"  {slug:16s} MISSING code or cert file (panel rot -- swap the member)"
    doc = json.load(open(codef))
    cert = json.load(open(certf))
    if not cert.get("d_exact"):
        return 1, f"  {slug:16s} cert is not d_exact (panel rot -- swap the member)"
    exact_d = int(doc["distance"]["d"])  # the cert certifies this as exact
    res = H.estimate(doc, trials=trials, seed=0)
    dh, verdict = res["d_heuristic"], res["verdict"]
    line = (f"  {slug:16s} exact_d={exact_d:2d} d_heur={dh} "
            f"verdict={verdict} method={res['method']}")
    if dh is not None and dh < exact_d:
        return 1, line + "  <<< FOUND LIGHTER THAN EXACT (bug/bad cert)"
    if require_corroboration and verdict != "corroborated":
        return 1, line + "  <<< PANEL MUST CORROBORATE (search regressed?)"
    return 0, line


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true",
                    help="sweep every exact cert on the board (manual audit; "
                         "inconclusive tolerated) instead of the pinned panel")
    ap.add_argument("--trials", type=int, default=2500)
    args = ap.parse_args(argv)

    if args.all:
        slugs = [os.path.basename(cf)[:-len(".json")]
                 for cf in sorted(glob.glob(os.path.join(ROOT, "certs", "*.json")))
                 if json.load(open(cf)).get("d_exact")
                 and os.path.exists(os.path.join(ROOT, "codes", os.path.basename(cf)))]
        mode = f"full board ({len(slugs)} exact certs)"
    else:
        slugs = PANEL
        mode = f"pinned panel ({len(slugs)} codes)"

    failures = 0
    print(f"=== corroboration over {mode}, trials={args.trials} ===")
    for slug in slugs:
        bad, line = check_code(slug, args.trials,
                               require_corroboration=not args.all)
        failures += bad
        print(line)

    print("\n=== refutation: planted over-claim ===")
    doc = json.load(open(os.path.join(ROOT, "codes", "16-2-4.json")))
    true_d = doc["distance"]["d"]
    over = copy.deepcopy(doc)
    over["distance"]["d"] = true_d + 3
    res = H.estimate(over, trials=4000, seed=0)
    print(f"  16-2-4 claimed {true_d + 3} (true {true_d}) -> "
          f"verdict={res['verdict']} d_heur={res['d_heuristic']}")
    ok = res["verdict"] == "refuted"
    print("  refutation", "OK" if ok else "FAILED")
    failures += 0 if ok else 1

    print("\n=== fast-path gating (issue #290) ===")
    import contextlib
    import io
    doc = json.load(open(os.path.join(ROOT, "codes", "16-2-4.json")))
    # explicit fast_trials=0 is the deterministic-gate opt-out: no accelerator,
    # and no warning (refute_check relies on this staying silent in CI logs)
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        res = H.estimate(doc, trials=200, seed=0, fast_trials=0)
    ok = res["method"] == "ris" and err.getvalue() == ""
    print(f"  fast_trials=0: method={res['method']} warned={bool(err.getvalue())}",
          "OK" if ok else "  <<< explicit disable must stay silent")
    failures += 0 if ok else 1
    if H._fast is not None:
        # accelerator importable but out-budgeted: must warn on stderr
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            res = H.estimate(doc, trials=200, seed=0, fast_trials=100)
        ok = "gf2_fast is available but skipped" in err.getvalue()
        print(f"  fast_trials<trials: warned={ok}",
              "OK" if ok else "  <<< silent skip is issue #290")
        failures += 0 if ok else 1
        # CLI default must scale the fast budget with --trials instead of
        # letting a deep --trials run silently drop to pure Python
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            H.main(os.path.join(ROOT, "codes", "16-2-4.json"),
                   trials=200, seed=0)
        method = json.loads(out.getvalue())["method"]
        ok = method == "ris+gf2_fast"
        print(f"  CLI default: method={method}",
              "OK" if ok else "  <<< CLI no longer engages the accelerator")
        failures += 0 if ok else 1
    else:
        print("  gf2_fast not importable here; accelerator cases skipped")

    print(f"\n{failures} failure(s)")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
