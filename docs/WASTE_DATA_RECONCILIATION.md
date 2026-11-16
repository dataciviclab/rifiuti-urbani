# Riconciliazione dei dati rifiuti

Documento tecnico di Fase 0: cosa i dati del Lab permettono di affermare, con
quale margine, e come riprodurre ogni verifica. Va aggiornato quando cambia una
fonte o una definizione.

Le cifre si riferiscono al **2024** salvo diversa indicazione.

## Fonti e versioni

| Fonte | Cosa | Copertura | Come arriva |
|---|---|---|---|
| ISPRA Catasto Nazionale Rifiuti | RU comunali, costi, flussi, impianti; RS produzione/gestione | 2018–2024 (RU base dal 2010) | `rifiuti-ispra-raw/download_multiyear.sh` |
| ARERA | tariffe, PEF, qualità del servizio | — | **non acquisita** |
| CONAI | filiere imballaggi | — | **non acquisita** |
| MUD | dichiarazioni ambientali | — | **non acquisita** |

Le fonti non acquisite non sono un dettaglio: senza ARERA non si può dire
"quanto paga il cittadino", solo "quanto costa il servizio".

## Unità di rilevazione

I dati RU comunali hanno **due tipi di unità**, distinte da `tipo_dato`:

- `Comune` — il comune dichiara i propri dati;
- `Aggregazione` — ISPRA attribuisce i dati di più comuni a un'unione;
  gli aderenti non hanno dati propri. La popolazione dell'unità è
  capofila + aderenti.

Nel 2024 le unità sono **7.782** per 58.934.177 abitanti. In Valle d'Aosta
sono 1 comune + 4 aggregazioni: un'analisi per comune lì ha 5 righe, non 74.

## Tre cose che non sono la stessa cosa

| Concetto | Cosa misura | Dove sta |
|---|---|---|
| Raccolta differenziata | quanto viene separato | `ispra_ru_base` (comune) |
| Trattamento | quanto entra negli impianti | `ispra_ru_gestione*` (aggregato) |
| Riciclaggio effettivo | quanto torna materia prima seconda | **non disponibile** |

La differenza tra RD% (67,69%) e riciclaggio effettivo (52,3% nazionale,
rapporto ISPRA) non è ricostruibile per comune con i dati aperti: la catena si
spezza tra raccolta e impianto.

## Riconciliazioni verificate

| Controllo | Valore | Esito |
|---|---|---|
| RU prodotti 2024 vs ISPRA | 29,93 Mt su 7.782 unità | ✅ |
| RD% pesata 2024 vs ISPRA | 67,69% | ✅ |
| Costi: comuni dichiaranti (fonte) | 11.589 mln su 54,06 M ab = 214,40 €/ab | ✅ coincide con ISPRA |
| Costi: compose regionale | 11.535 mln su 53,67 M ab = 214,94 €/ab | ✅ (85 codici non agganciati) |
| RS produzione: riga `Italia` | 172,05 Mt (161,26 NP + 10,79 P) | ✅ |
| RS: somma delle 4 aree | 344,10 Mt | ❌ doppio conteggio |
| Flussi: 20 regioni vs riga `Italia` | scarto < 0,5 t su 7 anni | ✅ |
| Import/export: blocco regioni vs blocchi Paesi | stesso totale, scarto < 10 t | ✅ |
| Impianti RS: aree vs riga `Italia` | coincidono per tipo | ✅ |

## Trappole: come si ottiene un numero sbagliato

1. **Sommare le aree geografiche.** `ispra_rs_produzione` contiene le righe
   `Italia` **e** `Nord`/`Centro`/`Sud`: sommarle dà 344 Mt invece di 172.
   Filtrare `area_geografica = 'Italia'` (nel mart: `totale_italia_t`).
2. **Moltiplicare la media dei costi per la popolazione intera.** La media
   €/ab è calcolata sui soli comuni che dichiarano (6.562 su 7.782 nel 2024).
   Applicarla a tutti dà 12.676 mln invece di 11.535: **+9,9%** a livello
   nazionale, **+25,6%** in Sicilia. Usare `costo_totale_mln` e `pop_costi`.
3. **Dividere per la popolazione sbagliata.** `sum(ctot × pop) / sum(pop)`
   con la popolazione intera (58,93 M) dà 195,73 €/ab invece di 214,94.
4. **Sommare i tre flussi fuori regione.** Organico, incenerimento e discarica
   sono tre grandezze distinte: la fonte non pubblica il loro totale e un
   rifiuto può uscire due volte (organico → scarti → discarica).
5. **Sommare throughput e rifiuti trattati.** Negli impianti il tonnellaggio
   delle "altre tipologie" è transito, non trattamento: non va sommato.
6. **Trattare R13/D15 come flussi.** Sono **giacenze** al 31/12: sommarle ai
   flussi gonfia i totali di ~18 Mt.
7. **Confondere "fuori regione" con "estero".** `ispra_ru_flussi` misura i
   movimenti tra regioni, `ispra_ru_import/export` il commercio estero. Non è
   accertato che il primo escluda il secondo: non sommarli.
8. **Sommare le due dimensioni di import/export.** `dimensione = 'regione'` e
   `'paese'` sono due viste dello stesso totale, non due parti.

## Copertura e dati mancanti

- Costi: **6.562 unità su 7.782** (84,3%). Le 1.220 mancanti non dichiarano il
  costo: nel compose compaiono con `ctot_euro_ab` nullo.
- 85 codici costo non si agganciano a `ru_base`: sono aderenti alle
  aggregazioni, i cui costi sono già nella riga di aggregazione. Escluderli è
  corretto, ma vanno dichiarati.
- Flussi fuori regione: il blocco **incenerimento** esiste solo dal 2020.
  Le uscite totali 2018–2019 non sono confrontabili con gli anni successivi.
- Import/export: disponibili dal 2018.
- Costi: nessun dettaglio per frazione (ISPRA aggrega differenziata e
  indifferenziata). "Quanto costa raccogliere il vetro" non è rispondibile.

## Cosa non è ricostruibile

- **Il percorso di una tonnellata** dal comune all'impianto e alla materia
  seconda. La gestione è disponibile per area geografica × tipo di impianto,
  non per impianto singolo con bacino di utenza.
- **Gli scarti degli impianti** e la qualità del riciclo.
- **Il costo riconosciuto** (PEF) e la **tariffa pagata**. Non sono open data:
  le predisposizioni tariffarie si trasmettono ad ARERA via piattaforma
  autenticata e diventano pubbliche solo come delibere PDF per comune, sul
  portale del federalismo fiscale del MEF.
- **Chi gestisce il servizio in ciascun comune.** L'Anagrafica Territoriale
  Rifiuti (ATRIF) di ARERA contiene esattamente questo dato, è obbligatoria
  dal 2023, ma non ha un export: è accessibile solo come ricerca web. Una
  ricostruzione parziale arriva dalle partecipate MEF (comune azionista →
  società → servizio affidato), che coprono però il 43,7% dei comuni e sono
  concentrate al Nord: misurano il modello in-house, non il servizio.

## Test riproducibili

```bash
pytest tests/ -q -k "Flussi or ImportExport or ComposeRegioni or DownloadGuard"
```

Le ancore sono le righe di totale della fonte (`Italia`, `TOTALE`), non numeri
scritti a mano: se ISPRA cambia i dati, i test seguono.

Verifica manuale della trappola 1:

```sql
SELECT round(sum(totale_t)/1e6, 2) FROM _data
WHERE dimensione = 'area' AND ripartizione = 'totale';          -- 344,10 (sbagliato)
SELECT round(sum(totale_t)/1e6, 2) FROM _data
WHERE dimensione = 'area' AND ripartizione = 'totale'
  AND area_geografica = 'Italia';                               -- 172,05
```

## Registro delle correzioni

| Data | Correzione | Effetto |
|---|---|---|
| 2026-11 | `ru_flussi`: letti i 3 blocchi (prima solo l'organico) | +1,58 Mt nel mart |
| 2026-11 | import/export: letto il blocco per Paese | +212 righe |
| 2026-11 | compose regionale: `costo_totale_mln` sui dichiaranti | totale −9,9% |
| 2026-11 | compose regionale: costo/tonnellata sulle tonnellate dichiaranti | indicatore corretto |
| 2026-11 | download: rifiuto delle risposte HTML | 11 file 404 rimossi |
