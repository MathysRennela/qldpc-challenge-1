.PHONY: build verify example test test-fast

build:
	uv run python site/build.py

test:
	uv run --frozen python run_tests.py

test-fast:
	uv run --frozen python run_tests.py --skip-slow

verify:
	uv run python verify/qldpc_verify.py $(CODE)

example:
	uv run python verify/qldpc_verify.py examples/72-6-6.json
