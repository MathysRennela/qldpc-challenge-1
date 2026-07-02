"""Integrity check for the trusted autoresearch validation stack (CI).

The autoresearch gate (`validate_candidate`) is only as trustworthy as the code it
depends on: if an agent could quietly edit the refuter or the distance search it
calls, it could soften the gate without ever touching the validator file. So this
pins the SHA-256 of the whole trusted closure -- the validator PLUS its trusted
dependencies -- and fails if any of it drifts from the pinned manifest.

Effect: a change to the trusted stack cannot be silent. It must re-pin the manifest
(`--update`), and that manifest diff is a small, reviewable, CODEOWNERS-gatable line
in the PR. CI runs this from the trusted tree, where an agent has no write access,
so an agent's LOCAL edits are irrelevant to what the board accepts.

  python verify/check_validator_integrity.py            # verify (CI); exit 1 on drift
  python verify/check_validator_integrity.py --update    # re-pin after a reviewed change
"""
import hashlib
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(_HERE, "validator_manifest.json")

# The trusted closure: the gate and everything it imports to make a verdict.
# Editing ANY of these changes what "validated" means, so all are pinned.
TRUSTED = [
    "validate_candidate.py",     # the gate itself
    "qldpc_verify.py",           # the real verifier (schema/n/k/CSS/weight/witness)
    "heuristic_distance.py",     # the RIS distance search + refute_check
    "gf2.py",                    # the GF(2) core (rref/rank/kernel used above)
    "check_validator_integrity.py",  # this checker, pinned as its own tripwire
]


def _sha256(filename):
    with open(os.path.join(_HERE, filename), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def current_hashes():
    return {fn: _sha256(fn) for fn in TRUSTED}


def update():
    manifest = {
        "_comment": ("Pinned SHA-256 of the trusted autoresearch validation stack. "
                     "CI (check_validator_integrity.py) fails if any of these files "
                     "drifts from this pin. Re-pin deliberately with "
                     "`python verify/check_validator_integrity.py --update` and get "
                     "the diff reviewed."),
        "files": current_hashes(),
    }
    with open(MANIFEST, "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    print(f"re-pinned {len(TRUSTED)} files -> {os.path.relpath(MANIFEST, os.path.dirname(_HERE))}")
    return 0


def check():
    if not os.path.exists(MANIFEST):
        print(f"FAIL: no manifest at {MANIFEST}; run --update to create it")
        return 1
    pinned = json.load(open(MANIFEST)).get("files", {})
    cur = current_hashes()
    drift = []
    for fn in TRUSTED:
        if fn not in pinned:
            drift.append(f"{fn}: not pinned (new trusted file)")
        elif pinned[fn] != cur[fn]:
            drift.append(f"{fn}: changed (pinned {pinned[fn][:12]}..., now {cur[fn][:12]}...)")
    stale = [fn for fn in pinned if fn not in TRUSTED]
    for fn in stale:
        drift.append(f"{fn}: pinned but no longer in the trusted list")
    if drift:
        print("FAIL: the trusted validation stack drifted from its pin:")
        for d in drift:
            print(f"  - {d}")
        print("\nIf this change is intended, re-pin with "
              "`python verify/check_validator_integrity.py --update` and have the "
              "manifest diff reviewed (these files gate what the board accepts).")
        return 1
    print(f"ok: trusted validation stack matches the pin ({len(TRUSTED)} files)")
    return 0


def main(argv):
    if "--update" in argv:
        return update()
    return check()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
