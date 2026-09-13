-- mart_flussi — ISPRA Rifiuti Urbani Flussi: arricchimento regionale
--
-- Aggiunge totali nazionali e percentuali per regione

SELECT
    anno,
    regione,
    quantita_t,
    -- Totale nazionale
    SUM(quantita_t) OVER (PARTITION BY anno) AS totale_nazionale,
    -- Percentuale regionale sul totale nazionale
    ROUND(
        quantita_t * 100.0 / NULLIF(SUM(quantita_t) OVER (PARTITION BY anno), 0),
        2
    ) AS pct_nazionale
FROM clean_input
WHERE quantita_t > 0
ORDER BY anno, quantita_t DESC
