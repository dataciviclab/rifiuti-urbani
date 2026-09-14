.PHONY: help download normalize run run-all run-compose preflight clean

YEAR_START ?= 2018
YEAR_END ?= 2024
YEARS = $(shell seq $(YEAR_START) $(YEAR_END))
YEARS_COMMA = $(shell echo $(YEARS) | tr ' ' ',')
PYTHON = python3

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Data acquisition ──────────────────────────────────────────────────────────

download: ## Download ISPRA data for all years (YEAR_START/YEAR_END)
	cd rifiuti-ispra-raw-2024 && ./download_multiyear.sh $(YEAR_START) $(YEAR_END)

# ── Normalization ─────────────────────────────────────────────────────────────

normalize: ## Normalize all raw CSVs
	$(PYTHON) scripts/normalize_ispra_all.py --batch --indir rifiuti-ispra-raw-2024/raw-$(YEAR_START) --outdir normalized/test 2>/dev/null || true
	@for year in $(YEARS); do \
		src="rifiuti-ispra-raw-2024/raw-$$year"; \
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
	rm -rf normalized/test

# ── Pipeline execution ────────────────────────────────────────────────────────

run: ## Run all datasets for current years
	@for ds in datasets/*/dataset.yml; do \
		name=$$(basename $$(dirname "$$ds")); \
		echo "▶ $$name ($(YEARS))"; \
		toolkit run --config "$$ds" --years $(YEARS_COMMA) || echo "  ✗ $$name failed"; \
	done

run-compose: ## Run compose unified
	toolkit run --config compose/rifiuti-urbani-unified/dataset.yml --years $(YEARS_COMMA)

run-all: run run-compose ## Run everything (datasets + compose)

run-%: ## Run single dataset: make run-ispra-ru-base
	toolkit run --config datasets/$*/dataset.yml --years $(YEARS_COMMA)

# ── Quality ───────────────────────────────────────────────────────────────────

preflight: ## Check all dataset configs
	@for ds in datasets/*/dataset.yml; do \
		name=$$(basename $$(dirname "$$ds")); \
		echo "🔍 $$name"; \
		toolkit inspect config --config "$$ds" 2>&1 | head -3; \
	done

status: ## Show pipeline status for all datasets
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

# --- Registry ---

.PHONY: registry registry-write
registry:
	$(TOOLKIT) registry build --prefix rifiuti-urbani

registry-write:
	$(TOOLKIT) registry build --prefix rifiuti-urbani --write

# ── Cleanup ───────────────────────────────────────────────────────────────────

clean: ## Remove all output
	rm -rf out/

clean-all: clean ## Remove output + normalized + raw downloads
	rm -rf normalized/ rifiuti-ispra-raw-2024/raw-*/

# ── Full pipeline ─────────────────────────────────────────────────────────────

pipeline: download normalize run-all ## Full pipeline: download → normalize → run
	@echo "✓ Pipeline complete"
