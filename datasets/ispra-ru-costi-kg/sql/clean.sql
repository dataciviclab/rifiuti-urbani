-- ISPRA Rifiuti Urbani — Costi comunali per kg — CLEAN
-- Normalized CSV: istat_comune, comune, provincia, numero_comuni, popolazione,
--                 crt, cts, crd, ctr, csl, cc, ck, ctot
-- Costi kg has: crt, crd, csl, cc, ck, ctot (cts/ctr empty)

SELECT
    {year}::INTEGER AS anno,
    normalize_string(istat_comune) AS codice_comune_istat,
    normalize_string(comune) AS comune_o_aggregazione,
    normalize_string(provincia) AS provincia,
    cast_bigint(remove_dot_thousands(numero_comuni)) AS numero_comuni,
    cast_bigint(remove_dot_thousands(popolazione)) AS popolazione,
    normalize_italian_number(crt) AS crt_cent_kg,
    normalize_italian_number(crd) AS crd_cent_kg,
    normalize_italian_number(csl) AS csl_cent_kg,
    normalize_italian_number(cc) AS cc_cent_kg,
    normalize_italian_number(ck) AS ck_cent_kg,
    normalize_italian_number(ctot) AS ctot_cent_kg
FROM raw_input
WHERE istat_comune IS NOT NULL
  AND comune IS NOT NULL
  AND ctot IS NOT NULL
