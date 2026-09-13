.PHONY: lint test run clean preflight

lint:
	@echo "No Python code to lint"

test:
	@echo "No tests configured yet"

run:
	@for ds in datasets/*/dataset.yml; do \
		echo "Running $$ds..."; \
		toolkit run --config "$$ds" --years 2024 || true; \
	done

preflight:
	@for ds in datasets/*/dataset.yml; do \
		echo "Preflight $$ds..."; \
		toolkit inspect config --config "$$ds" || true; \
	done

clean:
	rm -rf out/
