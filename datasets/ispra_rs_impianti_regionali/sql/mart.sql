-- mart_impianti — ISPRA RS Impianti
--
-- Una riga per (anno, tipo impianto, area) con la quota sul totale Italia
-- dello stesso tipo. Le righe Italia non entrano nel mart: i valori nazionali
-- sono colonne (n_italia_tipo, totale_italia_tipo), così non li si somma per
-- sbaglio alle aree.
--
-- ATTENZIONE: `categoria = 'recupero_stoccaggio'` non è sommabile a
-- 'trattamento_smaltimento'. Il tonnellaggio degli impianti di recupero e
-- stoccaggio è throughput (lo stesso rifiuto passa più volte), quello dei
-- trattamenti è il conferito. Per questo la categoria è esposta e la quota
-- è calcolata dentro lo stesso tipo.

WITH arricchito AS (
    SELECT
        anno,
        tipo_impianto,
        categoria,
        area_geografica,
        numero_impianti,
        rs_non_pericolosi_t,
        rs_pericolosi_t,
        totale_t,
        MAX(CASE WHEN area_geografica = 'Italia' THEN numero_impianti END)
            OVER (PARTITION BY anno, tipo_impianto) AS n_italia_tipo,
        MAX(CASE WHEN area_geografica = 'Italia' THEN totale_t END)
            OVER (PARTITION BY anno, tipo_impianto) AS totale_italia_tipo
    FROM clean_input
)
SELECT
    anno,
    tipo_impianto,
    categoria,
    area_geografica,
    numero_impianti,
    rs_non_pericolosi_t,
    rs_pericolosi_t,
    totale_t,
    n_italia_tipo,
    totale_italia_tipo,
    ROUND(totale_t * 100.0 / NULLIF(totale_italia_tipo, 0), 2) AS pct_italia_tipo
FROM arricchito
WHERE area_geografica <> 'Italia'
ORDER BY anno, categoria, tipo_impianto, totale_t DESC
