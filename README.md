# ispra-catasto-rifiuti

**Domanda guida:** Quali sono le dinamiche di produzione, gestione e movimentazione dei rifiuti urbani e speciali in Italia?

**Fonte:** [Catasto Nazionale Rifiuti ISPRA](https://www.catasto-rifiuti.isprambiente.it/)
**Formato:** CSV (download diretto HTTP + normalizzazione multi-sezione)
**Granularità:** comunale (RU), regionale (RS, flussi, import/export)
**Copertura:** 2010–2024

## Dataset

| Dataset | Livello | Copertura | Mart |
|---|---|---|---|
| `ispra-ru-base` | Comunale | 2010–2024 | 3 (comuni, sintesi, trend) |
| `ispra-ru-costi-procapite` | Comunale | 2020–2024 | 1 (benchmark) |
| `ispra-ru-costi-kg` | Comunale | 2020–2024 | 1 (benchmark) |
| `ispra-ru-flussi` | Regionale | 2018–2024 | 1 |
| `ispra-ru-import` | Regionale | 2018–2024 | 1 |
| `ispra-ru-export` | Regionale | 2018–2024 | 1 |
| `ispra-ru-gestione` | Nazionale | 2015–2024 | 1 |
| `ispra-rs-import` | Regionale | 2018–2024 | 1 |
| `ispra-rs-export` | Regionale | 2018–2024 | 1 |
| `ispra-rs-produzione` | Nazionale | 2014–2024 | 1 |
| `ispra-rs-gestione` | Nazionale | 2014–2024 | 1 |
| `ispra-rs-impianti` | Nazionale | 2018–2024 | 1 |

## Esecuzione

```bash
# Run singolo dataset
toolkit run --config datasets/ispra-ru-base/dataset.yml --years 2024

# Run tutti
make run
```

## Note

I CSV ISPRA multi-sezione (produzione, gestione, impianti) richiedono normalizzazione pre-processing tramite `scripts/normalize_ispra.py`. I CSV semplici (import/export, flussi) sono letti direttamente dal toolkit.
