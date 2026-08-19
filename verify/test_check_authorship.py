"""Tests for check_authorship.py, including the refutation binding (#611).

Builds a throwaway git repo, commits a code owned by @alice, then checks which
edits @bob can and cannot land: a clean refutation (rename + strictly lighter
witness credited to him in witness_provenance) binds; anything that also
touches the construction, authorship, or credit does not. The gate does no
code math, so the fixture code is synthetic.
"""

import copy
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_authorship

BASE_DOC = {
    "schema_version": "0.1",
    "name": "[[60,8,6]] synthetic test code",
    "code_type": "CSS",
    "n": 60, "k": 8,
    "checks": {"X": [[0, 1, 2]], "Z": [[3, 4, 5]]},
    "distance": {
        "d": 6,
        "X": {"value": 6, "confidence": "upper_bound",
              "witness": [0, 1, 2, 3, 4, 5]},
        "Z": {"value": 7, "confidence": "upper_bound",
              "witness": [0, 1, 2, 3, 4, 5, 6]},
    },
    "provenance": {"authors": ["@alice"], "construction": "synthetic",
                   "notes": "original."},
}

_fail = []


def check(name, cond):
    print(f"  {'ok  ' if cond else 'FAIL'}  {name}")
    if not cond:
        _fail.append(name)


def git(td, *args):
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    *args], cwd=td, check=True, capture_output=True)


def write_code(td, fname, doc):
    os.makedirs(os.path.join(td, "codes"), exist_ok=True)
    with open(os.path.join(td, "codes", fname), "w") as f:
        json.dump(doc, f)


def make_repo(td):
    git(td, "init", "-q", "-b", "main")
    write_code(td, "60-8-6.json", BASE_DOC)
    git(td, "add", "codes")
    git(td, "commit", "-q", "-m", "base")
    git(td, "checkout", "-q", "-b", "change")


def refuted(with_wp=True, found_by="@bob"):
    doc = copy.deepcopy(BASE_DOC)
    doc["name"] = "[[60,8,5]] synthetic test code"
    doc["schema_version"] = "0.2"
    doc["distance"]["X"] = {"value": 5, "confidence": "upper_bound",
                            "witness": [0, 1, 2, 3, 4]}
    if with_wp:
        doc["distance"]["X"]["witness_provenance"] = {
            "found_by": [found_by], "date": "2026-08-19", "found_at_samples": 10 ** 9}
    doc["distance"]["d"] = 5
    doc["provenance"]["notes"] += " Refuted."
    return doc


def run_case(name, edit, expect_ok, author="bob", rename=True):
    with tempfile.TemporaryDirectory() as td:
        make_repo(td)
        doc = edit()
        if rename:
            git(td, "rm", "-q", "codes/60-8-6.json")
            write_code(td, "60-8-5.json", doc)
        else:
            write_code(td, "60-8-6.json", doc)
        git(td, "add", "codes")
        git(td, "commit", "-q", "-m", "change")
        rc = check_authorship.main(
            ["--author", author, "--root", td, "--base", "main"])
        check(name, (rc == 0) == expect_ok)


def main():
    print("refutation binding (issue #611):")
    run_case("clean refutation by @bob binds", refuted, True)
    run_case("in-place (no rename) refutation binds",
             refuted, True, rename=False)
    run_case("owner @alice still binds via authors",
             refuted, True, author="alice")

    def no_wp():
        return refuted(with_wp=False)
    run_case("lighter witness without witness_provenance rejected",
             no_wp, False)

    def wrong_credit():
        return refuted(found_by="@carol")
    run_case("witness_provenance crediting someone else rejected",
             wrong_credit, False)

    def touches_checks():
        doc = refuted()
        doc["checks"]["X"] = [[0, 1, 3]]
        return doc
    run_case("refutation that also edits checks rejected", touches_checks,
             False)

    def appends_author():
        doc = refuted()
        doc["provenance"]["authors"].append("@bob")
        return doc
    run_case("refutation that also appends to authors rejected",
             appends_author, False)

    def swaps_author():
        doc = copy.deepcopy(BASE_DOC)
        doc["provenance"]["authors"] = ["@bob"]
        return doc
    run_case("author swap on someone else's code rejected", swaps_author,
             False, rename=False)

    def owner_adds_coauthor():
        doc = copy.deepcopy(BASE_DOC)
        doc["provenance"]["authors"] = ["@alice", "@carol"]
        return doc
    run_case("existing author may edit the author list",
             owner_adds_coauthor, True, author="alice", rename=False)

    def rewrites_notes():
        doc = refuted()
        doc["provenance"]["notes"] = "Mine now."
        return doc
    run_case("refutation that rewrites notes rejected", rewrites_notes, False)

    def loosens():
        doc = refuted()
        doc["distance"]["X"]["value"] = 8
        doc["distance"]["X"]["witness"] = list(range(8))
        doc["distance"]["d"] = 7
        doc["name"] = BASE_DOC["name"]
        return doc
    run_case("loosened bound rejected (no strict decrease)", loosens, False)

    def stamp_only():
        doc = copy.deepcopy(BASE_DOC)
        doc["schema_version"] = "0.2"
        doc["distance"]["X"]["witness_provenance"] = {
            "found_by": ["@bob"], "date": "2026-08-19", "found_at_samples": 10 ** 9}
        return doc
    run_case("survival stamp alone does not grant edit rights", stamp_only,
             False, rename=False)

    def stamp_riding_along():
        doc = refuted()
        doc["distance"]["Z"]["witness_provenance"] = {
            "found_by": ["@bob"], "date": "2026-08-19", "found_at_samples": 10 ** 9}
        return doc
    run_case("survival stamp riding on a real refutation binds",
             stamp_riding_along, True)

    print("\nplain submissions (original binding):")
    def new_code():
        return copy.deepcopy(BASE_DOC)
    with tempfile.TemporaryDirectory() as td:
        make_repo(td)
        write_code(td, "61-9-6.json", new_code())
        git(td, "add", "codes")
        git(td, "commit", "-q", "-m", "new")
        rc = check_authorship.main(
            ["--author", "bob", "--root", td, "--base", "main"])
        check("new code by non-author still rejected", rc == 1)
        rc = check_authorship.main(
            ["--author", "alice", "--root", td, "--base", "main"])
        check("new code by its author still accepted", rc == 0)

    print()
    if _fail:
        print(f"FAILED: {_fail}")
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
