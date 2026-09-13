-- mart_impianti — ISPRA RS Impianti: arricchimento
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
    -- Totale impianti per sezione (Italia row)
    MAX(CASE WHEN area = 'Italia' THEN n_impianti END) OVER (
        PARTITION BY anno, sezione
    ) AS totale_impianti_sezione,
    -- Pct area sul totale sezione
    ROUND(
        n_impianti * 100.0 / NULLIF(MAX(CASE WHEN area = 'Italia' THEN n_impianti END) OVER (
            PARTITION BY anno, sezione
        ), 0), 2
    ) AS pct_sezione
FROM clean_input
ORDER BY sezione, area
