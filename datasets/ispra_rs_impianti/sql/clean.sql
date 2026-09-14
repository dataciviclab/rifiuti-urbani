-- ISPRA RS Impianti — CLEAN
-- Aggrega per area geografica sommando i valori

SELECT
    anno,
    area_geografica,
    sum(numero_impianti) AS numero_impianti,
    sum(fanghi_t) AS fanghi_t,
    sum(altri_rs_t) AS altri_rs_t,
    sum(totale_rs_t) AS totale_rs_t
FROM (
    SELECT
        {year}::INTEGER AS anno,
        normalize_string(sezione) AS area_geografica,
        cast_bigint(col1) AS numero_impianti,
        normalize_italian_number(col2) AS fanghi_t,
        normalize_italian_number(col3) AS altri_rs_t,
        normalize_italian_number(col4) AS totale_rs_t
    FROM raw_input
    WHERE sezione IS NOT NULL
      AND sezione != ''
      AND sezione IN ('Nord', 'Centro', 'Sud', 'Italia')
)
GROUP BY anno, area_geografica
