-- ISPRA RS Gestione — CLEAN
-- CSV normalizzato: sezione;col1;col2;col3;col4;col5

SELECT
    {year}::INTEGER AS anno,
    normalize_string(sezione) AS sezione,
    normalize_string(col1) AS area,
    normalize_italian_number(col2) AS valore_1,
    normalize_italian_number(col3) AS valore_2,
    normalize_italian_number(col4) AS valore_3,
    normalize_italian_number(col5) AS valore_4
FROM raw_input
WHERE col1 IS NOT NULL
  AND col1 != ''
  AND col1 NOT LIKE '%Area%'
  AND col1 NOT LIKE '%Legenda%'
  AND col1 NOT LIKE '%R13%'
