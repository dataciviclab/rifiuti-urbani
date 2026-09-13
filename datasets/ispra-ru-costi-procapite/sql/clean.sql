-- ISPRA Rifiuti Urbani — Costi comunali pro capite — CLEAN
-- Normalized CSV: istat_comune, comune, provincia, numero_comuni, popolazione,
--                 crt, cts, crd, ctr, csl, cc, ck, ctot
-- All years have the same 13 columns after preprocessing.

SELECT
    {year}::INTEGER AS anno,
    normalize_string(istat_comune) AS codice_comune_istat,
    normalize_string(comune) AS comune_o_aggregazione,
    normalize_string(provincia) AS provincia,
    cast_bigint(remove_dot_thousands(numero_comuni)) AS numero_comuni,
    cast_bigint(remove_dot_thousands(popolazione)) AS popolazione,
    normalize_italian_number(crt) AS crt_euro_ab,
    normalize_italian_number(cts) AS cts_euro_ab,
    normalize_italian_number(crd) AS crd_euro_ab,
    normalize_italian_number(ctr) AS ctr_euro_ab,
    normalize_italian_number(csl) AS csl_euro_ab,
    normalize_italian_number(cc) AS cc_euro_ab,
    normalize_italian_number(ck) AS ck_euro_ab,
    normalize_italian_number(ctot) AS ctot_euro_ab
FROM raw_input
WHERE istat_comune IS NOT NULL
  AND comune IS NOT NULL
  AND ctot IS NOT NULL
