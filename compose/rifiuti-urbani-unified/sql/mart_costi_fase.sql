-- mart_costi_fase — Compose RU: composizione e indicatori di costo per comune
--
-- 1 riga per comune × anno con il costo del servizio scomposto per fase
-- (schema ISPRA/ARERA) e gli indicatori che rispondono a:
-- "quanto costa smaltire rispetto a recuperare?".
--
-- Fonti: clean_input del compose (ispra_ru_base + ispra_ru_costi_procapite
-- + ispra_ru_costi_kg).
--
-- Unità di misura:
--   *_euro_ab                 = euro per abitante
--   quota_*_pct               = % sul costo totale (ctot)
--   rapporto_recupero_smaltimento = CTR / CTS (null se CTS assente/zero)
--   costo_per_punto_rd_euro   = €/ab per ogni punto di RD%
--   costo_per_tonnellata_euro = € per tonnellata di RU prodotta
--
-- NOTA: CTOT non è sempre la somma delle voci mappate (nel tracciato ISPRA
-- 2020+ compare "Altri costi", che il normalizzatore non mappa). Per questo
-- `quota_altri_pct` chiude il conto a 100 e rende visibile il residuo invece
-- di nasconderlo: se è negativo, i costi a monte sono incoerenti.

WITH base AS (
    SELECT
        anno,
        codice_comune_istat,
        regione,
        provincia,
        comune,
        popolazione,
        classe_demografica,
        percentuale_rd,
        kg_ru_per_abitante,
        totale_ru_tonnellate,
        totale_rd_tonnellate,
        crt_euro_ab,
        cts_euro_ab,
        crd_euro_ab,
        ctr_euro_ab,
        csl_euro_ab,
        cc_euro_ab,
        ck_euro_ab,
        ctot_euro_ab
    FROM clean_input
    WHERE ctot_euro_ab IS NOT NULL
      AND ctot_euro_ab > 0
),

quoted AS (
    SELECT
        *,
        round(100.0 * crt_euro_ab / ctot_euro_ab, 2) AS quota_crt_pct,
        round(100.0 * cts_euro_ab / ctot_euro_ab, 2) AS quota_cts_pct,
        round(100.0 * crd_euro_ab / ctot_euro_ab, 2) AS quota_crd_pct,
        round(100.0 * ctr_euro_ab / ctot_euro_ab, 2) AS quota_ctr_pct,
        round(100.0 * csl_euro_ab / ctot_euro_ab, 2) AS quota_csl_pct,
        round(100.0 * cc_euro_ab / ctot_euro_ab, 2) AS quota_cc_pct,
        round(100.0 * ck_euro_ab / ctot_euro_ab, 2) AS quota_ck_pct
    FROM base
)

SELECT
    anno,
    codice_comune_istat,
    regione,
    provincia,
    comune,
    popolazione,
    classe_demografica,
    percentuale_rd,
    kg_ru_per_abitante,
    totale_ru_tonnellate,
    totale_rd_tonnellate,

    -- Costi (euro/abitante), schema ISPRA/ARERA
    crt_euro_ab,
    cts_euro_ab,
    crd_euro_ab,
    ctr_euro_ab,
    csl_euro_ab,
    cc_euro_ab,
    ck_euro_ab,
    ctot_euro_ab,

    -- Composizione percentuale
    quota_crt_pct,
    quota_cts_pct,
    quota_crd_pct,
    quota_ctr_pct,
    quota_csl_pct,
    quota_cc_pct,
    quota_ck_pct,
    round(
        100
        - coalesce(quota_crt_pct, 0)
        - coalesce(quota_cts_pct, 0)
        - coalesce(quota_crd_pct, 0)
        - coalesce(quota_ctr_pct, 0)
        - coalesce(quota_csl_pct, 0)
        - coalesce(quota_cc_pct, 0)
        - coalesce(quota_ck_pct, 0),
        2
    ) AS quota_altri_pct,

    -- Natura del costo: fissa (spazzamento, comuni, capitale) vs variabile
    -- (raccolta e trattamento).
    round(
        coalesce(quota_csl_pct, 0)
        + coalesce(quota_cc_pct, 0)
        + coalesce(quota_ck_pct, 0),
        2
    ) AS quota_costo_fisso_pct,
    round(
        coalesce(quota_crt_pct, 0)
        + coalesce(quota_cts_pct, 0)
        + coalesce(quota_crd_pct, 0)
        + coalesce(quota_ctr_pct, 0),
        2
    ) AS quota_costo_variabile_pct,

    -- Recupero vs smaltimento: >1 significa che il recupero pesa più dello
    -- smaltimento nel costo del servizio.
    round(ctr_euro_ab / nullif(cts_euro_ab, 0), 3) AS rapporto_recupero_smaltimento,

    -- Efficienza economica
    round(ctot_euro_ab / nullif(percentuale_rd, 0), 2) AS costo_per_punto_rd_euro,
    round(
        ctot_euro_ab * popolazione / nullif(totale_ru_tonnellate, 0),
        2
    ) AS costo_per_tonnellata_euro,

    -- €/kg derivati per CTS e CTR: ISPRA non li pubblica a livello di kg,
    -- si ricavano da €/ab ÷ kg RU pro capite.
    round(cts_euro_ab / nullif(kg_ru_per_abitante, 0) * 100, 2) AS cts_cent_kg,
    round(ctr_euro_ab / nullif(kg_ru_per_abitante, 0) * 100, 2) AS ctr_cent_kg

FROM quoted
ORDER BY anno, regione, provincia, comune;
