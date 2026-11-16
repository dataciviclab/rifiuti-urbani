SELECT
    anno, dimensione, territorio,
    rifiuti_non_pericolosi_t, rifiuti_pericolosi_t, totale_t,
    -- Totale e percentuale sono calcolati dentro la dimensione: le due viste
    -- (regioni, Paesi) descrivono lo stesso commercio estero, non due parti.
    SUM(totale_t) OVER (PARTITION BY anno, dimensione) AS totale_nazionale,
    ROUND(
        totale_t * 100.0
        / NULLIF(SUM(totale_t) OVER (PARTITION BY anno, dimensione), 0),
        2
    ) AS pct_nazionale
FROM clean_input
-- Esclude le righe di totale: sommarle raddoppia i totali.
WHERE totale_t > 0
  AND NOT is_aggregato
ORDER BY anno, dimensione, totale_t DESC
