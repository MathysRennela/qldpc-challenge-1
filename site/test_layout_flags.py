"""Layout flags and diagnostics on the rendered site (issue #1846)."""

import copy
import importlib.util
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_site_build():
    spec = importlib.util.spec_from_file_location(
        "site_build_layout_flags", os.path.join(ROOT, "site", "build.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fixture():
    with open(os.path.join(ROOT, "verify", "fixtures", "72-6-6.json")) as f:
        return json.load(f)


def _build(tmp_path, docs):
    """Run the full build against a board holding the given documents."""
    build = load_site_build()
    codes = tmp_path / "codes"
    codes.mkdir()
    for slug, doc in docs.items():
        with open(codes / f"{slug}.json", "w") as f:
            json.dump(doc, f)
    build.ROOT = str(tmp_path)
    build.DOCS = str(tmp_path / "docs")
    build.CERTS = str(tmp_path / "certs")
    os.makedirs(os.path.join(build.DOCS, "codes"), exist_ok=True)
    build.build()
    return build


def _read(build, *parts):
    with open(os.path.join(build.DOCS, *parts)) as f:
        return f.read()


def test_modular_flag_and_diagnostics_render(tmp_path):
    plain = _fixture()
    modular = copy.deepcopy(plain)
    modular["schema_version"] = "0.3"
    modular["name"] = "modular copy"
    modular["locality"]["modules"] = [
        0 if c[1] < 3 else 1 for c in modular["locality"]["coordinates"]]
    build = _build(tmp_path, {"72-6-6": plain, "72-6-6-mod": modular})

    index = _read(build, "index.html")
    # exactly one row carries the chip and the search term; the tab appears
    assert index.count('class="tchip mod"') == 1
    assert 'data-q="modular"' in index
    assert "2 modules" in index

    page = _read(build, "codes", "72-6-6-mod.html")
    assert "<h3>Modular layout</h3>" in page
    assert "<b>modules</b> 2" in page
    assert "<b>max ports per module</b> 1" in page
    assert "cross-module checks" in page
    assert 'class=modtable' in page

    plain_page = _read(build, "codes", "72-6-6.html")
    assert "Modular layout" not in plain_page
    assert 'class="tchip mod"' not in plain_page


def test_modular_flag_leaves_scores_alone(tmp_path):
    plain = _fixture()
    modular = copy.deepcopy(plain)
    modular["schema_version"] = "0.3"
    modular["locality"]["modules"] = [3] * modular["n"]
    build = load_site_build()
    import sys
    sys.path.insert(0, os.path.join(ROOT, "verify"))
    import qldpc_verify
    a, b = qldpc_verify.verify(plain), qldpc_verify.verify(modular)
    assert a["computed"]["locality_class"] == b["computed"]["locality_class"]
    n, k, d = plain["n"], plain["k"], plain["distance"]["d"]
    assert (build.geo_score(plain, n, k, d, "x")
            == build.geo_score(modular, n, k, d, "x"))
