-- ISPRA — Import rifiuti urbani (commercio estero) — CLEAN
-- CSV normalizzato: anno;dimensione;territorio;non_pericolosi_t;pericolosi_t;totale_t
--
-- La fonte partiziona la stessa grandezza due volte: per regione italiana di
-- destinazione e per Paese di provenienza. `dimensione` distingue le due
-- viste, che sommano allo stesso totale e non vanno sommate tra loro.

SELECT
    -- La riga TOTALE del blocco Paesi non ha anno: il file è per anno.
    {year}::INTEGER AS anno,
    lower(normalize_string(dimensione)) AS dimensione,
    normalize_string(territorio) AS territorio,
    -- Righe di totale: "Italia" nel blocco regioni, "TOTALE" in quello Paesi.
    lower(normalize_string(territorio)) IN ('italia', 'totale') AS is_aggregato,
    normalize_italian_number(non_pericolosi_t) AS rifiuti_non_pericolosi_t,
    normalize_italian_number(pericolosi_t) AS rifiuti_pericolosi_t,
    normalize_italian_number(totale_t) AS totale_t
FROM raw_input
WHERE territorio IS NOT NULL
  AND territorio NOT LIKE '%Regione%'
