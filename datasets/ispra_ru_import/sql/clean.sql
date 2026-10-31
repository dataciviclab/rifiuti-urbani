SELECT
    anno::INTEGER AS anno,
    normalize_string(regione) AS regione,
    -- La fonte include una riga di totale nazionale accanto alle regioni:
    -- va marcata, altrimenti sommarla raddoppia i totali (bug export 2x).
    lower(normalize_string(regione)) = 'italia' AS is_aggregato,
    normalize_italian_number(non_pericolosi_t) AS rifiuti_non_pericolosi_t,
    normalize_italian_number(pericolosi_t) AS rifiuti_pericolosi_t,
    normalize_italian_number(totale_t) AS totale_t
FROM raw_input
WHERE regione IS NOT NULL
  AND regione NOT LIKE '%Regione%'
