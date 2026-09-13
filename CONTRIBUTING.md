# Contributing

Questo è un dataset repo nel DataCivicLab workspace.

## Struttura

```
datasets/<slug>/
├── dataset.yml          # Contratto pipeline
├── sql/
│   ├── clean.sql        # Pulizia, typing, normalizzazione
│   └── mart*.sql        # Aggregazioni analitiche
```

## Convenzioni

- **Slug**: `snake_case` dal nome fonte
- **SQL**: usa macro toolkit (`normalize_string`, `normalize_italian_number`, `cast_bigint`)
- **Mart**: legge solo da `clean_input`, contiene aggregazioni/benchmark
- **Validazione**: `primary_key`, `not_null`, `min_rows` obbligatori

## Esecuzione

```bash
toolkit run --config datasets/<slug>/dataset.yml --years 2024
```
