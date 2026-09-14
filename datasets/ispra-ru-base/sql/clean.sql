-- ISPRA Rifiuti Urbani — CLEAN
-- Macro toolkit: cast_int, cast_bigint, cast_double, normalize_string, remove_dot_thousands
SELECT
    {year}::INTEGER AS anno,
    normalize_string(replace("IstatComune", chr(9), '')) AS codice_comune_istat,
    normalize_string("Regione") AS regione,
    normalize_string("Provincia") AS provincia,
    normalize_string("Comune") AS comune,
    cast_bigint(remove_dot_thousands("Popolazione")) AS popolazione,
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
  AND normalize_string("Dato riferito a") = 'Comune'
  AND cast_bigint(remove_dot_thousands("Popolazione")) IS NOT NULL
