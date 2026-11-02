-- mart_gestione — ISPRA RU Gestione
--
-- Una riga per (anno, tipo impianto, area), con il totale Italia dello stesso
-- tipo come colonna (non come riga: sommarla alle aree raddoppia i totali).
--
-- ATTENZIONE: `tot_ru_t` e `totale_t` includono anche il rifiuto in arrivo
-- dagli impianti di trattamento ("Tot. RU e tratt. RU"). Sommare i totali di
-- tipologie diverse conta più volte la stessa tonnellata lungo la filiera:
-- per i confronti territoriali usare `numero_impianti` o la singola
-- tipologia, non la somma dei totali.

WITH arricchito AS (
    SELECT
        anno,
        tipo_impianto,
        area_geografica,
        numero_impianti,
        frazione_umida_t,
        verde_t,
        tot_ru_t,
        fanghi_t,
        altro_t,
        totale_t,
        MAX(CASE WHEN area_geografica = 'Italia' THEN numero_impianti END)
            OVER (PARTITION BY anno, tipo_impianto) AS n_italia_tipo,
        MAX(CASE WHEN area_geografica = 'Italia' THEN totale_t END)
            OVER (PARTITION BY anno, tipo_impianto) AS totale_italia_tipo
    FROM clean_input
)
SELECT
    anno,
    tipo_impianto,
    area_geografica,
    numero_impianti,
    frazione_umida_t,
    verde_t,
    tot_ru_t,
    fanghi_t,
    altro_t,
    totale_t,
    n_italia_tipo,
    totale_italia_tipo,
    ROUND(totale_t * 100.0 / NULLIF(totale_italia_tipo, 0), 2) AS pct_italia_tipo
FROM arricchito
WHERE area_geografica <> 'Italia'
ORDER BY anno, tipo_impianto, totale_t DESC
