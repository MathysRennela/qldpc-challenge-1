.PHONY: build verify example test test-fast fast

build:
	uv run python site/build.py

# Optional C++ RIS accelerator (verify/gf2_fast.cpp); pure Python is the fallback.
fast:
	uv run --with pybind11 --with setuptools python verify/setup_gf2_fast.py \
	  build_ext --build-lib verify --build-temp build/gf2_fast

test:
	uv run --frozen python run_tests.py

test-fast:
	uv run --frozen python run_tests.py --skip-slow

verify:
	uv run python verify/qldpc_verify.py $(CODE)

example:
	uv run python verify/qldpc_verify.py examples/72-6-6.json
