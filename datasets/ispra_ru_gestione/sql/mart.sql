-- mart_gestione — ISPRA RU Gestione: arricchimento
--
-- Aggiunge totali per sezione e percentuali per area.

SELECT
    anno,
    sezione,
    area,
    n_impianti,
    t1,
    t2,
    t3,
    -- Totale per sezione (Italia row)
    MAX(CASE WHEN area = 'Italia' THEN t3 END) OVER (
        PARTITION BY anno, sezione
    ) AS totale_sezione,
    -- Pct area sul totale sezione
    ROUND(
        t3 * 100.0 / NULLIF(MAX(CASE WHEN area = 'Italia' THEN t3 END) OVER (
            PARTITION BY anno, sezione
        ), 0), 2
    ) AS pct_sezione
FROM clean_input
WHERE t3 > 0
ORDER BY sezione, area
