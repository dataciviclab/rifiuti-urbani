-- ISPRA RS Produzione — CLEAN
-- CSV normalizzato: sezione;col1;col2;col3;col4;col5
-- sezione = area geografica, col1-col4 = valori

SELECT
    {year}::INTEGER AS anno,
    normalize_string(sezione) AS area_geografica,
    normalize_italian_number(col1) AS rs_np_t,
    normalize_italian_number(col2) AS rs_p_t,
    normalize_italian_number(col3) AS rs_cer_nd_t,
    normalize_italian_number(col4) AS totale_t
FROM raw_input
WHERE sezione IS NOT NULL
  AND sezione != ''
  AND sezione NOT LIKE '%Totale%'
  AND sezione NOT LIKE '%Descrizione%'
  AND sezione NOT LIKE '%Capitolo%'
