-- ISPRA Rifiuti Urbani — Flussi extraregionali — CLEAN
-- CSV pre-normalizzato: sezione;col1;col2;col3
-- sezione = tipologia flusso, col1 = regione, col2 = anno, col3 = quantita

SELECT
    cast(col2 AS INTEGER) AS anno,
    normalize_string(col1) AS regione,
    normalize_string(sezione) AS tipologia_flusso,
    normalize_italian_number(col3) AS quantita_tonnellate
FROM raw_input
WHERE col1 IS NOT NULL
  AND col3 IS NOT NULL
  AND col2 ~ '^\d{4}$'
