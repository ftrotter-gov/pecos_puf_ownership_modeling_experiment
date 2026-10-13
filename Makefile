# PECOS ownership pipeline and reports.
#
# Everything builds locally. There is no CI, by design: the site is built on
# your machine and pushed from your machine, so what you tested is what ships.
#
# Full path from raw CSVs to a published site:
#
#     make all        # data -> graph -> test -> sources -> site
#     make publish    # push the built site to GitHub Pages
#
# One-time setup:
#
#     python -m venv .venv && source .venv/bin/activate
#     pip install -r requirements.txt
#     cp example.env .env
#     make install

PYTHON ?= .venv/bin/python
NPM ?= npm

.DEFAULT_GOAL := help
.PHONY: help install patch patch-report patch-verify data graph test sources site serve publish publish-dry all clean

help:
	@echo "PECOS ownership reports"
	@echo
	@echo "  make install      Install the Evidence (node) dependencies"
	@echo "  make patch        Apply patched_data/ to the raw CSV"
	@echo "  make patch-report Apply the patch and explain every change"
	@echo "  make patch-verify Check the patched CSV against the rules"
	@echo "  make data         Build the hierarchy tables   (build_hierarchy.py)"
	@echo "  make graph        Resolve ultimate ownership   (build_ownership_graph.py)"
	@echo "  make test         Run the InLaw validation checks"
	@echo "  make sources      Extract DuckDB tables to parquet for the report"
	@echo "  make site         Build the static site into reports/build/"
	@echo "  make serve        Run the Evidence dev server with live reload"
	@echo "  make publish      Push the built site to GitHub Pages"
	@echo "  make publish-dry  Stage a publish without pushing"
	@echo "  make all          patch -> data -> graph -> test -> sources -> site"
	@echo "  make clean        Remove build output and extracted parquet"

install:
	cd reports && $(NPM) install

# Stage 0: correct the source data. All data-content fixes live in
# patched_data/owner_name_patch.yaml; nothing downstream edits data content.
patch:
	$(PYTHON) apply_data_patch.py

patch-report:
	$(PYTHON) apply_data_patch.py --report

patch-verify:
	$(PYTHON) apply_data_patch.py --verify

# Stage 1: the five-category hierarchy, reimplemented from the original R.
# Reads the PATCHED CSV by default.
data:
	$(PYTHON) build_hierarchy.py

# Stage 2: resolve ultimate ownership. Depends on stage 1 having written
# hospital_enrollments and hospital_allowners to the database.
graph:
	$(PYTHON) build_ownership_graph.py

test:
	.venv/bin/inlaw inlaw_tests

# Stage 3: run every sources/pecos/*.sql against DuckDB and write the results
# as parquet under reports/static/data. Only these results are published --
# never the database itself.
sources:
	cd reports && $(NPM) run sources

site:
	cd reports && $(NPM) run build

serve:
	cd reports && $(NPM) run dev

publish:
	$(PYTHON) publish_reports.py

publish-dry:
	$(PYTHON) publish_reports.py --dry-run

all: patch data graph test sources site
	@echo
	@echo "Built. Preview it with 'make serve', publish it with 'make publish'."

clean:
	rm -rf reports/build reports/.evidence reports/static/data
