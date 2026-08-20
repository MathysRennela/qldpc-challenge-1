"""Tests for verify/check_prose.py.

Fixtures are synthetic (written to a temp tree) so the suite does not depend on
which notes happen to be on the board; the last case pins the one behaviour that
must hold against the real repo -- a note citing an attributed external artifact
passes, and a note citing gitignored working output does not.
"""
import os
import subprocess
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_HERE)
import check_prose

FAILURES = []


def check(name, ok, detail=""):
    print(("PASS" if ok else "FAIL"), name, detail)
    if not ok:
        FAILURES.append(name)


def problems_for(text, root, slug=None):
    out = []
    check_prose.check_text(text, "t.md", root, out, is_note_slug=slug)
    return [why for _, why, _ in out]


def main():
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "research", "kit"))
        open(os.path.join(tmp, "research", "kit", "group_algebra.py"), "w").close()

        check("path that exists resolves",
              problems_for("built with `research/kit/group_algebra.py`", tmp) == [])

        check("module.function form resolves",
              problems_for("call `research/kit/group_algebra.build_2bga`", tmp) == [])

        check("file::symbol form resolves",
              problems_for("see `research/kit/group_algebra.py::build_2bga`", tmp) == [])

        check("pinned external artifact passes",
              problems_for(
                  "taken from github.com/a7b/yarn @ 82fb695, "
                  "`processor_codes/mitten/Hx.npy`", tmp) == [])

        missing = ["path does not exist in this tree"]
        rejected_external_citations = (
            ("missing path is caught",
             "MILP via `evaluation/distance_milp.py`"),
            ("unpinned external source does not exempt a missing path",
             "From https://github.com/qiskit-community/qcode-discovery, "
             "use `evaluation/distance_milp.py`."),
            ("unrelated URL and SHA do not form a pinned source",
             "From https://example.com @ 82fb695, use `vendor/tool.py`."),
            ("lookalike GitHub host does not form a pinned source",
             "From https://evilgithub.com/a7b/yarn @ 82fb695, "
             "use `vendor/tool.py`."),
            ("GitHub-looking URL path does not form a pinned source",
             "From https://example.com/github.com/a7b/yarn @ 82fb695, "
             "use `vendor/tool.py`."),
            ("GitHub-looking query value does not form a pinned source",
             "From https://example.com/?next=github.com/a7b/yarn @ 82fb695, "
             "use `vendor/tool.py`."),
            ("Markdown delimiter inside a URL does not start a source",
             "From https://example.com/?next=|github.com/a7b/yarn @ 82fb695, "
             "use `vendor/tool.py`."),
            ("SHA prefix in a longer revision does not count as a pin",
             "From github.com/a7b/yarn @ deadbee-main, use `vendor/tool.py`."),
            ("unrelated URL elsewhere does not exempt a missing path",
             "Reference: https://arxiv.org/abs/2607.28795\n\n"
             "Built with `evaluation/distance_milp.py`."),
            ("unrelated URL in the same paragraph does not exempt a path",
             "Reference https://arxiv.org/abs/2607.28795; local helper "
             "`evaluation/distance_milp.py`."),
            ("pinned source elsewhere does not exempt a missing path",
             "Source: github.com/a7b/yarn @ 82fb695.\n\n"
             "Built with `evaluation/distance_milp.py`."),
            ("pinned source in an earlier clause does not exempt a path",
             "Source github.com/a7b/yarn @ 82fb695; local helper "
             "`evaluation/distance_milp.py`."),
            ("DOI sentence punctuation ends its citation",
             "Source https://doi.org/10.1234/example. Local helper "
             "`evaluation/distance_milp.py`."),
            ("pinned citation exempts only its own paragraph",
             "From github.com/a7b/yarn @ 82fb695, `vendor/tool.py`.\n\n"
             "Local helper: `evaluation/distance_milp.py`."),
            ("source after a path does not retroactively exempt it",
             "Used `vendor/tool.py` from github.com/a7b/yarn @ 82fb695."),
            ("same path is rechecked outside its pinned citation",
             "From github.com/a7b/yarn @ 82fb695, `vendor/tool.py`.\n\n"
             "Local helper: `vendor/tool.py`."),
            ("pinned citation does not leak to another list item",
             "- From github.com/a7b/yarn @ 82fb695: `vendor/tool.py`\n"
             "- Local helper: `evaluation/distance_milp.py`"),
            ("pinned citation does not leak between blockquoted bullets",
             "> - From github.com/a7b/yarn @ 82fb695: `vendor/tool.py`\n"
             "> - Local helper: `evaluation/distance_milp.py`"),
            ("pinned citation does not cross a blockquote blank line",
             "> Source github.com/a7b/yarn @ 82fb695:\n>\n"
             "> `evaluation/distance_milp.py`"),
            ("pinned citation does not leak between table rows",
             "| source | github.com/a7b/yarn @ 82fb695 | `vendor/tool.py` |\n"
             "| local | none | `evaluation/distance_milp.py` |"),
            ("pinned citation does not leak in a table without leading pipes",
             "source | github.com/a7b/yarn @ 82fb695 | `vendor/tool.py`\n"
             "local | none | `evaluation/distance_milp.py`"),
        )
        for name, text in rejected_external_citations:
            check(name, problems_for(text, tmp) == missing)

        check("path-like text inside a full URL is not a repo path",
              problems_for(
                  "See https://github.com/a7b/yarn/blob/82fb695/tools/build.py",
                  tmp) == [])

        check("gitignored dir is caught even with an external source named",
              problems_for(
                  "evidence in `research/candidates/run1/` see https://example.com",
                  tmp) == ["gitignored working output cited as evidence"])

        check("absolute local path is caught",
              "absolute local path"
              in problems_for("ran /Users/me/scratch/search.py", tmp))

        check("session URL is caught",
              "session URL" in problems_for(
                  "https://claude.ai/code/session_01ABC", tmp))

        check("scaffolding is caught",
              "leftover scaffolding" in problems_for(
                  "Drafted by `qldpc submit`; edit before requesting review.", tmp))

        check("unticked checkbox is caught",
              "leftover scaffolding" in problems_for("- [ ] verified", tmp))

        check("arXiv id is not treated as a path",
              problems_for("see quant-ph/9601029 for the original", tmp) == [])

        check("placeholder path is not treated as a path",
              problems_for("writes `codes/<n>-<k>-<d>.json`", tmp) == [])

        check("note slug mismatch is caught",
              "note's first [[n,k,d]] disagrees with its filename"
              in problems_for("# [[270,54,12]] code", tmp, slug=("270", "54", "10")))

        check("note with no params is caught",
              "note states no [[n,k,d]]"
              in problems_for("A note with no parameters.", tmp,
                              slug=("482", "146", "42")))

        check("matching note slug passes",
              problems_for("# [[270,54,10]] code", tmp, slug=("270", "54", "10"))
              == [])

    # Against the real tree: the two behaviours the check exists to distinguish.
    real = os.path.join(ROOT, "notes", "300-60-14.md")
    if os.path.exists(real):
        r = subprocess.run([sys.executable, os.path.join(_HERE, "check_prose.py"),
                            "--files", "notes/300-60-14.md"],
                           cwd=ROOT, capture_output=True, text=True)
        check("real note with a pinned external artifact passes",
              r.returncode == 0, r.stdout.strip().splitlines()[-1:] or "")

    real = os.path.join(ROOT, "notes", "700-75-3.md")
    if os.path.exists(real):
        r = subprocess.run([sys.executable, os.path.join(_HERE, "check_prose.py"),
                            "--files", "notes/700-75-3.md"],
                           cwd=ROOT, capture_output=True, text=True)
        check("real note citing research/candidates/ fails", r.returncode == 1)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s): {', '.join(FAILURES)}")
        return 1
    print("all prose checks pass")
    return 0


def test_main():
    """pytest entry point; the suite body lives in main()."""
    assert main() == 0


if __name__ == "__main__":
    sys.exit(main())
