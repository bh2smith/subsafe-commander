

.PHONY: clean
clean:
	rm -rf __pycache__ venv

.PHONY: fmt
fmt:
	black ./

.PHONY: lint
lint:
	pylint src/

.PHONY: types
types:
	mypy src/ --strict

.PHONY: check
check: fmt lint types

.PHONY: test-unit
test-unit:
	python -m pytest tests/unit

.PHONY: test-e2e
test-integration:
	python -m pytest tests/integration

.PHONY: test-all
test-all: test-unit test-integration
