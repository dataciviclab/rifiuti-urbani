-- mart_produzione — ISPRA RS Produzione
--
-- Una riga per (anno, dimensione, etichetta, area, ripartizione) con il
-- valore nazionale della stessa etichetta come colonna, non come riga.
--
-- `dimensione` dice cosa significa `etichetta`:
--   area      → etichetta = area geografica (dati di sintesi)
--   attivita  → etichetta = attività economica (ATECO, macro-settore)
--   capitolo  → etichetta = capitolo dell'Elenco Europeo dei Rifiuti (EER)
--
-- Le ripartizioni (totale / np / p) non vanno sommate tra loro: `totale_t`
-- è NULL sulle righe np/p proprio per impedirlo.

WITH arricchito AS (
    SELECT
        anno,
        dimensione,
        etichetta,
        area_geografica,
        ripartizione,
        np_t,
        p_t,
        cer_nd_t,
        totale_t,
        -- Per dimensione='area' l'etichetta *è* l'area: se la si include nella
        -- partizione ogni riga resta sola e il valore Italia non arriva.
        MAX(CASE WHEN area_geografica = 'Italia' THEN np_t END)
            OVER (PARTITION BY anno, dimensione,
                  CASE WHEN dimensione = 'area' THEN '' ELSE etichetta END, ripartizione) AS np_italia_t,
        MAX(CASE WHEN area_geografica = 'Italia' THEN p_t END)
            OVER (PARTITION BY anno, dimensione,
                  CASE WHEN dimensione = 'area' THEN '' ELSE etichetta END, ripartizione) AS p_italia_t,
        MAX(CASE WHEN area_geografica = 'Italia' THEN totale_t END)
            OVER (PARTITION BY anno, dimensione,
                  CASE WHEN dimensione = 'area' THEN '' ELSE etichetta END, ripartizione) AS totale_italia_t
    FROM clean_input
)
SELECT
    anno,
    dimensione,
    etichetta,
    area_geografica,
    ripartizione,
    np_t,
    p_t,
    cer_nd_t,
    totale_t,
    np_italia_t,
    p_italia_t,
    totale_italia_t,
    ROUND(coalesce(totale_t, np_t, p_t) * 100.0
          / NULLIF(coalesce(totale_italia_t, np_italia_t, p_italia_t), 0), 3) AS pct_italia
FROM arricchito
WHERE area_geografica <> 'Italia'
ORDER BY anno, dimensione, coalesce(totale_t, np_t, p_t) DESC
