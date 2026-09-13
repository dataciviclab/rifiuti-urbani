-- clean.sql — Compose RU: unifica ispra-ru-base + costi su comune
--
-- Legge da raw_input (ispra-ru-base clean) e JOIN con support dataset.
-- Output: 1 riga per comune × anno con RD% + costi + benchmark.

WITH base AS (
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
        fascia_rd
    FROM raw_input
),

costi_pc AS (
    SELECT
        anno,
        codice_comune_istat,
        crt_euro_ab,
        cts_euro_ab,
        crd_euro_ab,
        ctr_euro_ab,
        csl_euro_ab,
        cc_euro_ab,
        ck_euro_ab,
        ctot_euro_ab
    FROM read_parquet('{support.costi_procapite.clean}')
),

costi_kg AS (
    SELECT
        anno,
        codice_comune_istat,
        crt_cent_kg,
        crd_cent_kg,
        csl_cent_kg,
        cc_cent_kg,
        ck_cent_kg,
        ctot_cent_kg
    FROM read_parquet('{support.costi_kg.clean}')
)

SELECT
    b.anno,
    b.codice_comune_istat,
    b.regione,
    b.provincia,
    b.comune,
    b.popolazione,
    b.totale_ru_tonnellate,
    b.totale_rd_tonnellate,
    b.percentuale_rd,
    b.kg_ru_per_abitante,
    b.kg_rd_per_abitante,
    b.classe_demografica,
    b.media_nazionale_rd,
    b.media_regionale_rd,
    b.percentile_nazionale,
    b.fascia_rd,
    -- Costi pro capite
    c.ctot_euro_ab,
    c.crt_euro_ab,
    c.crd_euro_ab,
    c.csl_euro_ab,
    c.cc_euro_ab,
    c.ck_euro_ab,
    -- Costi per kg
    k.ctot_cent_kg,
    k.crt_cent_kg,
    k.crd_cent_kg,
    k.csl_cent_kg,
    k.cc_cent_kg,
    k.ck_cent_kg
FROM base b
LEFT JOIN costi_pc c ON b.anno = c.anno AND b.codice_comune_istat = c.codice_comune_istat
LEFT JOIN costi_kg k ON b.anno = k.anno AND b.codice_comune_istat = k.codice_comune_istat
