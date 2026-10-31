# Rifiuti Urbani Italia

**Domanda guida:** Quali sono le dinamiche di produzione, gestione e movimentazione dei rifiuti urbani e speciali in Italia?

**Fonte:** [Catasto Nazionale Rifiuti ISPRA](https://www.catasto-rifiuti.isprambiente.it/)
**Granularita:** comunale (RU), regionale (RS flussi import/export), nazionale (RS produzione gestione)
**Copertura:** 2010–2024 (per dataset: vedi tabella)

## Unità di rilevazione

I dati RU comunali hanno **due tipi di unità**, distinte dalla colonna `tipo_dato`:

- `Comune` — il comune riporta i propri dati;
- `Aggregazione` — ISPRA attribuisce i dati di più comuni a un'unione
  (`Aggregazione: <nome>`); i comuni aderenti (`Vedi aggregazione`) non hanno
  dati propri. La `popolazione` dell'unità è capofila + aderenti, così i
  pro-capite restano corretti.

Senza questo, la Valle d'Aosta nel 2024 sarebbe rappresentata dal solo comune
di Aosta (RD 78,6%) invece che dall'intera regione (71,7%, dato ISPRA).
Nei dataset regionali `ru_import`/`ru_export`/`rs_import`/`rs_export`/`ru_flussi`
la fonte include una riga di totale `Italia`: è marcata con `is_aggregato` ed
esclusa dai mart, per non raddoppiare i totali.

## Dataset

| Slug | Livello | Anni | Tipo raw |
|---|---|---|---|
| `ispra_ru_base` | Comunale | 2010–2024 | http_file |
| `ispra_ru_costi_procapite` | Comunale | 2018–2024 | local_file |
| `ispra_ru_costi_kg` | Comunale | 2018–2024 | local_file |
| `ispra_ru_flussi` | Regionale | 2018–2024 | local_file |
| `ispra_ru_gestione` | Nazionale | 2015–2024 | local_file |
| `ispra_ru_export` | Regionale | 2018–2024 | local_file |
| `ispra_ru_import` | Regionale | 2018–2024 | local_file |
| `ispra_rs_produzione` | Nazionale | 2014–2024 | local_file |
| `ispra_rs_gestione` | Nazionale | 2014–2024 | local_file |
| `ispra_rs_import` | Regionale | 2018–2024 | local_file |
| `ispra_rs_export` | Regionale | 2018–2024 | local_file |
| `ispra_rs_impianti` | Nazionale | 2018–2024 | local_file |

**Compose:** `rifiuti_urbani_unified` — JOIN ru_base + costi_procapite + costi_kg (2018–2024)

## Struttura

```
datasets/          12 dataset con dataset.yml + sql/
compose/           rifiuti_urbani_unified
normalized/        CSV normalizzati
scripts/           normalize_ispra_all.py (normalizzazione multi-sezione ISPRA)
registry/          registry.json (catalogo dataset + signal + entity)
dashboard/         Streamlit multi-pagina
tests/             Contract tests
```

## Esecuzione

```bash
make run                          # tutti i dataset, ognuno per gli anni di dataset.yml
make run-compose                  # compose unified
make run-ispra-ru-base            # singolo dataset
make pipeline                     # test + download + normalize + run completo
make check                        # validazione config
make normalize                    # normalizza CSV ISPRA raw (2014-2024)
make download                     # scarica dati ISPRA (2014-2024)
```

Gli anni pubblicati sono quelli dichiarati in `dataset.yml`: `ispra_ru_base`
copre 2010–2024, i costi e i flussi iniziano nel 2018, i rifiuti speciali
produzione/gestione nel 2014. `make download`/`make normalize` coprono la
finestra di acquisizione 2014–2024 (`YEAR_START`/`YEAR_END`).

## Sorgenti dati

I CSV ISPRA sono multi-sezione con formati variabili tra anni. `scripts/normalize_ispra_all.py` li normalizza in un formato uniforme prima del pipeline toolkit.

- **RU comunale**: download HTTP diretto da ISPRA (http_file)
- **RU costi/flussi/gestione + RS**: da CSV normalizzati locali (local_file)

## Segnali di qualita

- [CI pipeline](.github/workflows/pipeline.yml): lint + test + run + GCS sync
- [Config check](.github/workflows/ci.yml): validazione dataset.yml su PR
- [Registry](registry/registry.json): catalogo aggiornato dalla CI

## License

MIT
