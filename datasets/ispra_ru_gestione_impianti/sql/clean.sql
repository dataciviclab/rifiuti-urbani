-- ISPRA RU Gestione per impianto — CLEAN
--
-- L'elenco completo impianti non espone un ID impianto: più impianti dello
-- stesso tipo nello stesso comune arrivano come righe distinte. Il grain
-- pubblico è quindi (tipo impianto, regione, provincia, comune);
-- `n_impianti` conserva quanti impianti sono stati aggregati, mentre le
-- tonnellate sono sommate.
--
-- ATTENZIONE: `tot_ru_t` e `totale_t` comprendono anche il rifiuto in arrivo
-- dagli impianti di trattamento. Non vanno sommati tra tipologie diverse:
-- la stessa tonnellata transita più volte lungo la filiera.

SELECT
    {year}::INTEGER AS anno,
    normalize_string(tipo_impianto) AS tipo_impianto,
    normalize_string(regione) AS regione,
    normalize_string(provincia) AS provincia,
    normalize_string(comune) AS comune,
    count(*) AS n_impianti,
    sum(normalize_italian_number(frazione_umida_t)) AS frazione_umida_t,
    sum(normalize_italian_number(verde_t)) AS verde_t,
    sum(normalize_italian_number(tot_ru_t)) AS tot_ru_t,
    sum(normalize_italian_number(fanghi_t)) AS fanghi_t,
    sum(normalize_italian_number(altro_t)) AS altro_t,
    sum(normalize_italian_number(totale_t)) AS totale_t
FROM raw_input
WHERE tipo_impianto IS NOT NULL
  AND regione IS NOT NULL
  AND comune IS NOT NULL
GROUP BY anno, tipo_impianto, regione, provincia, comune
