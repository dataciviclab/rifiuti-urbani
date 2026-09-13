-- mart_impianti — ISPRA RS Impianti: arricchimento
--
-- Aggiunge totali per area geografica e percentuali.

SELECT
    anno,
    area_geografica,
    numero_impianti,
    fanghi_t,
    altri_rs_t,
    totale_rs_t,
    -- Totale impianti per area (Italia row)
    MAX(CASE WHEN area_geografica = 'Italia' THEN totale_rs_t END) OVER (
        PARTITION BY anno
    ) AS totale_italia,
    -- Pct area sul totale Italia
    ROUND(
        totale_rs_t * 100.0 / NULLIF(MAX(CASE WHEN area_geografica = 'Italia' THEN totale_rs_t END) OVER (
            PARTITION BY anno
        ), 0), 2
    ) AS pct_italia
FROM clean_input
WHERE totale_rs_t > 0
ORDER BY anno, area_geografica
