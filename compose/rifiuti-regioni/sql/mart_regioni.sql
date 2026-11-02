-- mart_regioni — Compose regionale RU/RS
--
-- Una riga per regione × anno. Aggiunge i confronti nazionali (quota di RU,
-- distanza dalla media RD e dai costi) e il rank per RD%.
--
-- Nota: `pct_discarica_su_trattamenti_finali` è una quota di mix, non un
-- bilancio di massa: il denominatore esclude il TMB (pre-trattamento) e non
-- include il riciclo delle frazioni secche, che vive in ru_base.

WITH arricchito AS (
    SELECT
        *,
        SUM(totale_ru_tonnellate) OVER (PARTITION BY anno) AS ru_nazionale_t,
        AVG(percentuale_rd) OVER (PARTITION BY anno) AS media_nazionale_rd,
        AVG(ctot_euro_ab) OVER (PARTITION BY anno) AS media_nazionale_ctot,
        AVG(pct_discarica_su_trattamenti_finali) OVER (PARTITION BY anno)
            AS media_nazionale_pct_discarica
    FROM clean_input
)
SELECT
    *,
    ROUND(totale_ru_tonnellate * 100.0 / NULLIF(ru_nazionale_t, 0), 2) AS pct_ru_nazionale,
    ROUND(percentuale_rd - media_nazionale_rd, 2) AS distanza_media_rd_pp,
    ROUND(ctot_euro_ab - media_nazionale_ctot, 2) AS distanza_media_costo_euro,
    RANK() OVER (PARTITION BY anno ORDER BY percentuale_rd DESC) AS rank_rd
FROM arricchito
ORDER BY anno, regione
