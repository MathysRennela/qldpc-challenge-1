"""
GPU deep RIS refutation/witness search for board codes -- wrapper around the
standalone verify/ris_gpu.cu binary (build with `make ris`).

For each side of a CSS code this derives the opposite-type logical basis
exactly as qldpc_verify.py does (via gf2.py, the audited reference), hands
the packed matrices to the GPU binary, and then re-verifies any recovered
operator here on the CPU: in ker(H_check), anticommutes with a logical,
weight recounted. Only CPU-verified operators are reported. All weights are
upper bounds on distance; nothing here is a proof.

    make ris
    python verify/ris_gpu.py codes/674-128-87.json --trials 1000000000

Writes <code>.witness.json alongside each input. The GPU binary needs an
NVIDIA GPU + CUDA; this wrapper itself is numpy + stdlib only.
"""

import argparse
import json
import os
import struct
import subprocess
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gf2  # noqa: E402

MAGIC = b"RISGPU01"


def find_binary(explicit=None):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates = [explicit, os.environ.get("RIS_GPU_BIN"),
                  os.path.join(root, "build", "ris_gpu")]
    for c in candidates:
        if c and os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    raise FileNotFoundError(
        "ris_gpu binary not found; build it with `make ris` or set RIS_GPU_BIN")


def checks_matrix(support_list, n):
    H = np.zeros((len(support_list), n), dtype=np.int8)
    for r, sup in enumerate(support_list):
        for q in sup:
            H[r, q] ^= 1
    return H


def pack_rows(M):
    """Bit-pack GF(2) rows LSB-first: column j -> word j//64, bit j%64.
    Must match the layout ris_gpu.cu reads."""
    M = (np.asarray(M, dtype=np.uint8) % 2)
    m, n = M.shape
    nw = (n + 63) // 64
    padded = np.zeros((m, nw * 64), dtype=np.uint8)
    padded[:, :n] = M
    powers = np.uint64(1) << np.arange(64, dtype=np.uint64)
    return (padded.reshape(m, nw, 64).astype(np.uint64) * powers).sum(axis=2,
                                                                      dtype=np.uint64)


def write_input(path, W_null, W_logical, n):
    packed_null = pack_rows(W_null)
    packed_logical = pack_rows(W_logical)
    nw = packed_null.shape[1]
    with open(path, "wb") as f:
        f.write(MAGIC)
        f.write(struct.pack("<4i", n, packed_null.shape[0],
                            packed_logical.shape[0], nw))
        f.write(packed_null.astype("<u8").tobytes())
        f.write(packed_logical.astype("<u8").tobytes())


def parse_output(text):
    out = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        out[key] = val
    if "support" in out:
        out["support"] = [int(x) for x in out["support"].split(",") if x]
    for key in ("best_weight", "trials", "n", "k_sub", "k_null", "k_logical"):
        if key in out:
            out[key] = int(out[key])
    return out


def cpu_verify(support, n, H_check, L_opp):
    """The trust boundary: accept an operator only on CPU-checked evidence.

    Returns the recounted weight of the verified operator, or None. Malformed
    support lists (out-of-range or duplicate indices) are rejected like any
    failed verification rather than crashing the sweep."""
    if not support or len(set(support)) != len(support) or \
            not all(isinstance(q, int) and 0 <= q < n for q in support):
        return None
    v = np.zeros(n, dtype=np.int8)
    v[support] = 1
    if not gf2.commutes(v, H_check):
        return None
    if not bool(((gf2._as_gf2(L_opp) @ v) % 2).any()):
        return None
    return int(v.sum())


def run_side(side, H_check, L_opp, claimed, args, binary):
    with tempfile.NamedTemporaryFile(suffix=".risgpu", delete=False) as tmp:
        write_input(tmp.name, gf2.kernel_basis(H_check), L_opp,
                    H_check.shape[1])
        cmd = [binary, tmp.name, "--mode", args.mode,
               "--trials", str(args.trials), "--seed", str(args.seed)]
        if args.k_sub is not None:
            cmd += ["--k-sub", str(args.k_sub)]
        if args.pair_depth:
            cmd += ["--pair-depth", str(args.pair_depth)]
        if args.target is not None:
            cmd += ["--target", str(args.target)]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  check=True, timeout=args.proc_timeout)
        finally:
            os.unlink(tmp.name)
    res = parse_output(proc.stdout)
    entry = {"claimed": claimed, "gpu_best_weight": res.get("best_weight"),
             "trials": res.get("trials"), "witness_weight": None,
             "operator_support": None, "cpu_verified": False}
    support = res.get("support")
    if support:
        weight = cpu_verify(support, H_check.shape[1], H_check, L_opp)
        if weight is not None:
            entry["witness_weight"] = weight
            entry["operator_support"] = support
            entry["cpu_verified"] = True
        else:
            print(f"  [{side}] GPU operator FAILED CPU verification -- "
                  "discarded", file=sys.stderr)
    print(f"  [{side}] claimed {claimed}, GPU best {res.get('best_weight')}, "
          f"cpu-verified witness "
          f"{entry['witness_weight'] if entry['cpu_verified'] else 'none'}")
    return entry


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("code_json", nargs="+", help="board code JSON file(s)")
    ap.add_argument("--trials", type=int, default=50_000_000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--k-sub", type=int, default=None,
                    help="sketch rows (default: binary's default; in "
                         "--pair-depth mode the binary defaults to the "
                         "full kernel basis)")
    ap.add_argument("--pair-depth", type=int, default=0,
                    help=">0: deep kernel (full-basis RREF + XOR pairs of "
                         "the P lightest rows per trial); stronger per "
                         "trial at large n")
    ap.add_argument("--mode", choices=("recover", "estimate"),
                    default="recover")
    ap.add_argument("--target", type=int, default=None,
                    help="early-stop once a weight < target is committed")
    ap.add_argument("--sides", default="X,Z")
    ap.add_argument("--binary", default=None,
                    help="path to the ris_gpu binary (default: build/ris_gpu)")
    ap.add_argument("--proc-timeout", type=int, default=7200,
                    help="kill a wedged GPU binary after this many seconds")
    args = ap.parse_args()
    binary = find_binary(args.binary)
    sides = [s.strip().upper() for s in args.sides.split(",") if s.strip()]

    for path in args.code_json:
        with open(path) as f:
            doc = json.load(f)
        n = doc["n"]
        HX = checks_matrix(doc["checks"]["X"], n)
        HZ = checks_matrix(doc["checks"]["Z"], n)
        dist = doc["distance"]
        print(f"{path}: [[{n},{doc['k']},{dist['d']}]] mode={args.mode} "
              f"trials={args.trials}")
        out = {"code": path, "tool": "ris_gpu", "mode": args.mode,
               "trials": args.trials, "seed": args.seed}
        # An X-type logical lives in ker(H_Z) and must anticommute with a
        # Z-type logical; mirror for Z.
        if "X" in sides:
            out["X"] = run_side("X", HZ, gf2.logical_basis(HX, HZ),
                                dist["X"]["value"], args, binary)
        if "Z" in sides:
            out["Z"] = run_side("Z", HX, gf2.logical_basis(HZ, HX),
                                dist["Z"]["value"], args, binary)
        res_path = path.rsplit(".json", 1)[0] + ".witness.json"
        with open(res_path, "w") as f:
            json.dump(out, f, indent=1)
        print(f"  -> {res_path}")


if __name__ == "__main__":
    main()
