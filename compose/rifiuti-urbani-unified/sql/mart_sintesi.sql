-- mart_sintesi — Compose RU: statistiche provinciali unificate
--
-- 1 riga per provincia × anno con RD% + costi.

SELECT
    anno,
    regione,
    provincia,
    count(*) AS n_comuni,
    round(sum(popolazione), 0) AS popolazione_totale,
    -- RD% medio pesato
    round(sum(percentuale_rd * popolazione) / nullif(sum(popolazione), 0), 2) AS rd_media_ponderata,
    -- Kg pro-capite
    round(sum(totale_ru_tonnellate * 1000.0) / nullif(sum(popolazione), 0), 1) AS kg_ru_procapite,
    round(sum(totale_rd_tonnellate * 1000.0) / nullif(sum(popolazione), 0), 1) AS kg_rd_procapite,
    -- Costi medi
    round(avg(ctot_euro_ab), 2) AS costo_medio_euro_ab,
    round(avg(ctot_cent_kg), 2) AS costo_medio_cent_kg,
    round(avg(kg_ru_per_abitante), 1) AS kg_ru_medio
FROM clean_input
WHERE popolazione > 0
  AND provincia IS NOT NULL
GROUP BY anno, regione, provincia
ORDER BY anno DESC, rd_media_ponderata DESC
