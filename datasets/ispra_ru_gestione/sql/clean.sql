-- ISPRA RU Gestione — CLEAN
--
-- Il file contiene 7 sezioni impianto (Compostaggio, Trattamento integrato,
-- Digestione, TMB, Incenerimento, Coincenerimento, Discarica) più un blocco
-- "Andamento" (serie storica dei conteggi, non un dato dell'anno).
--
-- Prima il normalizzatore usava il primo header per tutte le sezioni: nello
-- stesso anno convivevano 28 righe per 4 aree, con le metriche spostate
-- nelle colonne sbagliate. Ora una riga per (tipo impianto, area).

SELECT
    {year}::INTEGER AS anno,
    normalize_string(tipo_impianto) AS tipo_impianto,
    normalize_string(area_geografica) AS area_geografica,
    normalize_italian_integer(numero_impianti) AS numero_impianti,
    normalize_italian_number(frazione_umida_t) AS frazione_umida_t,
    normalize_italian_number(verde_t) AS verde_t,
    -- "Tot. RU e tratt. RU": comprende anche il rifiuto che arriva dagli
    -- impianti di trattamento, quindi non è sommabile tra tipologie diverse
    normalize_italian_number(tot_ru_t) AS tot_ru_t,
    normalize_italian_number(fanghi_t) AS fanghi_t,
    normalize_italian_number(altro_t) AS altro_t,
    normalize_italian_number(totale_t) AS totale_t
FROM raw_input
WHERE tipo_impianto IS NOT NULL
  AND area_geografica IS NOT NULL
  AND numero_impianti IS NOT NULL
