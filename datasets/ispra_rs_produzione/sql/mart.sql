-- mart_produzione — ISPRA RS Produzione: arricchimento
--
-- Aggiunge totali per sezione e percentuali per area.

SELECT
    anno,
    sezione,
    area,
    valore_1 AS nord,
    valore_2 AS centro,
    valore_3 AS sud,
    valore_4 AS totale_italia,
    -- Pct area sul totale sezione
    ROUND(
        valore_4 * 100.0 / NULLIF(MAX(valore_4) OVER (
            PARTITION BY anno, sezione
        ), 0), 2
    ) AS pct_sezione
FROM clean_input
WHERE valore_4 > 0
  AND area NOT LIKE '%Totale%'
  AND area NOT LIKE '%Descrizione%'
ORDER BY sezione, valore_4 DESC
