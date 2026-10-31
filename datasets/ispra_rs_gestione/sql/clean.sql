-- ISPRA RS Gestione — CLEAN
--
-- Il file contiene 7 blocchi: sintesi (R1-R12 + R13, D1-D14 + D15), operazioni
-- di recupero e di smaltimento nelle tre ripartizioni (totale, non pericolosi,
-- pericolosi). Il normalizzatore emette la forma lunga:
-- una riga per (area, ripartizione, codice operazione).
--
-- `natura` distingue i flussi (R1-R12, D1-D14) dalle giacenze a fine anno
-- (R13, D15): sommarle insieme gonfia i totali di ~18 Mt.

SELECT
    {year}::INTEGER AS anno,
    normalize_string(area_geografica) AS area_geografica,
    normalize_string(ripartizione) AS ripartizione,
    normalize_string(tipo_operazione) AS tipo_operazione,
    normalize_string(codice) AS codice,
    normalize_string(natura) AS natura,
    normalize_italian_number(quantita_t) AS quantita_t
FROM raw_input
WHERE area_geografica IS NOT NULL
  AND codice IS NOT NULL
