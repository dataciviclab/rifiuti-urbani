-- mart_impianti — ISPRA RU gestione per impianto/comune
--
-- Una riga per (anno, tipo impianto, regione, provincia, comune) con la quota
-- sul totale Italia e sul totale regionale dello stesso tipo.
--
-- La quota è calcolata dentro la stessa tipologia: sommare tipologie diverse
-- conta più volte la stessa tonnellata (TMB → incenerimento/discarica).

WITH arricchito AS (
    SELECT
        *,
        SUM(totale_t) OVER (PARTITION BY anno, tipo_impianto) AS totale_italia_tipo,
        SUM(totale_t) OVER (PARTITION BY anno, tipo_impianto, regione) AS totale_regionale_tipo
    FROM clean_input
)
SELECT
    anno,
    tipo_impianto,
    regione,
    provincia,
    comune,
    n_impianti,
    frazione_umida_t,
    verde_t,
    tot_ru_t,
    fanghi_t,
    altro_t,
    totale_t,
    totale_italia_tipo,
    totale_regionale_tipo,
    ROUND(totale_t * 100.0 / NULLIF(totale_italia_tipo, 0), 2) AS pct_italia_tipo,
    ROUND(totale_t * 100.0 / NULLIF(totale_regionale_tipo, 0), 2) AS pct_regionale_tipo
FROM arricchito
ORDER BY anno, tipo_impianto, totale_t DESC
