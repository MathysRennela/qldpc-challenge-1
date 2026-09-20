#!/usr/bin/env python3
"""Re-measure a board entry's distance claim on fresh seeds before targeting it.

A leaderboard distance is a witness-backed *upper* bound, and a claim that is one
or two units soft makes any candidate tuned to beat it wasted budget -- while a
refutation is itself a valid submission.

Verdicts: `refuted` (a lighter logical was exhibited; decisive), `holds` (the
search reached the claim and found nothing lighter; evidence, not proof) and
`inconclusive` (it did not even reach the claim; says nothing about the code, and
must not be read as corroboration).

Search: random information sets on both Pauli sides, via `verify/gf2_fast` when
built (`make fast`), else NumPy. Every witness is re-validated against the raw
matrices before it is recorded; one that fails is discarded.

  ladder  one entry, an escalating budget ladder on fresh seeds each rung
  screen  several entries at one budget, to triage a whole cell's leaders

Pass `--witness-out` (ladder) or `--witness-dir` (screen): the best support is
written on every new best, so a rung killed by a time limit still leaves the
artifact a revision needs. Set `--pair-depth` to the depth the claim's own ladder
used; the default of 10 under-reads against the 24-80 these affine ladders used
and reports a soft claim as a hold.

  python research/audits/leader_audit.py ladder codes/360-12-24.json \
      --ladder 1000000:101 5000000:201 --pair-depth 64 --witness-out /tmp/w.json
  python research/audits/leader_audit.py screen --trials 2000000 --seeds 51 52 \
      --pair-depth 64 codes/672-20-32.json codes/922-18-31.json

`holds` never upgrades a claim to the exact (`d=`) tier; that needs
`verify/certify.py`.
"""

import argparse
import json
import os
import sys
import time

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", ".."))
for _p in (os.path.join(_REPO, "research", "kit"), os.path.join(_REPO, "verify")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import surrogate  # noqa: E402
from css import commutes, compute_k, in_rowspace, verify_css  # noqa: E402


def load_entry(path):
    """Return (n, k, HX, HZ, doc) for a board JSON entry."""
    with open(path) as fh:
        doc = json.load(fh)
    n = int(doc["n"])
    HX = _rows_to_dense(doc["checks"]["X"], n)
    HZ = _rows_to_dense(doc["checks"]["Z"], n)
    return n, int(doc["k"]), HX, HZ, doc


def _rows_to_dense(rows, n):
    M = np.zeros((len(rows), n), dtype=np.int8)
    for i, row in enumerate(rows):
        for q in row:
            M[i, int(q)] ^= 1
    return M


def ris(HX, HZ, trials, seed, threads=8, pair_depth=10):
    """One RIS search on both sides. Returns (weight, side, support, seconds)."""
    t0 = time.time()
    if surrogate._fast is not None:
        w, side, support = surrogate._fast.distance_rand_witness(
            np.asarray(HX, dtype=np.int8),
            np.asarray(HZ, dtype=np.int8),
            trials=int(trials),
            seed=int(seed),
            pair_depth=pair_depth,
            threads=int(threads),
        )
        w = surrogate._weight_or_inf(w, HX.shape[1])
        support = sorted(int(q) for q in support) if support else []
        side = {"X": "X", "Z": "Z"}.get(side, side)
        if side in ("X", "Z"):
            return w, side, support, time.time() - t0
    # NumPy fallback, or an accelerator proposal that did not validate.
    prepared = surrogate.prepare_distance_search(HX, HZ)
    wx, sx = surrogate._search_lightest(*prepared.side("X")[:2], trials, seed, bases=prepared.side("X")[2:])
    wz, sz = surrogate._search_lightest(*prepared.side("Z")[:2], trials, seed + 1, bases=prepared.side("Z")[2:])
    side, (w, sup) = ("X", (wx, sx)) if wx <= wz else ("Z", (wz, sz))
    if w > HX.shape[1]:
        return float("inf"), "", [], time.time() - t0
    return w, side, sorted(int(q) for q in sup), time.time() - t0


def validate_witness(n, HX, HZ, side, weight, support):
    """Re-check a proposed logical against the raw matrices, independently."""
    if side not in ("X", "Z"):
        return False, "no witness"
    support = [int(q) for q in support]
    if len(support) != len(set(support)) or any(q < 0 or q >= n for q in support):
        return False, "bad support"
    if len(support) != int(weight):
        return False, "weight != support size"
    v = np.zeros(n, dtype=np.int8)
    v[support] = 1
    Hself, Hopp = (HX, HZ) if side == "X" else (HZ, HX)
    if not commutes(v, Hopp):
        return False, "does not commute with the opposite checks"
    if in_rowspace(v, Hself):
        return False, "lies in the stabilizer row space (trivial)"
    return True, "ok"


def describe(n, k_claim, HX, HZ, doc, tag):
    k = compute_k(HX, HZ)
    w = max(int(HX.sum(axis=1).max()), int(HZ.sum(axis=1).max()))
    print(
        f"{tag}: n={n} k={k} (claimed {k_claim}) w={w} css_ok={verify_css(HX, HZ)}"
        f" claim d<={doc['distance']['d']}"
        f" (X={doc['distance']['X']['value']}, Z={doc['distance']['Z']['value']})",
        flush=True,
    )
    return k, w


def _parse_ladder(text):
    """'1000000:101,102 5000000:201' -> [(1000000, [101, 102]), (5000000, [201])]."""
    out = []
    for rung in text:
        trials, _, seeds = rung.partition(":")
        out.append((int(trials), [int(s) for s in seeds.split(",") if s]))
    return out


def _write_witness(path, payload):
    """Persist a witness with an atomic replace.

    Called on *every* new best rather than once at the end of a ladder: a rung
    can be killed by a time limit or a scheduler, and the witness behind the
    lightest reading is the artifact a distance revision needs. Losing it costs
    a re-run of the whole rung.
    """
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, "w") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, path)


def _best_payload(entry, n, k, claim, best, verdict=None):
    payload = {"entry": entry, "n": n, "k": k, "claim": claim, **best}
    if verdict is not None:
        payload["verdict"] = verdict
    return payload


def cmd_ladder(args):
    n, k_claim, HX, HZ, doc = load_entry(args.entry)
    k, w = describe(n, k_claim, HX, HZ, doc, os.path.basename(args.entry))
    claim = doc["distance"]["d"]
    best = {"weight": n + 1, "side": None, "support": [], "seed": None, "trials": None}
    print(f"  pair_depth={args.pair_depth} threads={args.threads}", flush=True)
    for trials, seeds in args.ladder:
        for seed in seeds:
            weight, side, support, dt = ris(HX, HZ, trials, seed, args.threads, args.pair_depth)
            ok, why = validate_witness(n, HX, HZ, side, weight, support)
            print(f"  trials={trials:>10,} seed={seed}: d<={weight} side={side} [{dt:.0f}s] witness={why}", flush=True)
            if not ok:
                # A proposal that fails the independent re-check must not move
                # the bar: otherwise the verdict, and the saved witness, could
                # be driven by exactly the accelerator bug this re-check exists
                # to catch.
                print(f"    DISCARDED d<={weight}: {why}", flush=True)
                continue
            if weight < best["weight"]:
                best = {"weight": weight, "side": side, "support": support, "seed": seed, "trials": trials}
                print(f"    NEW BEST d<={weight} side={side} support={support}", flush=True)
                if args.witness_out:
                    _write_witness(args.witness_out, _best_payload(args.entry, n, k, claim, best))
    verdict = "REFUTED" if best["weight"] < claim else "holds" if best["weight"] == claim else "inconclusive"
    print(
        f"VERDICT: n={n} k={k} claim={claim} d_ub={best['weight']} "
        f"eff(kd^2/n)={k * best['weight'] ** 2 / n:.2f} -> {verdict}",
        flush=True,
    )
    if args.witness_out and best["support"]:
        _write_witness(args.witness_out, _best_payload(args.entry, n, k, claim, best, verdict))
    return 2 if verdict == "REFUTED" else 0


def cmd_screen(args):
    rows = []
    print(f"  pair_depth={args.pair_depth} threads={args.threads}", flush=True)
    for entry in args.entries:
        n, k_claim, HX, HZ, doc = load_entry(entry)
        k, w = describe(n, k_claim, HX, HZ, doc, os.path.basename(entry))
        claim = doc["distance"]["d"]
        best = {"weight": n + 1, "side": None, "support": [], "seed": None, "trials": args.trials}
        for seed in args.seeds:
            weight, side, support, dt = ris(HX, HZ, args.trials, seed, args.threads, args.pair_depth)
            ok, why = validate_witness(n, HX, HZ, side, weight, support)
            print(f"  seed={seed}: d<={weight} side={side} [{dt:.0f}s] witness={why}", flush=True)
            if not ok:
                print(f"    DISCARDED d<={weight}: {why}", flush=True)
                continue
            if weight < best["weight"]:
                best = {"weight": weight, "side": side, "support": support, "seed": seed, "trials": args.trials}
                print(f"    NEW BEST d<={weight} side={side} support={support}", flush=True)
                if args.witness_dir:
                    stem = os.path.basename(entry)[:-5]
                    _write_witness(
                        os.path.join(args.witness_dir, f"{stem}.json"),
                        _best_payload(entry, n, k, claim, best),
                    )
        verdict = "REFUTED" if best["weight"] < claim else "holds" if best["weight"] == claim else "inconclusive"
        rows.append((os.path.basename(entry)[:-5], n, k, w, claim, best["weight"], verdict))
    print("=" * 72)
    print(f"{'entry':>14s} | {'n':>4s} {'k':>4s} {'w':>2s} {'claim':>5s} {'d_ub':>5s}  verdict")
    for name, n, k, w, claim, best, verdict in rows:
        print(f"{name:>14s} | {n:4d} {k:4d} {w:2d} {claim:5d} {best:5d}  {verdict}")
    return 2 if any(r[-1] == "REFUTED" for r in rows) else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    lad = sub.add_parser("ladder", help="escalating budget ladder on one entry")
    lad.add_argument("entry")
    lad.add_argument(
        "--ladder",
        nargs="+",
        required=True,
        metavar="TRIALS:SEED,SEED",
        type=str,
        help="e.g. 1000000:101,102 20000000:301,302",
    )
    lad.add_argument("--threads", type=int, default=8)
    lad.add_argument(
        "--pair-depth",
        type=int,
        default=10,
        help="how many of the lightest reduced rows are combined pairwise each trial "
        "(larger finds lighter logicals for little extra cost; match the depth the claim's "
        "own ladder used, e.g. 64, or the reading is not comparable)",
    )
    lad.add_argument(
        "--witness-out",
        default=None,
        help="file to write the lightest validated witness to; rewritten on every new best",
    )
    lad.set_defaults(func=cmd_ladder)

    scr = sub.add_parser("screen", help="one budget, several entries")
    scr.add_argument("entries", nargs="+")
    scr.add_argument("--trials", type=int, default=2_000_000)
    scr.add_argument("--seeds", type=int, nargs="+", default=[51])
    scr.add_argument("--threads", type=int, default=8)
    scr.add_argument("--pair-depth", type=int, default=10)
    scr.add_argument(
        "--witness-dir",
        default=None,
        help="directory to drop <entry>.json for the lightest validated witness per entry",
    )
    scr.set_defaults(func=cmd_screen)

    args = ap.parse_args(argv)
    if getattr(args, "ladder", None):
        args.ladder = _parse_ladder(args.ladder)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
