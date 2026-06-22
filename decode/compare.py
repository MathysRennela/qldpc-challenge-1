"""
Illustrative decoding comparison: evaluate representative board codes at a fixed
code-capacity noise rate and rank by logical error rate (LER). Point of the
exercise: show the decoding axis orders codes differently from (n,k,d)/kd^2/n,
i.e. great static parameters do not imply good decoding. Block LER at fixed p;
codes have different k, so this is illustrative, not the final track metric.
"""
import os

from eval import load_code, logical_error_rate

ROOT = os.path.join(os.path.dirname(__file__), "..")
CODES = ["81-1-9", "64-2-8", "126-28-8", "144-12-12", "180-6-10", "120-5-8"]
P = 0.04
SHOTS = 3000

out = []
for slug in CODES:
    HX, HZ, n, k = load_code(os.path.join(ROOT, "codes", f"{slug}.json"))
    r = logical_error_rate(HX, HZ, P, shots=SHOTS, seed=3)
    out.append((slug, n, k, r["ler"], r["ler_per_logical"]))
    print(f"{slug}: n={n} k={k}  block_LER={r['ler']:.4f}  "
          f"per_logical={r['ler_per_logical']:.4f}", flush=True)

print(f"\n=== ranked by PER-LOGICAL LER at p={P} (lower is better) ===")
for slug, n, k, ler, pl in sorted(out, key=lambda x: x[4]):
    print(f"  [[{slug.replace('-', ',')}]]  k={k}  per-logical={pl:.4f}  "
          f"(block={ler:.4f})")
