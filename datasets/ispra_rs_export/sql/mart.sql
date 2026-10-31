SELECT
    anno, regione, rifiuti_non_pericolosi_t, rifiuti_pericolosi_t, totale_t,
    SUM(totale_t) OVER (PARTITION BY anno) AS totale_nazionale,
    ROUND(totale_t * 100.0 / NULLIF(SUM(totale_t) OVER (PARTITION BY anno), 0), 2) AS pct_nazionale
FROM clean_input
-- Esclude la riga di totale nazionale: sommarla alle regioni raddoppia i totali.
WHERE totale_t > 0
  AND NOT is_aggregato
ORDER BY totale_t DESC
