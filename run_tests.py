"""Run the test suite. A thin wrapper over pytest, kept as the documented entry
point so CI and the README command do not change.

Discovery is still by convention -- pytest collects test_*.py under verify/,
research/, and site/ -- so a new test joins the suite the moment it exists and
cannot be silently left out of CI the way a hand-listed step can (which is how
two of five tests once went unrun).

  uv run --frozen python run_tests.py              # everything (what CI runs)
  uv run --frozen python run_tests.py --skip-slow  # quick local iteration

To run or debug one test, call pytest directly; it replaces running a test file
as a standalone script:

  uv run pytest verify/test_verifier.py            # one file
  uv run pytest verify/test_verifier.py::test_main # one test
  uv run pytest -k refute -x --pdb                 # match, stop, drop into pdb
"""
import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

# Slow tests (about a minute or more locally); skipped with --skip-slow, by
# pytest -k expression so the names stay readable here.
SLOW = []


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-slow", action="store_true",
                    help="skip the tests listed in SLOW")
    args, extra = ap.parse_known_args(argv)

    cmd = [sys.executable, "-m", "pytest", "verify", "research", "site"]
    if args.skip_slow and SLOW:
        cmd += ["--deselect" if "::" in s else "--ignore=" + s for s in SLOW]
    cmd += extra
    return subprocess.run(cmd, cwd=ROOT).returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
