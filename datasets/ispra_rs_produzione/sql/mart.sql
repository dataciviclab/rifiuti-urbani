-- mart_produzione — ISPRA RS Produzione: arricchimento
--
-- Aggiunge totali per area geografica e percentuali.

SELECT
    anno,
    area_geografica,
    rs_np_t,
    rs_p_t,
    rs_cer_nd_t,
    totale_t,
    -- Totale per area (Italia row)
    MAX(CASE WHEN area_geografica = 'Italia' THEN totale_t END) OVER (
        PARTITION BY anno
    ) AS totale_italia,
    -- Pct area sul totale Italia
    ROUND(
        totale_t * 100.0 / NULLIF(MAX(CASE WHEN area_geografica = 'Italia' THEN totale_t END) OVER (
            PARTITION BY anno
        ), 0), 2
    ) AS pct_italia
FROM clean_input
WHERE totale_t > 0
ORDER BY anno, area_geografica
