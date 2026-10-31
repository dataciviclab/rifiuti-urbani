-- ISPRA Rifiuti Urbani — CLEAN
-- Macro toolkit: cast_int, cast_bigint, cast_double, normalize_string, remove_dot_thousands
--
-- Unità di rilevazione: comune OPPURE aggregazione di comuni.
-- ISPRA attribuisce i dati di alcuni comuni a un'unione ("Aggregazione: X"):
-- la riga del capofila porta i dati dell'intera unione, i comuni aderenti
-- ("Vedi aggregazione: X") portano solo la popolazione.
-- Scartare le aggregazioni (come si faceva prima) perdeva 20 unità e 114
-- comuni: la Valle d'Aosta restava con il solo comune di Aosta.
--
-- La popolazione dell'unità è quindi capofila + comuni aderenti; è la base
-- corretta per i pro-capite. Le righe "Vedi aggregazione" non hanno metriche
-- e servono solo a ricostruire la popolazione, quindi non entrano in output.

WITH parsed AS (
    SELECT
        {year}::INTEGER AS anno,
        normalize_string(replace("IstatComune", chr(9), '')) AS codice_comune_istat,
        normalize_string("Regione") AS regione,
        normalize_string("Provincia") AS provincia,
        normalize_string("Comune") AS comune,
        cast_bigint(remove_dot_thousands("Popolazione")) AS popolazione_comune,
        normalize_string("Dato riferito a") AS dato_riferito_a,
        -- Frazioni merceologiche
        normalize_italian_number("Frazione umida(1) (t)") AS frazione_umida_t,
        normalize_italian_number("Verde (t)") AS verde_t,
        normalize_italian_number("Carta e cartone (t)") AS carta_t,
        normalize_italian_number("Vetro (t)") AS vetro_t,
        normalize_italian_number("Legno (t)") AS legno_t,
        normalize_italian_number("Metallo (t)") AS metallo_t,
        normalize_italian_number("Plastica (t)") AS plastica_t,
        normalize_italian_number("RAEE (t)") AS raee_t,
        normalize_italian_number("Tessili (t)") AS tessili_t,
        normalize_italian_number("Selettiva (t)") AS selettiva_t,
        normalize_italian_number("Rifiuti da C e D (t)") AS cd_t,
        normalize_italian_number("Pulizia stradale a recupero (t)") AS pulizia_stradale_t,
        normalize_italian_number("Ingombranti misti a recupero (t)") AS ingombranti_t,
        normalize_italian_number("Altro (t)") AS altro_t,
        normalize_italian_number("Ingombranti a smaltimento (t)") AS ingombranti_smalt_t,
        normalize_italian_number("Indifferenziato (t)") AS indifferenziato_t,
        -- Totali
        normalize_italian_number("Totale RD (t)") AS totale_rd_tonnellate,
        normalize_italian_number("Totale RU (t)") AS totale_ru_tonnellate,
        -- Il campo ISPRA contiene "  64,79%" (con spazi e % finale)
        normalize_italian_number(replace("Percentuale RD (%)", '%', '')) AS percentuale_rd
    FROM raw_input
    WHERE normalize_string(replace("IstatComune", chr(9), '')) IS NOT NULL
),
classificato AS (
    SELECT
        *,
        CASE
            WHEN dato_riferito_a LIKE 'Aggregazione:%'      THEN 'Aggregazione'
            WHEN dato_riferito_a LIKE 'Vedi aggregazione:%' THEN 'Vedi aggregazione'
            ELSE 'Comune'
        END AS tipo_dato,
        NULLIF(TRIM(SPLIT_PART(dato_riferito_a, ':', 2)), '') AS aggregazione
    FROM parsed
),
con_popolazione_unita AS (
    -- La window deve vedere anche le righe "Vedi aggregazione" (che portano
    -- solo la popolazione), quindi si calcola qui e si filtra dopo.
    SELECT
        *,
        CAST(
            SUM(popolazione_comune) OVER (
                PARTITION BY anno, regione, COALESCE(aggregazione, codice_comune_istat)
            ) AS BIGINT
        ) AS popolazione_unita
    FROM classificato
)
SELECT
    anno,
    codice_comune_istat,
    regione,
    provincia,
    comune,
    -- Popolazione dell'unità: capofila + comuni aderenti all'aggregazione
    popolazione_unita AS popolazione,
    dato_riferito_a,
    tipo_dato,
    aggregazione,
    frazione_umida_t,
    verde_t,
    carta_t,
    vetro_t,
    legno_t,
    metallo_t,
    plastica_t,
    raee_t,
    tessili_t,
    selettiva_t,
    cd_t,
    pulizia_stradale_t,
    ingombranti_t,
    altro_t,
    ingombranti_smalt_t,
    indifferenziato_t,
    totale_rd_tonnellate,
    totale_ru_tonnellate,
    percentuale_rd
FROM con_popolazione_unita
WHERE tipo_dato <> 'Vedi aggregazione'
  AND popolazione_comune IS NOT NULL
