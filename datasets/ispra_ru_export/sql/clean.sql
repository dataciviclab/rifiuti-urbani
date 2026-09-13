SELECT
    {year}::INTEGER AS anno,
    normalize_string("Regione") AS regione,
    normalize_italian_number("Rifiuti non pericolosi(t)") AS rifiuti_non_pericolosi_t,
    normalize_italian_number("Rifiuti pericolosi (t)") AS rifiuti_pericolosi_t,
    normalize_italian_number("Totale(t)") AS totale_t
FROM raw_input
WHERE normalize_string("Regione") IS NOT NULL
  AND normalize_string("Regione") NOT LIKE '%Regione%'
