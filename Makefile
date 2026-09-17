# DataCivicLab — Rifiuti Urbani ISPRA
# Standard interface: make lint test pipeline run clean
# CLI toolkit del Lab. La memoria DuckDB è controllata da safe_connect
# (lab-connectors) via env DUCKDB_MEMORY_LIMIT (default 2GB).

TOOLKIT = toolkit
PYTHON  = python3

YEAR_START ?= 2018
YEAR_END   ?= 2024
YEARS       = $(shell seq $(YEAR_START) $(YEAR_END))
YEARS_COMMA = $(shell echo $(YEARS) | tr ' ' ',')

# --- Dataset discovery ------------------------------------------------------
DATASETS := $(shell find datasets -name dataset.yml 2>/dev/null | sort)
COMPOSE  := $(shell find compose -name dataset.yml 2>/dev/null | sort)

# --- Standard interface (ADR-001, workflows.md) ------------------------------

.PHONY: lint
lint:
	ruff check .

.PHONY: test
test:
	python -m pytest tests/ -v

.PHONY: check
check:
	@for f in $(DATASETS) $(COMPOSE); do \
		echo "→ $$f"; \
		$(TOOLKIT) run preflight --config "$$f" > /dev/null 2>&1 || exit 1; \
	done
	@echo "✅ All configs valid"

.PHONY: run
run:
	@for f in $(DATASETS); do \
		echo "=== $$f ==="; \
		$(TOOLKIT) run --config "$$f" --years $(YEARS_COMMA) || exit 1; \
	done

.PHONY: run-compose
run-compose:
	@for f in $(COMPOSE); do \
		echo "=== $$f ==="; \
		$(TOOLKIT) run --config "$$f" --years $(YEARS_COMMA) || exit 1; \
	done

.PHONY: run-all
run-all: run run-compose

.PHONY: pipeline
pipeline: lint test run-all
	@echo "✅ Pipeline complete"

# --- Single dataset runner ---------------------------------------------------

.PHONY: run-%
run-%:
	$(TOOLKIT) run --config datasets/$*/dataset.yml --years $(YEARS_COMMA)

# --- Data acquisition (ISPRA-specific) ---------------------------------------

.PHONY: download
download:
	cd rifiuti-ispra-raw && ./download_multiyear.sh $(YEAR_START) $(YEAR_END)

.PHONY: normalize
normalize:
	@for year in $(YEARS); do \
		src="rifiuti-ispra-raw/raw-$$year"; \
		[ -d "$$src" ] || continue; \
		echo "Normalizing $$year..."; \
		[ -f "$$src/costi_procapite.csv" ] && $(PYTHON) scripts/normalize_ispra_all.py -i "$$src/costi_procapite.csv" -o "normalized/costi_procapite/ispra_costi_pc_$$year.csv" -t costi -y $$year 2>/dev/null; \
		[ -f "$$src/costi_kg.csv" ] && $(PYTHON) scripts/normalize_ispra_all.py -i "$$src/costi_kg.csv" -o "normalized/costi_kg/ispra_costi_kg_$$year.csv" -t costi -y $$year 2>/dev/null; \
		[ -f "$$src/ru_flussi.csv" ] && $(PYTHON) scripts/normalize_ispra_all.py -i "$$src/ru_flussi.csv" -o "normalized/flussi/ispra_ru_flussi_$$year.csv" -t auto -y $$year 2>/dev/null; \
		[ -f "$$src/ru_import.csv" ] && $(PYTHON) scripts/normalize_ispra_all.py -i "$$src/ru_import.csv" -o "normalized/ru_import/ispra_ru_import_$$year.csv" -t auto -y $$year 2>/dev/null; \
		[ -f "$$src/ru_export.csv" ] && $(PYTHON) scripts/normalize_ispra_all.py -i "$$src/ru_export.csv" -o "normalized/ru_export/ispra_ru_export_$$year.csv" -t auto -y $$year 2>/dev/null; \
		[ -f "$$src/ru_gestione.csv" ] && $(PYTHON) scripts/normalize_ispra_all.py -i "$$src/ru_gestione.csv" -o "normalized/ru_gestione/ispra_ru_gestione_$$year.csv" -t auto -y $$year 2>/dev/null; \
		[ -f "$$src/rs_import.csv" ] && $(PYTHON) scripts/normalize_ispra_all.py -i "$$src/rs_import.csv" -o "normalized/rs_import/ispra_rs_import_$$year.csv" -t auto -y $$year 2>/dev/null; \
		[ -f "$$src/rs_export.csv" ] && $(PYTHON) scripts/normalize_ispra_all.py -i "$$src/rs_export.csv" -o "normalized/rs_export/ispra_rs_export_$$year.csv" -t auto -y $$year 2>/dev/null; \
		[ -f "$$src/rs_produzione.csv" ] && $(PYTHON) scripts/normalize_ispra_all.py -i "$$src/rs_produzione.csv" -o "normalized/rs_produzione/ispra_rs_produzione_$$year.csv" -t auto -y $$year 2>/dev/null; \
		[ -f "$$src/rs_gestione.csv" ] && $(PYTHON) scripts/normalize_ispra_all.py -i "$$src/rs_gestione.csv" -o "normalized/rs_gestione/ispra_rs_gestione_$$year.csv" -t auto -y $$year 2>/dev/null; \
		[ -f "$$src/rs_impianti.csv" ] && $(PYTHON) scripts/normalize_ispra_all.py -i "$$src/rs_impianti.csv" -o "normalized/rs_impianti/ispra_rs_impianti_$$year.csv" -t auto -y $$year 2>/dev/null; \
	done

# --- Status / diagnostics ----------------------------------------------------

.PHONY: status
status:
	@echo "=== Pipeline Status ==="
	@for ds in datasets/*/; do \
		name=$$(basename "$$ds"); \
		last_run=$$(ls -t out/data/_runs/$$name/*/ 2>/dev/null | head -1); \
		if [ -n "$$last_run" ]; then \
			status=$$(cat "out/data/_runs/$$name/$$last_run"/*.json 2>/dev/null | $(PYTHON) -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','?'))" 2>/dev/null || echo "?"); \
			echo "  $$name: $$status"; \
		else \
			echo "  $$name: no runs"; \
		fi \
	done

# --- Registry ---------------------------------------------------------------

.PHONY: registry registry-write
registry:
	$(TOOLKIT) registry build --prefix rifiuti-urbani

registry-write:
	$(TOOLKIT) registry build --prefix rifiuti-urbani --write

# --- Cleanup ----------------------------------------------------------------

.PHONY: clean
clean:
	rm -rf out/data/_runs out/data/probe out/data/raw out/data/clean out/data/mart out/data/cross .tmp/

.PHONY: clean-runs
clean-runs:
	rm -rf out/data/_runs/

.PHONY: clean-all
clean-all: clean
	rm -rf normalized/ rifiuti-ispra-raw/raw-*/

# --- Help -------------------------------------------------------------------

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
