"""Tests for the locality-track score f (issue #168)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import locality_score as ls


def test_surface_code_calibrates_to_one():
    # The rotated surface code scores exactly f = 1 at every distance.
    for d in (3, 5, 9, 25, 51):
        n, k, coords, supports = ls._surface_code_layout(d)
        w = ls.box_range(coords, supports)
        assert w == 2, (d, w)
        assert abs(ls.score(n, k, d, 2, w) - 1.0) < 1e-9


def test_ceiling_matches_theorem():
    # g(2) = 2*1*8^2 = 128; ceiling(2) = 1024*128 = 2^17.
    assert abs(ls.g(2) - 128.0) < 1e-9
    assert abs(ls.ceiling(2) - 2 ** 17) < 1e-6


def test_score_is_scale_free_on_a_saturating_family():
    # A family with k ~ n and d fixed (block-diagonal tiling) has constant f:
    # doubling n and k leaves f untouched.
    f1 = ls.score(n=1000, k=100, d=8, D=2, w=4)
    f2 = ls.score(n=2000, k=200, d=8, D=2, w=4)
    assert abs(f1 - f2) < 1e-9


def test_score_decreases_in_w():
    a = ls.score(n=400, k=8, d=12, D=2, w=3)
    b = ls.score(n=400, k=8, d=12, D=2, w=6)
    assert a > b > 0


def test_box_range_counts_sites_not_distance():
    # Three collinear qubits at x = 0,1,2 span two steps -> a 3-site box.
    coords = [(0, 0), (1, 0), (2, 0), (0, 1)]
    assert ls.box_range(coords, [[0, 1, 2]]) == 3
    # A single 2x2 plaquette spans one step per axis -> a 2-site box.
    assert ls.box_range(coords, [[0, 1, 3]]) == 2


def test_unrestricted_has_no_score():
    assert ls.dimension_of_class("unrestricted") is None
    assert ls.score_from_computed(390, 82, 30,
                                  {"locality_class": "unrestricted"}) is None


def test_score_from_computed_roundtrip():
    comp = {"locality_class": "local-2d-bilayer", "locality": {"box_range": 2}}
    out = ls.score_from_computed(9, 1, 3, comp)
    assert out["D"] == 2 and out["w"] == 2
    assert abs(out["f"] - 1.0) < 1e-6
    assert out["ceiling_version"] == "v1"


def test_evaluate_embedding_scores_surface_plaquette():
    n, k, coords, supports = ls._surface_code_layout(5)
    ev = ls.evaluate_embedding(n, k, 5, coords, supports, layers=1)
    assert ev["valid"] and ev["D"] == 2 and ev["w"] == 2
    assert abs(ev["f"] - 1.0) < 1e-9


def test_evaluate_embedding_rejects_crammed_layout():
    # Two qubits on the same site with layers=1 is cramming -> not scorable.
    coords = [(0, 0), (0, 0), (1, 0), (1, 1)]
    ev = ls.evaluate_embedding(4, 1, 3, coords, [[0, 1, 2, 3]], layers=1)
    assert ev["valid"] is False and "cram" in ev["reason"]
    # With two declared layers the same layout is honest again.
    ev2 = ls.evaluate_embedding(4, 1, 3, coords, [[0, 1, 2, 3]], layers=2)
    assert ev2["valid"] is True


def test_best_over_embeddings_takes_the_max():
    supports = [[0, 1, 2, 3]]
    tight = [(0, 0), (1, 0), (0, 1), (1, 1)]          # span 1/axis -> w=2
    loose = [(0, 0), (2, 0), (0, 1), (1, 1)]          # x-span 2   -> w=3
    embs = [(loose, 1, "alt_embeddings[0]", supports),
            (tight, 1, "locality", supports)]
    best = ls.best_over_embeddings(4, 1, 3, embs)
    assert best["w"] == 2 and best["source"] == "locality"
    assert best["n_embeddings"] == 2
    # The tight embedding must out-score the loose one.
    assert best["f"] == ls.evaluate_embedding(4, 1, 3, tight, supports)["f"]


def test_best_over_embeddings_none_when_all_crammed():
    crammed = [(0, 0), (0, 0)]
    assert ls.best_over_embeddings(
        2, 1, 2, [(crammed, 1, "locality", [[0, 1]])]) is None


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ok  {name}")
    print("PASS")
