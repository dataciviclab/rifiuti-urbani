-- mart_flussi — ISPRA Rifiuti Urbani Flussi: arricchimento regionale
--
-- Aggiunge totali nazionali e percentuali per regione. Totale e percentuale
-- sono calcolati per tipo di flusso: sommare organico, incenerimento e
-- discarica darebbe un "totale" che non esiste nella fonte.

SELECT
    anno,
    tipo_flusso,
    regione,
    quantita_t,
    -- Totale nazionale del tipo di flusso
    SUM(quantita_t) OVER (PARTITION BY anno, tipo_flusso) AS totale_nazionale,
    -- Percentuale regionale sul totale nazionale del tipo di flusso
    ROUND(
        quantita_t * 100.0 / NULLIF(SUM(quantita_t) OVER (PARTITION BY anno, tipo_flusso), 0),
        2
    ) AS pct_nazionale
FROM clean_input
-- Esclude la riga di totale nazionale: sommarla alle regioni raddoppia i totali.
WHERE quantita_t > 0
  AND NOT is_aggregato
ORDER BY anno, tipo_flusso, quantita_t DESC
