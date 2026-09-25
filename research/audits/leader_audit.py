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
used; the default of 10 under-reads against the 24-80 these affine ladders used,
so a soft claim cannot be refuted and lands on `inconclusive`.

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
import re
import sys
import tempfile
import time

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", ".."))
for _p in (os.path.join(_REPO, "research", "kit"), os.path.join(_REPO, "verify")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Verdict tokens: printed and written verbatim, so a script can match the string
# the README documents. Exit 2 is the documented "a claim was refuted" signal a
# gating script keys on, so a usage error or an unusable entry must not reuse it.
VERDICT_REFUTED = "refuted"
VERDICT_HOLDS = "holds"
VERDICT_INCONCLUSIVE = "inconclusive"
EXIT_OK = 0
EXIT_REFUTED = 2
EXIT_INVALID = 3

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


def _search_side(prepared, tag, trials, seed, pair_depth):
    """One side's NumPy search, reusing the prepared GF(2) bases."""
    hself, hopp, kernel, logicals = prepared.side(tag)
    return surrogate._search_lightest(hself, hopp, trials, seed, pair_depth=pair_depth, bases=(kernel, logicals))


def ris(HX, HZ, trials, seed, threads=8, pair_depth=10, prepared=None):
    """One RIS search on both sides. Returns (weight, side, support, seconds).

    ``prepared`` (from ``surrogate.prepare_distance_search``) is built once by
    the ladder and screen loops and reused: the GF(2) bases depend only on the
    check matrices, so rebuilding them per seed is pure waste.
    """
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
        if side in ("X", "Z"):
            return w, side, support, time.time() - t0
        # The n+1 sentinel: no logical of either type (a k = 0 entry, or a search
        # that found nothing). That is a result, not a reason to retry. Falling
        # through here would re-run the whole budget on the NumPy path, which is
        # ~1 ms/trial -- hours at an 8M rung, not a cheap second opinion.
        return float("inf"), "", [], time.time() - t0
    if prepared is None:
        prepared = surrogate.prepare_distance_search(HX, HZ)
    # Independent streams per side. With plain `seed` / `seed + 1` the Z side of
    # ladder seed s replays the X side of seed s + 1, which is not the "fresh
    # independent seeds each rung" the ladder advertises.
    x_seed, z_seed = np.random.SeedSequence(int(seed)).spawn(2)
    wx, sx = _search_side(prepared, "X", trials, x_seed, pair_depth)
    wz, sz = _search_side(prepared, "Z", trials, z_seed, pair_depth)
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
    css_ok = verify_css(HX, HZ)
    w = max(int(HX.sum(axis=1).max()), int(HZ.sum(axis=1).max()))
    print(
        f"{tag}: n={n} k={k} (claimed {k_claim}) w={w} css_ok={css_ok}"
        f" claim d<={doc['distance']['d']}"
        f" (X={doc['distance']['X']['value']}, Z={doc['distance']['Z']['value']})",
        flush=True,
    )
    return k, w, css_ok


def _reject_unusable(entry, k, k_claim, css_ok):
    """Refuse to score an entry that is not the code it claims to be.

    A verdict, an exit code and a witness are all things a gating script acts
    on. Producing them for an entry whose check matrices do not commute, or
    whose recorded ``k`` is not the ``k`` of its matrices, means acting on a
    refutation of something that is not the claimed CSS code.
    """
    if not css_ok:
        print(f"ERROR: {entry}: H_X H_Z^T != 0 over GF(2); not a CSS code", file=sys.stderr, flush=True)
        return True
    if k != k_claim:
        print(
            f"ERROR: {entry}: recomputed k={k} != recorded k={k_claim}; "
            "a verdict here would not be about the claimed code",
            file=sys.stderr,
            flush=True,
        )
        return True
    return False


def _verdict(best_weight, claim):
    if best_weight < claim:
        return VERDICT_REFUTED
    if best_weight == claim:
        return VERDICT_HOLDS
    return VERDICT_INCONCLUSIVE


def _parse_ladder(text):
    """'1000000:101,102 5000000:201' -> [(1000000, [101, 102]), (5000000, [201])].

    A rung with no seeds runs zero searches but still appears in the log, so it
    is rejected rather than silently skipped: a reader would otherwise take the
    deep rung for run, and the verdict would be computed from the rungs that did
    run. A non-positive trial count is the same failure mode and is rejected too.
    """
    out = []
    for rung in text:
        trials, sep, seeds = rung.partition(":")
        if not sep:
            raise argparse.ArgumentTypeError(f"ladder rung {rung!r} has no seeds; expected TRIALS:SEED[,SEED...]")
        try:
            n_trials = int(trials)
            seed_list = [int(s) for s in seeds.split(",") if s]
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"ladder rung {rung!r}: {exc}") from None
        if not seed_list:
            raise argparse.ArgumentTypeError(f"ladder rung {rung!r} has no seeds; expected TRIALS:SEED[,SEED...]")
        if n_trials <= 0:
            raise argparse.ArgumentTypeError(f"ladder rung {rung!r}: trials must be positive")
        out.append((n_trials, seed_list))
    return out


def _write_witness(path, payload):
    """Persist a witness with an atomic replace.

    Called on *every* new best rather than once at the end of a ladder: a rung
    can be killed by a time limit or a scheduler, and the witness behind the
    lightest reading is the artifact a distance revision needs. Losing it costs
    a re-run of the whole rung.

    The scratch file comes from ``tempfile.mkstemp`` rather than a fixed
    ``<path>.tmp``: two processes writing the same path would otherwise race for
    the same scratch name and one would clobber the other's half-written file.
    """
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=parent, prefix=os.path.basename(path) + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)
            fh.write("\n")
        os.chmod(tmp, 0o644)  # mkstemp is 0600; keep the usual umask-style default
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def _witness_stem(entry):
    """Return a stable, collision-free stem for one entry's screen witness file.

    ``os.path.basename`` alone lets two entries that share a file name -- a board
    entry and a copy of it kept in a scratch directory -- overwrite each other's
    witness. Naming by the path relative to the repo (the convention elsewhere
    in ``verify/``) keeps one file per entry; a path outside the repo falls back
    to the absolute path, which is unique for the same reason.
    """
    absolute = os.path.abspath(entry)
    rel = os.path.relpath(absolute, _REPO)
    if rel.startswith(".."):
        rel = absolute
    if rel.endswith(".json"):
        rel = rel[:-5]
    return re.sub(r"[^A-Za-z0-9._-]+", "_", rel)


def _best_payload(entry, n, k, claim, best, verdict=None):
    payload = {"entry": entry, "n": n, "k": k, "claim": claim, **best}
    if verdict is not None:
        payload["verdict"] = verdict
    return payload


def cmd_ladder(args):
    n, k_claim, HX, HZ, doc = load_entry(args.entry)
    k, w, css_ok = describe(n, k_claim, HX, HZ, doc, os.path.basename(args.entry))
    if _reject_unusable(args.entry, k, k_claim, css_ok):
        return EXIT_INVALID
    claim = doc["distance"]["d"]
    if args.witness_out and os.path.exists(args.witness_out):
        # A file left by an earlier run would survive a run in which nothing is
        # found or every proposal is discarded, and then read as this run's
        # artifact -- stale `verdict: refuted` included.
        os.remove(args.witness_out)
    prepared = surrogate.prepare_distance_search(HX, HZ)
    best = {"weight": n + 1, "side": None, "support": [], "seed": None, "trials": None}
    print(f"  pair_depth={args.pair_depth} threads={args.threads}", flush=True)
    for trials, seeds in args.ladder:
        for seed in seeds:
            weight, side, support, dt = ris(HX, HZ, trials, seed, args.threads, args.pair_depth, prepared=prepared)
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
    verdict = _verdict(best["weight"], claim)
    # eff(kd^2/n) is only meaningful once a logical was actually found: when
    # nothing was, the best weight is the n + 1 sentinel, not a distance.
    eff = f"eff(kd^2/n)={k * best['weight'] ** 2 / n:.2f} " if best["weight"] <= n else ""
    print(
        f"VERDICT: n={n} k={k} claim={claim} d_ub={best['weight']} {eff}-> {verdict}",
        flush=True,
    )
    if args.witness_out and best["support"]:
        _write_witness(args.witness_out, _best_payload(args.entry, n, k, claim, best, verdict))
    return EXIT_REFUTED if verdict == VERDICT_REFUTED else EXIT_OK


def cmd_screen(args):
    rows = []
    print(f"  pair_depth={args.pair_depth} threads={args.threads}", flush=True)
    for entry in args.entries:
        n, k_claim, HX, HZ, doc = load_entry(entry)
        k, w, css_ok = describe(n, k_claim, HX, HZ, doc, os.path.basename(entry))
        if _reject_unusable(entry, k, k_claim, css_ok):
            return EXIT_INVALID
        claim = doc["distance"]["d"]
        prepared = surrogate.prepare_distance_search(HX, HZ)
        best = {"weight": n + 1, "side": None, "support": [], "seed": None, "trials": args.trials}
        for seed in args.seeds:
            weight, side, support, dt = ris(HX, HZ, args.trials, seed, args.threads, args.pair_depth, prepared=prepared)
            ok, why = validate_witness(n, HX, HZ, side, weight, support)
            print(f"  seed={seed}: d<={weight} side={side} [{dt:.0f}s] witness={why}", flush=True)
            if not ok:
                print(f"    DISCARDED d<={weight}: {why}", flush=True)
                continue
            if weight < best["weight"]:
                best = {"weight": weight, "side": side, "support": support, "seed": seed, "trials": args.trials}
                print(f"    NEW BEST d<={weight} side={side} support={support}", flush=True)
                if args.witness_dir:
                    _write_witness(
                        os.path.join(args.witness_dir, f"{_witness_stem(entry)}.json"),
                        _best_payload(entry, n, k, claim, best),
                    )
        verdict = _verdict(best["weight"], claim)
        rows.append((os.path.splitext(os.path.basename(entry))[0], n, k, w, claim, best["weight"], verdict))
    print("=" * 72)
    print(f"{'entry':>14s} | {'n':>4s} {'k':>4s} {'w':>2s} {'claim':>5s} {'d_ub':>5s}  verdict")
    for name, n, k, w, claim, best, verdict in rows:
        print(f"{name:>14s} | {n:4d} {k:4d} {w:2d} {claim:5d} {best:5d}  {verdict}")
    return EXIT_REFUTED if any(r[-1] == VERDICT_REFUTED for r in rows) else EXIT_OK


class _Parser(argparse.ArgumentParser):
    """argparse exits 2 on a usage error, and 2 is also EXIT_REFUTED.

    A gating script keys on 2 meaning "a claim was refuted", so a mistyped
    invocation must not be indistinguishable from one.
    """

    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(EXIT_INVALID, f"{self.prog}: error: {message}\n")


def main(argv=None):
    ap = _Parser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
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
        help="file to write the lightest validated witness to; cleared at the start of a run "
        "and rewritten on every new best",
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
        help="directory to drop one witness file per entry, named after the entry's path "
        "within the repo so two same-named entries cannot overwrite each other",
    )
    scr.set_defaults(func=cmd_screen)

    args = ap.parse_args(argv)
    if getattr(args, "ladder", None):
        try:
            args.ladder = _parse_ladder(args.ladder)
        except argparse.ArgumentTypeError as exc:
            ap.error(str(exc))
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
