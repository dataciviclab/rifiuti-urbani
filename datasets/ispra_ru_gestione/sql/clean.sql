SELECT
    {year}::INTEGER AS anno,
    normalize_string(sezione) AS area_geografica,
    cast_bigint(col1) AS numero_impianti,
    normalize_italian_number(col2) AS frazione_umida_t,
    normalize_italian_number(col3) AS verde_t,
    normalize_italian_number(col4) AS tot_ru_t,
    normalize_italian_number(col5) AS fanghi_t,
    normalize_italian_number(col6) AS altro_t,
    normalize_italian_number(col7) AS totale_t
FROM raw_input
WHERE sezione IS NOT NULL AND sezione != ''
  AND sezione IN ('Nord', 'Centro', 'Sud', 'Italia')
