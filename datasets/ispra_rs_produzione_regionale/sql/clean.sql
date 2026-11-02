-- ISPRA RS Produzione — CLEAN
--
-- Il file contiene 7 tabelle: dati di sintesi per area, poi la produzione per
-- attività economica e per capitolo EER, ognuna in versione totale /
-- non pericolosi / pericolosi. Accatastarle come un'unica tabella (come
-- faceva il vecchio parser) produceva 3 righe per settore con le metriche
-- spostate.
--
-- Il normalizzatore emette la forma lunga:
-- una riga per (dimensione, etichetta, area, ripartizione).

SELECT
    {year}::INTEGER AS anno,
    normalize_string(dimensione) AS dimensione,
    normalize_string(etichetta) AS etichetta,
    normalize_string(area_geografica) AS area_geografica,
    normalize_string(ripartizione) AS ripartizione,
    normalize_italian_number(np_t) AS np_t,
    normalize_italian_number(p_t) AS p_t,
    normalize_italian_number(cer_nd_t) AS cer_nd_t,
    -- `totale_t` è valorizzato solo per la ripartizione "totale": per le
    -- righe np/p resta NULL, così una somma per ripartizione non conta
    -- tre volte lo stesso rifiuto.
    normalize_italian_number(totale_t) AS totale_t
FROM raw_input
WHERE dimensione IS NOT NULL
  AND etichetta IS NOT NULL
  AND area_geografica IS NOT NULL
