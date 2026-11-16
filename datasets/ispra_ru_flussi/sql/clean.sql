-- ISPRA Rifiuti Urbani — Flussi extraregionali — CLEAN
-- CSV normalizzato: anno;regione;tipo_flusso;quantita_t
--
-- Il file di origine contiene un blocco per tipo di flusso (frazione organica,
-- incenerimento, discarica). `tipo_flusso` è parte della chiave: senza,
-- leggere un solo blocco faceva sparire incenerimento e discarica.

SELECT
    anno::INTEGER AS anno,
    normalize_string(regione) AS regione,
    lower(normalize_string(tipo_flusso)) AS tipo_flusso,
    -- La fonte include una riga di totale nazionale accanto alle regioni:
    -- va marcata, altrimenti sommarla raddoppia i totali.
    lower(normalize_string(regione)) = 'italia' AS is_aggregato,
    normalize_italian_number(quantita_t) AS quantita_t
FROM raw_input
WHERE regione IS NOT NULL
  AND tipo_flusso IS NOT NULL
  AND quantita_t IS NOT NULL
