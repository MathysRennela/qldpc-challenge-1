"""Run every test in the repo, discovered by convention -- not by a hand-kept list.

Any file matching verify/test_*.py or research/test_*.py is part of the suite the
moment it exists; it cannot be silently left out of CI the way a hand-listed step
can (which is how two of five tests once went unrun). Each test stays a standalone
script (plain python, exit 0 = pass) so it can still be run and audited on its own.

  uv run --frozen python run_tests.py              # everything (what CI runs)
  uv run --frozen python run_tests.py --skip-slow  # quick local iteration
"""
import argparse
import glob
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))

# Slow tests (about a minute or more locally); skipped with --skip-slow.
# Currently empty: test_heuristic_distance.py used to sweep every certified code
# (O(board size)) but now checks a fixed panel and runs in seconds.
SLOW = set()


def collect():
    tests = []
    for pattern in ("verify/test_*.py", "research/test_*.py"):
        tests += sorted(glob.glob(os.path.join(ROOT, pattern)))
    return [os.path.relpath(t, ROOT) for t in tests]


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-slow", action="store_true",
                    help="skip the tests listed in SLOW")
    args = ap.parse_args(argv)

    tests = collect()
    if args.skip_slow:
        tests = [t for t in tests if t not in SLOW]
    if not tests:
        print("no tests found -- the glob conventions are broken")
        return 1

    failed = []
    for t in tests:
        print(f"\n=== {t} ===", flush=True)
        t0 = time.time()
        r = subprocess.run([sys.executable, os.path.join(ROOT, t)], cwd=ROOT)
        dt = time.time() - t0
        status = "PASS" if r.returncode == 0 else f"FAIL (exit {r.returncode})"
        print(f"=== {t}: {status} in {dt:.1f}s ===", flush=True)
        if r.returncode != 0:
            failed.append(t)

    print(f"\n{len(tests) - len(failed)}/{len(tests)} test files passed"
          + (f"; FAILED: {', '.join(failed)}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
