.PHONY: install generate build serve clean deploy

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

install:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

generate:
	$(PYTHON) scripts/generate_pages.py

build: generate
	$(PYTHON) -m mkdocs build --strict

serve: generate
	$(PYTHON) -m mkdocs serve --dev-addr 127.0.0.1:8000

clean:
	rm -rf site docs/generated/*.md
	find docs/assets -mindepth 1 ! -name '.gitkeep' -delete 2>/dev/null || true

deploy: build
	$(PYTHON) -m mkdocs gh-deploy --force
