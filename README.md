# ispra-catasto-rifiuti

**Domanda guida:** Quali sono le dinamiche di produzione, gestione e movimentazione dei rifiuti urbani e speciali in Italia?

**Fonte:** [Catasto Nazionale Rifiuti ISPRA](https://www.catasto-rifiuti.isprambiente.it/)
**Formato:** CSV (download HTTP + normalizzazione Python)
**Granularità:** comunale (RU), regionale (RS, flussi, import/export)
**Copertura:** 2010–2024

## Dataset

| Dataset | Livello | Anni | Source |
|---|---|---|---|
| `ispra-ru-base` | Comunale | 2010–2024 | http_file |
| `ispra-ru-costi-procapite` | Comunale | 2018–2024 | local_file (normalizzato) |
| `ispra-ru-costi-kg` | Comunale | 2018–2024 | local_file (normalizzato) |
| `ispra-ru-flussi` | Regionale | 2024 | local_file |
| `ispra-ru-import` | Regionale | 2024 | local_file |
| `ispra-ru-export` | Regionale | 2024 | local_file |
| `ispra-ru-gestione` | Nazionale | 2024 | local_file |
| `ispra-rs-import` | Regionale | 2024 | local_file |
| `ispra-rs-export` | Regionale | 2018–2024 | local_file (normalizzato) |
| `ispra-rs-produzione` | Nazionale | 2024 | local_file |
| `ispra-rs-gestione` | Nazionale | 2024 | local_file |
| `ispra-rs-impianti` | Nazionale | 2024 | local_file |

**Compose:** `rifiuti-urbani-unified` — JOIN ru-base + costi procapite + costi kg (2018–2024)

## Struttura

```
datasets/          12 dataset con dataset.yml + sql/
compose/           rifiuti-urbani-unified
normalized/        CSV normalizzati (costi, rs-export)
scripts/           normalize_ispra_all.py
```

## Esecuzione

```bash
# Normalizza CSV ISPRA
python scripts/normalize_ispra_all.py --input raw.csv --output clean.csv --type costi

# Run singolo dataset
toolkit run --config datasets/ispra-ru-base/dataset.yml --years 2024

# Run tutti gli anni
toolkit run --config datasets/ispra-ru-costi-procapite/dataset.yml --years 2018,2019,2020,2021,2022,2023,2024

# Compose multi-year
toolkit run --config compose/rifiuti-urbani-unified/dataset.yml --years 2018,2019,2020,2021,2022,2023,2024
```

## Note

I CSV ISPRA sono multi-sezione con formati variabili tra anni. `scripts/normalize_ispra_all.py` li normalizza in un formato uniforme prima del pipeline toolkit.
