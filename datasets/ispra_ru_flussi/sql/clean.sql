-- ISPRA Rifiuti Urbani — Flussi extraregionali — CLEAN
-- CSV normalizzato: regione;anno;quantita_t

SELECT
    anno::INTEGER AS anno,
    normalize_string(regione) AS regione,
    -- La fonte include una riga di totale nazionale accanto alle regioni:
    -- va marcata, altrimenti sommarla raddoppia i totali.
    lower(normalize_string(regione)) = 'italia' AS is_aggregato,
    normalize_italian_number(quantita_t) AS quantita_t
FROM raw_input
WHERE regione IS NOT NULL
  AND quantita_t IS NOT NULL
