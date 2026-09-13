-- mart_gestione — ISPRA RS Gestione: arricchimento
--
-- Aggiunge totali per sezione e percentuali per area.

SELECT
    anno,
    sezione,
    area,
    valore_1,
    valore_2,
    valore_3,
    valore_4,
    -- Totale per sezione (Italia row)
    MAX(CASE WHEN area = 'Italia' THEN valore_4 END) OVER (
        PARTITION BY anno, sezione
    ) AS totale_sezione,
    -- Pct area sul totale sezione
    ROUND(
        valore_4 * 100.0 / NULLIF(MAX(CASE WHEN area = 'Italia' THEN valore_4 END) OVER (
            PARTITION BY anno, sezione
        ), 0), 2
    ) AS pct_sezione
FROM clean_input
ORDER BY sezione, area
