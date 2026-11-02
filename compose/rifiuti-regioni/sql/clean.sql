-- clean.sql — Compose regionale RU/RS
--
-- Grain: una riga per regione × anno.
--
-- Fonti (clean dei dataset di supporto, glob su tutti gli anni):
--   raw_input = rifiuti_urbani_unified/mart_comuni (grain comunale)
--   {support.ru_gestione_regionale.clean}
--   {support.ru_import.clean} / {support.ru_export.clean}
--   {support.ru_flussi.clean}
--   {support.rs_produzione_regionale.clean}
--   {support.rs_gestione_regionale.clean}
--
-- I support sono letti in forma lunga e aggregati per (anno, regione): il
-- join usa una chiave regione normalizzata (minuscolo, senza trattino),
-- perché le fonti regionali alternano "PIEMONTE", "Piemonte" e
-- "Friuli-Venezia Giulia".
--
-- ATTENZIONE: le tonnellate di gestione sono throughput impiantistico, non un
-- bilancio di massa. TMB è pre-trattamento e la stessa tonnellata transita
-- verso incenerimento/discarica: le colonne restano separate e i tassi sono
-- calcolati solo sui trattamenti finali (TMB escluso).

WITH base AS (
    SELECT
        anno,
        regione,
        COUNT(*) AS n_comuni,
        SUM(popolazione) AS popolazione,
        SUM(totale_ru_tonnellate) AS totale_ru_tonnellate,
        SUM(totale_rd_tonnellate) AS totale_rd_tonnellate,
        SUM(CASE WHEN percentuale_rd IS NOT NULL
                 THEN percentuale_rd * popolazione ELSE 0 END)
            / NULLIF(SUM(CASE WHEN percentuale_rd IS NOT NULL
                              THEN popolazione ELSE 0 END), 0) AS percentuale_rd,
        -- I costi si mediano solo sui comuni che li dichiarano: usare tutta
        -- la popolazione diluirebbe la media (i comuni senza costo entrano
        -- nel denominatore ma non nel numeratore).
        SUM(CASE WHEN ctot_euro_ab IS NOT NULL THEN popolazione ELSE 0 END) AS pop_costi,
        SUM(CASE WHEN ctot_euro_ab IS NOT NULL
                 THEN coalesce(crt_euro_ab, 0) * popolazione ELSE 0 END)
            / NULLIF(SUM(CASE WHEN ctot_euro_ab IS NOT NULL
                              THEN popolazione ELSE 0 END), 0) AS crt_euro_ab,
        SUM(CASE WHEN ctot_euro_ab IS NOT NULL
                 THEN coalesce(cts_euro_ab, 0) * popolazione ELSE 0 END)
            / NULLIF(SUM(CASE WHEN ctot_euro_ab IS NOT NULL
                              THEN popolazione ELSE 0 END), 0) AS cts_euro_ab,
        SUM(CASE WHEN ctot_euro_ab IS NOT NULL
                 THEN coalesce(crd_euro_ab, 0) * popolazione ELSE 0 END)
            / NULLIF(SUM(CASE WHEN ctot_euro_ab IS NOT NULL
                              THEN popolazione ELSE 0 END), 0) AS crd_euro_ab,
        SUM(CASE WHEN ctot_euro_ab IS NOT NULL
                 THEN coalesce(ctr_euro_ab, 0) * popolazione ELSE 0 END)
            / NULLIF(SUM(CASE WHEN ctot_euro_ab IS NOT NULL
                              THEN popolazione ELSE 0 END), 0) AS ctr_euro_ab,
        SUM(CASE WHEN ctot_euro_ab IS NOT NULL
                 THEN coalesce(csl_euro_ab, 0) * popolazione ELSE 0 END)
            / NULLIF(SUM(CASE WHEN ctot_euro_ab IS NOT NULL
                              THEN popolazione ELSE 0 END), 0) AS csl_euro_ab,
        SUM(CASE WHEN ctot_euro_ab IS NOT NULL
                 THEN coalesce(cc_euro_ab, 0) * popolazione ELSE 0 END)
            / NULLIF(SUM(CASE WHEN ctot_euro_ab IS NOT NULL
                              THEN popolazione ELSE 0 END), 0) AS cc_euro_ab,
        SUM(CASE WHEN ctot_euro_ab IS NOT NULL
                 THEN coalesce(ck_euro_ab, 0) * popolazione ELSE 0 END)
            / NULLIF(SUM(CASE WHEN ctot_euro_ab IS NOT NULL
                              THEN popolazione ELSE 0 END), 0) AS ck_euro_ab,
        SUM(CASE WHEN ctot_euro_ab IS NOT NULL
                 THEN ctot_euro_ab * popolazione ELSE 0 END)
            / NULLIF(SUM(CASE WHEN ctot_euro_ab IS NOT NULL
                              THEN popolazione ELSE 0 END), 0) AS ctot_euro_ab
    FROM raw_input
    WHERE popolazione > 0
    GROUP BY anno, regione
),

gestione AS (
    SELECT
        anno,
        lower(replace(area_geografica, '-', ' ')) AS regione_key,
        SUM(numero_impianti) AS n_impianti,
        SUM(CASE WHEN tipo_impianto LIKE 'Smaltimento%' THEN totale_t ELSE 0 END) AS discarica_t,
        SUM(CASE WHEN tipo_impianto LIKE 'Incenerimento%' THEN totale_t ELSE 0 END) AS incenerimento_t,
        SUM(CASE WHEN tipo_impianto LIKE 'Coincenerimento%' THEN totale_t ELSE 0 END) AS coincenerimento_t,
        SUM(CASE WHEN tipo_impianto LIKE 'Trattamento meccanico%' THEN totale_t ELSE 0 END) AS tmb_t,
        SUM(CASE WHEN tipo_impianto LIKE 'Compostaggio%' THEN totale_t ELSE 0 END) AS compostaggio_t,
        SUM(CASE WHEN tipo_impianto LIKE 'Trattamento integrato%' THEN totale_t ELSE 0 END) AS trattamento_integrato_t,
        SUM(CASE WHEN tipo_impianto LIKE 'Digestione%' THEN totale_t ELSE 0 END) AS digestione_t
    FROM read_parquet('{support.ru_gestione_regionale.clean}')
    WHERE lower(area_geografica) <> 'italia'
    GROUP BY 1, 2
),

import_ru AS (
    SELECT
        anno,
        lower(replace(regione, '-', ' ')) AS regione_key,
        SUM(totale_t) AS import_t
    FROM read_parquet('{support.ru_import.clean}')
    WHERE NOT is_aggregato
    GROUP BY 1, 2
),

export_ru AS (
    SELECT
        anno,
        lower(replace(regione, '-', ' ')) AS regione_key,
        SUM(totale_t) AS export_t
    FROM read_parquet('{support.ru_export.clean}')
    WHERE NOT is_aggregato
    GROUP BY 1, 2
),

flussi_ru AS (
    SELECT
        anno,
        lower(replace(regione, '-', ' ')) AS regione_key,
        SUM(quantita_t) AS flussi_extraregionali_t
    FROM read_parquet('{support.ru_flussi.clean}')
    WHERE NOT is_aggregato
    GROUP BY 1, 2
),

rs_produzione AS (
    SELECT
        anno,
        lower(replace(area_geografica, '-', ' ')) AS regione_key,
        SUM(np_t) AS rs_np_t,
        SUM(p_t) AS rs_p_t,
        SUM(totale_t) AS rs_totale_t
    FROM read_parquet('{support.rs_produzione_regionale.clean}')
    WHERE dimensione = 'area'
      AND ripartizione = 'totale'
      AND lower(area_geografica) <> 'italia'
    GROUP BY 1, 2
),

rs_gestione AS (
    SELECT
        anno,
        lower(replace(area_geografica, '-', ' ')) AS regione_key,
        SUM(CASE WHEN tipo_operazione = 'recupero' AND natura = 'flusso'
                 THEN quantita_t ELSE 0 END) AS rs_recupero_t,
        SUM(CASE WHEN tipo_operazione = 'smaltimento' AND natura = 'flusso'
                 THEN quantita_t ELSE 0 END) AS rs_smaltimento_t,
        SUM(CASE WHEN natura = 'giacenza' THEN quantita_t ELSE 0 END) AS rs_giacenza_t
    FROM read_parquet('{support.rs_gestione_regionale.clean}')
    WHERE ripartizione = 'totale'
      AND lower(area_geografica) <> 'italia'
    GROUP BY 1, 2
),

unito AS (
    SELECT
        b.anno,
        b.regione,
        b.n_comuni,
        b.popolazione,
        b.totale_ru_tonnellate,
        b.totale_rd_tonnellate,
        b.percentuale_rd,
        b.crt_euro_ab,
        b.cts_euro_ab,
        b.crd_euro_ab,
        b.ctr_euro_ab,
        b.csl_euro_ab,
        b.cc_euro_ab,
        b.ck_euro_ab,
        b.ctot_euro_ab,
        g.n_impianti,
        g.discarica_t,
        g.incenerimento_t,
        g.coincenerimento_t,
        g.tmb_t,
        g.compostaggio_t,
        g.trattamento_integrato_t,
        g.digestione_t,
        i.import_t,
        e.export_t,
        f.flussi_extraregionali_t,
        p.rs_np_t,
        p.rs_p_t,
        p.rs_totale_t,
        r.rs_recupero_t,
        r.rs_smaltimento_t,
        r.rs_giacenza_t
    FROM base b
    LEFT JOIN gestione g
        ON b.anno = g.anno
       AND lower(replace(b.regione, '-', ' ')) = g.regione_key
    LEFT JOIN import_ru i
        ON b.anno = i.anno
       AND lower(replace(b.regione, '-', ' ')) = i.regione_key
    LEFT JOIN export_ru e
        ON b.anno = e.anno
       AND lower(replace(b.regione, '-', ' ')) = e.regione_key
    LEFT JOIN flussi_ru f
        ON b.anno = f.anno
       AND lower(replace(b.regione, '-', ' ')) = f.regione_key
    LEFT JOIN rs_produzione p
        ON b.anno = p.anno
       AND lower(replace(b.regione, '-', ' ')) = p.regione_key
    LEFT JOIN rs_gestione r
        ON b.anno = r.anno
       AND lower(replace(b.regione, '-', ' ')) = r.regione_key
)

SELECT
    anno,
    regione,
    n_comuni,
    popolazione,
    totale_ru_tonnellate,
    totale_rd_tonnellate,
    ROUND(percentuale_rd, 2) AS percentuale_rd,
    ROUND(totale_ru_tonnellate * 1000.0 / NULLIF(popolazione, 0), 1) AS kg_ru_per_abitante,
    ROUND(totale_rd_tonnellate * 1000.0 / NULLIF(popolazione, 0), 1) AS kg_rd_per_abitante,

    -- Costi del servizio (euro/abitante, media pesata sulla popolazione)
    ROUND(ctot_euro_ab, 2) AS ctot_euro_ab,
    ROUND(crt_euro_ab, 2) AS crt_euro_ab,
    ROUND(cts_euro_ab, 2) AS cts_euro_ab,
    ROUND(crd_euro_ab, 2) AS crd_euro_ab,
    ROUND(ctr_euro_ab, 2) AS ctr_euro_ab,
    ROUND(csl_euro_ab, 2) AS csl_euro_ab,
    ROUND(cc_euro_ab, 2) AS cc_euro_ab,
    ROUND(ck_euro_ab, 2) AS ck_euro_ab,
    ROUND(100.0 * cts_euro_ab / NULLIF(ctot_euro_ab, 0), 2) AS quota_cts_pct,
    ROUND(100.0 * ctr_euro_ab / NULLIF(ctot_euro_ab, 0), 2) AS quota_ctr_pct,
    ROUND(100.0 * (csl_euro_ab + cc_euro_ab + ck_euro_ab) / NULLIF(ctot_euro_ab, 0), 2)
        AS quota_costo_fisso_pct,
    ROUND(ctr_euro_ab / NULLIF(cts_euro_ab, 0), 3) AS rapporto_recupero_smaltimento,
    ROUND(ctot_euro_ab / NULLIF(percentuale_rd, 0), 2) AS costo_per_punto_rd_euro,
    ROUND(ctot_euro_ab * popolazione / NULLIF(totale_ru_tonnellate, 0), 2)
        AS costo_per_tonnellata_euro,

    -- Mix impiantistico (tonnellate; TMB è pre-trattamento, non un sink)
    n_impianti,
    ROUND(discarica_t, 1) AS discarica_t,
    ROUND(incenerimento_t, 1) AS incenerimento_t,
    ROUND(coincenerimento_t, 1) AS coincenerimento_t,
    ROUND(tmb_t, 1) AS tmb_t,
    ROUND(compostaggio_t, 1) AS compostaggio_t,
    ROUND(trattamento_integrato_t, 1) AS trattamento_integrato_t,
    ROUND(digestione_t, 1) AS digestione_t,
    ROUND(
        coalesce(discarica_t, 0) + coalesce(incenerimento_t, 0)
        + coalesce(coincenerimento_t, 0) + coalesce(compostaggio_t, 0)
        + coalesce(trattamento_integrato_t, 0) + coalesce(digestione_t, 0),
        1
    ) AS trattamenti_finali_t,
    ROUND(discarica_t * 100.0 / NULLIF(
        coalesce(discarica_t, 0) + coalesce(incenerimento_t, 0)
        + coalesce(coincenerimento_t, 0) + coalesce(compostaggio_t, 0)
        + coalesce(trattamento_integrato_t, 0) + coalesce(digestione_t, 0), 0), 2)
        AS pct_discarica_su_trattamenti_finali,
    ROUND((coalesce(compostaggio_t, 0) + coalesce(trattamento_integrato_t, 0)
           + coalesce(digestione_t, 0)) * 100.0 / NULLIF(
        coalesce(discarica_t, 0) + coalesce(incenerimento_t, 0)
        + coalesce(coincenerimento_t, 0) + coalesce(compostaggio_t, 0)
        + coalesce(trattamento_integrato_t, 0) + coalesce(digestione_t, 0), 0), 2)
        AS pct_riciclo_organico_su_trattamenti_finali,

    -- Movimentazione (0 dove la fonte non riporta la regione)
    ROUND(coalesce(import_t, 0), 1) AS import_t,
    ROUND(coalesce(export_t, 0), 1) AS export_t,
    ROUND(coalesce(export_t, 0) - coalesce(import_t, 0), 1) AS saldo_export_import_t,
    ROUND(coalesce(export_t, 0) * 100.0 / NULLIF(totale_ru_tonnellate, 0), 2) AS export_su_prodotto_pct,
    ROUND(coalesce(flussi_extraregionali_t, 0), 1) AS flussi_extraregionali_t,

    -- Rifiuti speciali
    ROUND(rs_np_t, 1) AS rs_np_t,
    ROUND(rs_p_t, 1) AS rs_p_t,
    ROUND(rs_totale_t, 1) AS rs_totale_t,
    ROUND(rs_recupero_t, 1) AS rs_recupero_t,
    ROUND(rs_smaltimento_t, 1) AS rs_smaltimento_t,
    ROUND(rs_giacenza_t, 1) AS rs_giacenza_t,
    ROUND(rs_recupero_t * 100.0 / NULLIF(rs_recupero_t + rs_smaltimento_t, 0), 2)
        AS rs_recupero_su_gestito_pct

FROM unito
ORDER BY anno, regione
