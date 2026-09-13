-- ISPRA RS Gestione — CLEAN
-- CSV normalizzato: sezione;col1;col2;col3;col4;col5

SELECT
    {year}::INTEGER AS anno,
    normalize_string(col1) AS area_geografica,
    normalize_italian_number(col2) AS rs_np_t,
    normalize_italian_number(col3) AS rs_p_t,
    normalize_italian_number(col4) AS rs_cer_nd_t,
    normalize_italian_number(col5) AS totale_t
FROM raw_input
WHERE col1 IS NOT NULL
  AND col1 != ''
  AND col1 NOT LIKE '%Area%'
  AND col1 NOT LIKE '%Legenda%'
  AND col1 NOT LIKE '%R13%'
