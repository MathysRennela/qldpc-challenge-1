"""Regression tests for the audit harness (``leader_audit.py``).

Two properties matter because the harness is allowed to gate a script and its
output can become a distance revision:

* a proposal that fails the independent GF(2) re-check can neither move the
  reading nor reach the witness file -- otherwise an accelerator bug could
  manufacture a refutation, which is the exact failure the re-check exists to
  prevent;
* the lightest witness seen so far is on disk before the ladder finishes, so a
  rung killed by a time limit does not cost a re-run.

The searches are stubbed throughout: these test the plumbing, not the codes.
They pass with or without the optional ``gf2_fast`` accelerator.
"""

import json
import os
import sys
import types

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

import leader_audit as la  # noqa: E402

ENTRY = os.path.join(_REPO, "codes", "72-12-6.json")


def _genuine_witness():
    """Find a real logical of the fixture entry, through the harness itself."""
    n, _k, HX, HZ, _doc = la.load_entry(ENTRY)
    weight, side, support, _dt = la.ris(HX, HZ, trials=2000, seed=1, threads=2)
    ok, why = la.validate_witness(n, HX, HZ, side, weight, support)
    assert ok, why
    return n, HX, HZ, weight, side, support


def _ladder_args(witness_out, ladder=((2000, [1]), (4000, [2]))):
    return types.SimpleNamespace(entry=ENTRY, ladder=list(ladder), threads=2, witness_out=str(witness_out))


def test_invalid_proposal_is_discarded(monkeypatch, tmp_path):
    """An unvalidated witness must not refute the claim or be written out."""
    monkeypatch.setattr(la, "ris", lambda *a, **k: (3, "X", [0, 1, 2], 0.0))
    out = tmp_path / "witness.json"
    rc = la.cmd_ladder(_ladder_args(out))
    assert rc == 0, "a bogus proposal was scored as a refutation"
    assert not out.exists(), "a bogus proposal reached the witness file"


def test_witness_written_on_every_new_best(monkeypatch, tmp_path):
    """The best-so-far survives a later rung that yields nothing usable."""
    n, HX, HZ, weight, side, support = _genuine_witness()
    seen = []

    def staged(HX_, HZ_, trials, seed, threads=8, pair_depth=10):
        seen.append(seed)
        if len(seen) == 1:
            return weight, side, support, 0.0
        return 2, "X", [0, 1], 0.0  # lighter, but not a logical

    monkeypatch.setattr(la, "ris", staged)
    out = tmp_path / "witness.json"
    rc = la.cmd_ladder(_ladder_args(out))
    assert rc == 0
    payload = json.loads(out.read_text())
    assert (payload["weight"], payload["side"], payload["support"]) == (weight, side, support)
    assert payload["seed"] == 1
    assert payload["claim"] == 6 and payload["verdict"] == "holds"

    # the written support is a witness, re-checked against the raw matrices
    ok, why = la.validate_witness(n, HX, HZ, payload["side"], payload["weight"], payload["support"])
    assert ok, why


def test_refutation_writes_witness_and_exits_two(monkeypatch, tmp_path):
    """Exit code 2 and a saved witness are the two artifacts a revision needs."""
    _n, _HX, _HZ, weight, side, support = _genuine_witness()
    real_load = la.load_entry

    def soft_claim(path):
        n, k, HX, HZ, doc = real_load(path)
        doc["distance"]["d"] = weight + 4  # pretend the board over-claims
        return n, k, HX, HZ, doc

    monkeypatch.setattr(la, "load_entry", soft_claim)
    monkeypatch.setattr(la, "ris", lambda *a, **k: (weight, side, support, 0.0))
    out = tmp_path / "witness.json"
    rc = la.cmd_ladder(_ladder_args(out, ladder=((2000, [1]),)))
    assert rc == 2
    assert json.loads(out.read_text())["verdict"] == "REFUTED"


def test_screen_keeps_one_witness_per_entry(monkeypatch, tmp_path):
    """A triage screen can also refute, so it saves its witnesses too."""
    _n, _HX, _HZ, weight, side, support = _genuine_witness()
    monkeypatch.setattr(la, "ris", lambda *a, **k: (weight, side, support, 0.0))
    witness_dir = tmp_path / "witnesses"
    args = types.SimpleNamespace(entries=[ENTRY], trials=2000, seeds=[1, 2], threads=2, witness_dir=str(witness_dir))
    assert la.cmd_screen(args) == 0
    payload = json.loads((witness_dir / "72-12-6.json").read_text())
    assert payload["weight"] == weight and payload["entry"] == ENTRY
