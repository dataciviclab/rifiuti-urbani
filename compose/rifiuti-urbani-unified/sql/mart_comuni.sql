-- mart_comuni — Compose RU: vista unificata comuni
--
-- 1 riga per comune × anno con tutti gli attributi.
-- Uso: dashboard, analisi territoriali, ranking civico.

SELECT
    anno,
    codice_comune_istat,
    regione,
    provincia,
    comune,
    popolazione,
    totale_ru_tonnellate,
    totale_rd_tonnellate,
    percentuale_rd,
    kg_ru_per_abitante,
    kg_rd_per_abitante,
    classe_demografica,
    media_nazionale_rd,
    media_regionale_rd,
    percentile_nazionale,
    fascia_rd,
    ctot_euro_ab,
    crt_euro_ab,
    crd_euro_ab,
    csl_euro_ab,
    cc_euro_ab,
    ck_euro_ab,
    ctot_cent_kg,
    crt_cent_kg,
    crd_cent_kg,
    csl_cent_kg,
    cc_cent_kg,
    ck_cent_kg
FROM clean_input
ORDER BY anno, regione, provincia, comune
