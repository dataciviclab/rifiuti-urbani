SELECT
    {year}::INTEGER AS anno,
    normalize_string(sezione) AS sezione,
    normalize_string(col1) AS area,
    cast_bigint(col2) AS n_impianti,
    normalize_italian_number(col3) AS t1,
    normalize_italian_number(col4) AS t2,
    normalize_italian_number(col5) AS t3
FROM raw_input
WHERE col1 IS NOT NULL AND col1 != ''
  AND col1 IN ('Nord', 'Centro', 'Sud', 'Italia')
