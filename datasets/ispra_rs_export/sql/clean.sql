SELECT
    {year}::INTEGER AS anno,
    normalize_string(regione) AS regione,
    normalize_italian_number(non_pericolosi_t) AS rifiuti_non_pericolosi_t,
    normalize_italian_number(pericolosi_t) AS rifiuti_pericolosi_t,
    normalize_italian_number(totale_t) AS totale_t
FROM raw_input
WHERE regione IS NOT NULL
