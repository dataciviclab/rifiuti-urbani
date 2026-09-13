-- ISPRA Rifiuti Urbani — Flussi extraregionali — CLEAN
-- CSV normalizzato: regione;anno;quantita_t

SELECT
    anno::INTEGER AS anno,
    normalize_string(regione) AS regione,
    normalize_italian_number(quantita_t) AS quantita_t
FROM raw_input
WHERE regione IS NOT NULL
  AND quantita_t IS NOT NULL
