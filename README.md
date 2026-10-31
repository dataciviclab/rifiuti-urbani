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

## Impianti, gestione e produzione RS

I file ISPRA di impianti, gestione e produzione sono **multi-tabella**: un solo
CSV contiene più blocchi (compostaggio, TMB, incenerimento, discarica…), ognuno
con il proprio header e un numero di colonne diverso (in `rs_impianti` 2024:
da 2 a 6). Il normalizzatore li legge come blocchi e li mappa **per nome di
colonna**, non per posizione.

Ogni dataset espone quindi la dimensione che prima veniva persa:

| dataset | dimensione | esempio |
|---|---|---|
| `ispra_rs_impianti` | `tipo_impianto`, `categoria` | Impianti di recupero di materia: 4.620 impianti, 91,2 Mt |
| `ispra_ru_gestione` | `tipo_impianto` | TMB 132 impianti, incenerimento 35 |
| `ispra_rs_gestione` | `codice` operazione + `natura` | R1-R12 flussi, R13 giacenza |
| `ispra_rs_produzione` | `dimensione` + `etichetta` | attività economica / capitolo EER |

Due avvertenze strutturali:

- **recupero/stoccaggio ≠ trattamento/smaltimento**: il tonnellaggio delle
  "altre tipologie" è throughput (lo stesso rifiuto transita più volte) e non
  va sommato a quello degli impianti di trattamento;
- **R13/D15 sono giacenze**, non flussi: sommarle gonfia i totali di ~18 Mt.

Dal 2023 ISPRA pubblica anche le "altre tipologie" di impianti: il conteggio
totale passa da ~2.400 a ~10.500 unità. La serie confrontabile tra anni è
quella per `categoria = 'trattamento_smaltimento'`.

## Dataset

| Slug | Livello | Anni | Tipo raw |
|---|---|---|---|
| `ispra_ru_base` | Comunale | 2010–2024 | http_file |
| `ispra_ru_costi_procapite` | Comunale | 2018–2024 | local_file |
| `ispra_ru_costi_kg` | Comunale | 2018–2024 | local_file |
| `ispra_ru_flussi` | Regionale | 2018–2024 | local_file |
| `ispra_ru_gestione` | Nazionale × tipo impianto | 2015–2024 | local_file |
| `ispra_ru_export` | Regionale | 2018–2024 | local_file |
| `ispra_ru_import` | Regionale | 2018–2024 | local_file |
| `ispra_rs_produzione` | Attività / capitolo EER | 2014–2024 | local_file |
| `ispra_rs_gestione` | Operazione (R/D) | 2014–2024 | local_file |
| `ispra_rs_import` | Regionale | 2018–2024 | local_file |
| `ispra_rs_export` | Regionale | 2018–2024 | local_file |
| `ispra_rs_impianti` | Tipo impianto × area | 2018–2024 | local_file |

**Compose:** `rifiuti_urbani_unified` — JOIN ru_base + costi_procapite + costi_kg (2018–2024)

## Struttura

```
datasets/          12 dataset con dataset.yml + sql/
compose/           rifiuti_urbani_unified
normalized/        CSV normalizzati
scripts/           normalize_ispra_all.py (parser multi-blocco ISPRA)
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
