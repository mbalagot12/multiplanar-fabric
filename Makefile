.PHONY: install generate build build-github build-custom serve clean deploy deploy-github deploy-custom

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

# Production URLs — override with: make build SITE_URL=<url>
# Or set the MKDOCS_SITE_URL repository variable in GitHub Actions.
GITHUB_PAGES_URL := https://mbalagot12.github.io/multiplanar-fabric/
CUSTOM_DOMAIN_URL := https://multiplanar.agentic24x7.net/
SITE_URL ?= $(CUSTOM_DOMAIN_URL)

install:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

generate:
	$(PYTHON) scripts/generate_pages.py

build: generate
	MKDOCS_SITE_URL=$(SITE_URL) $(PYTHON) -m mkdocs build --strict

build-github:
	$(MAKE) build SITE_URL=$(GITHUB_PAGES_URL)

build-custom:
	$(MAKE) build SITE_URL=$(CUSTOM_DOMAIN_URL)

serve: generate
	$(PYTHON) -m mkdocs serve --dev-addr 127.0.0.1:8000

clean:
	rm -rf site docs/generated/*.md
	find docs/assets -mindepth 1 ! -name '.gitkeep' -delete 2>/dev/null || true

deploy: build
	MKDOCS_SITE_URL=$(SITE_URL) $(PYTHON) -m mkdocs gh-deploy --force

deploy-github:
	$(MAKE) deploy SITE_URL=$(GITHUB_PAGES_URL)

deploy-custom:
	$(MAKE) deploy SITE_URL=$(CUSTOM_DOMAIN_URL)
