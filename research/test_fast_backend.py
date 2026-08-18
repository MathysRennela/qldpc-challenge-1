"""Regression tests for the optional accelerated research backend."""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "kit"))
sys.path.insert(0, os.path.join(_HERE, "..", "verify"))

from bb import build_bb, KNOWN
import surrogate
from surrogate import distance_rand
from search import screen, sample_bb

try:
    import gf2_fast
except ImportError:
    gf2_fast = None


def main():
    p = KNOWN["[[72,12,6]]"]
    HX, HZ = build_bb(p["l"], p["m"], p["A"], p["B"])

    assert distance_rand(HX, HZ, trials=100, seed=0, backend="numpy") == 6
    assert distance_rand(HX, HZ, trials=100, seed=0, backend="auto") == 6

    try:
        distance_rand(HX, HZ, trials=1, backend="invalid")
    except ValueError:
        pass
    else:
        raise AssertionError("invalid backend was accepted")

    class NoLogicalBackend:
        @staticmethod
        def distance_rand_witness(*args, **kwargs):
            return HX.shape[1] + 1, "", []

    original_backend = surrogate._fast
    surrogate._fast = NoLogicalBackend()
    try:
        assert distance_rand(HX, HZ, trials=1, backend="fast") == float("inf")
    finally:
        surrogate._fast = original_backend

    if gf2_fast is not None:
        assert distance_rand(
            HX, HZ, trials=100, seed=0, backend="fast", threads=2) == 6
        records = screen(
            sample_bb(4, seed=1), min_k=2, min_d=2, trials=20,
            backend="fast", threads=2)
        assert records
    else:
        try:
            distance_rand(HX, HZ, trials=1, backend="fast")
        except ImportError:
            pass
        else:
            raise AssertionError("explicit fast backend did not report missing extension")

    print("PASS: optional fast backend and NumPy fallback")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
