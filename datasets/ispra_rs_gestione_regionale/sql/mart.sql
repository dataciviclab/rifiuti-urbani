-- mart_gestione — ISPRA RS Gestione
--
-- Da forma lunga (una riga per codice operazione) a una riga per
-- (anno, area, ripartizione, tipo operazione), con flussi e giacenze
-- **separati**: R13/D15 sono rifiuti in giacenza al 31/12, non trattati
-- nell'anno, e sommarli ai flussi gonfia i totali di ~18 Mt.
--
-- Le righe Italia non entrano nel mart: i valori nazionali sono colonne.

WITH per_area AS (
    SELECT
        anno,
        area_geografica,
        ripartizione,
        tipo_operazione,
        SUM(CASE WHEN natura = 'flusso' THEN quantita_t ELSE 0 END) AS flussi_t,
        SUM(CASE WHEN natura = 'giacenza' THEN quantita_t ELSE 0 END) AS giacenza_t
    FROM clean_input
    GROUP BY anno, area_geografica, ripartizione, tipo_operazione
),
arricchito AS (
    SELECT
        *,
        MAX(CASE WHEN area_geografica = 'Italia' THEN flussi_t END)
            OVER (PARTITION BY anno, ripartizione, tipo_operazione) AS flussi_italia_t,
        MAX(CASE WHEN area_geografica = 'Italia' THEN giacenza_t END)
            OVER (PARTITION BY anno, ripartizione, tipo_operazione) AS giacenza_italia_t
    FROM per_area
)
SELECT
    anno,
    area_geografica,
    ripartizione,
    tipo_operazione,
    ROUND(flussi_t, 0) AS flussi_t,
    ROUND(giacenza_t, 0) AS giacenza_t,
    ROUND(flussi_t + giacenza_t, 0) AS totale_t,
    ROUND(flussi_italia_t, 0) AS flussi_italia_t,
    ROUND(giacenza_italia_t, 0) AS giacenza_italia_t,
    ROUND(flussi_t * 100.0 / NULLIF(flussi_italia_t, 0), 2) AS pct_flussi_italia
FROM arricchito
WHERE area_geografica <> 'Italia'
ORDER BY anno, ripartizione, tipo_operazione, flussi_t DESC
