-- ISPRA RS Impianti — CLEAN
--
-- Il file ISPRA è multi-tabella: 10 sezioni di impianti (Compostaggio, TMB,
-- Incenerimento, Discarica…) più "Altre tipologie", ognuna con un header
-- diverso (da 3 a 6 colonne), e un blocco "Riepilogo" con i conteggi
-- ufficiali per tipologia.
--
-- Prima il normalizzatore applicava il primo header a tutto il file: le
-- sezioni a 6 colonne perdevano il totale e i conteggi con separatore
-- ("1.409") diventavano NULL. Risultato pubblicato: 954 impianti invece
-- di 10.563, con le 8.201 unità di recupero/stoccaggio invisibili.
--
-- Il normalizzatore ora emette una riga per (tipo impianto, area) con lo
-- schema canonico qui sotto; questo clean fa solo typing e classificazione.

SELECT
    {year}::INTEGER AS anno,
    normalize_string(tipo_impianto) AS tipo_impianto,
    -- Recupero/stoccaggio e trattamento/smaltimento non sono sommabili:
    -- il tonnellaggio delle "altre tipologie" è throughput (la stessa
    -- tonnellata transita più volte), quello dei trattamenti è conferito.
    CASE
        WHEN lower(tipo_impianto) LIKE '%recupero%'
          OR lower(tipo_impianto) LIKE '%stoccaggio%'
          OR lower(tipo_impianto) LIKE '%trattamento chimico%'
        THEN 'recupero_stoccaggio'
        ELSE 'trattamento_smaltimento'
    END AS categoria,
    normalize_string(area_geografica) AS area_geografica,
    normalize_italian_integer(numero_impianti) AS numero_impianti,
    normalize_italian_number(rs_non_pericolosi_t) AS rs_non_pericolosi_t,
    normalize_italian_number(rs_pericolosi_t) AS rs_pericolosi_t,
    -- Le "altre tipologie" non hanno una colonna Totale: si somma NP + P
    coalesce(
        normalize_italian_number(totale_t),
        coalesce(normalize_italian_number(rs_non_pericolosi_t), 0)
        + coalesce(normalize_italian_number(rs_pericolosi_t), 0)
    ) AS totale_t
FROM raw_input
WHERE tipo_impianto IS NOT NULL
  AND area_geografica IS NOT NULL
  AND numero_impianti IS NOT NULL
