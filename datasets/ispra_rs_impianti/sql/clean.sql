SELECT
    {year}::INTEGER AS anno,
    normalize_string(sezione) AS area_geografica,
    cast_bigint(col1) AS numero_impianti,
    normalize_italian_number(col2) AS fanghi_t,
    normalize_italian_number(col3) AS altri_rs_t,
    normalize_italian_number(col4) AS totale_rs_t
FROM raw_input
WHERE sezione IS NOT NULL AND sezione != ''
  AND sezione IN ('Nord', 'Centro', 'Sud', 'Italia')
