PYTHON = python3

VENV      = venv
ACTIVATE := . $(VENV)/bin/activate

# Write a marker .install file to indicate that the dependencies have been
# installed.
INST := $(VENV)/.install
$(INST): requirements.txt
	$(PYTHON) -m venv $(VENV)
	$(ACTIVATE); pip install --upgrade pip
	$(ACTIVATE); pip install -r requirements.txt
	touch $@

.PHONY: install
install: $(INST)

.PHONY: clean
clean:
	rm -rf __pycache__ venv

.PHONY: fmt
fmt: install
	$(ACTIVATE); black ./

.PHONY: lint
lint: install
	$(ACTIVATE); pylint src/

.PHONY: types
types: install
	$(ACTIVATE); mypy src/ --strict

.PHONY: check
check: fmt lint types

.PHONY: test-unit
test-unit: install
	$(ACTIVATE); python -m pytest tests/unit

.PHONY: test-e2e
test-integration: install
	$(ACTIVATE); python -m pytest tests/integration

.PHONY: test-all
test-all: test-unit test-integration
