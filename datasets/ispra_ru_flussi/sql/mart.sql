-- mart_flussi — ISPRA Rifiuti Urbani Flussi: arricchimento regionale
--
-- Aggiunge totali nazionali e percentuali per regione

SELECT
    anno,
    regione,
    tipologia_flusso,
    quantita_tonnellate,
    -- Totale nazionale per tipo di flusso
    SUM(quantita_tonnellate) OVER (PARTITION BY anno, tipologia_flusso) AS totale_nazionale,
    -- Percentuale regionale sul totale nazionale
    ROUND(
        quantita_tonnellate * 100.0 / NULLIF(SUM(quantita_tonnellate) OVER (PARTITION BY anno, tipologia_flusso), 0),
        2
    ) AS pct_nazionale
FROM clean_input
WHERE quantita_tonnellate > 0
ORDER BY anno, tipologia_flusso, quantita_tonnellate DESC
