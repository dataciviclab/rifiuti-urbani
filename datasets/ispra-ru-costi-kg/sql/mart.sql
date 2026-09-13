-- mart_comuni — ISPRA Rifiuti Urbani Costi per kg: arricchimento + benchmark
--
-- Stessa cardinalità del clean (1 riga = 1 comune × anno).
-- Ogni riga arricchita con:
--   • media nazionale/provinciale dei costi
--   • percentile nazionale
--   • fascia qualitativa
--   • distanza % dalla media nazionale/provinciale
--   • rank per provincia

with
base as (
    select
        anno,
        codice_comune_istat,
        comune_o_aggregazione as comune,
        provincia,
        popolazione,
        crt_cent_kg,
        crd_cent_kg,
        csl_cent_kg,
        cc_cent_kg,
        ck_cent_kg,
        ctot_cent_kg
    from clean_input
    where popolazione > 0
),
enriched as (
    select
        *,
        -- Media nazionale costi totali
        round(avg(ctot_cent_kg) over (partition by anno), 2) as media_nazionale_ctot,
        -- Media provinciale costi totali
        round(avg(ctot_cent_kg) over (partition by anno, provincia), 2) as media_provinciale_ctot,
        -- Percentile nazionale (0 = più basso, 1 = più alto)
        case
            when ctot_cent_kg is null then null
            else round(percent_rank() over (partition by anno order by ctot_cent_kg), 4)
        end as percentile_nazionale,
        -- Distanza % dalla media nazionale
        case
            when avg(ctot_cent_kg) over (partition by anno) <> 0
            then round((ctot_cent_kg - avg(ctot_cent_kg) over (partition by anno))
                 / abs(avg(ctot_cent_kg) over (partition by anno)) * 100, 2)
        end as distanza_media_nazionale_pct,
        -- Distanza % dalla media provinciale
        case
            when avg(ctot_cent_kg) over (partition by anno, provincia) <> 0
            then round((ctot_cent_kg - avg(ctot_cent_kg) over (partition by anno, provincia))
                 / abs(avg(ctot_cent_kg) over (partition by anno, provincia)) * 100, 2)
        end as distanza_media_provinciale_pct,
        -- Fascia qualitativa basata su percentile
        case
            when ctot_cent_kg is null then null
            when percent_rank() over (partition by anno order by ctot_cent_kg) >= 0.8 then 'ELEVATO'
            when percent_rank() over (partition by anno order by ctot_cent_kg) >= 0.6 then 'SOPRA_MEDIA'
            when percent_rank() over (partition by anno order by ctot_cent_kg) >= 0.4 then 'MEDIA'
            when percent_rank() over (partition by anno order by ctot_cent_kg) >= 0.2 then 'SOTTO_MEDIA'
            else 'BASSO'
        end as fascia_costi,
        -- Rank per provincia (1 = costo più alto nella provincia)
        case
            when ctot_cent_kg is null then null
            else row_number() over (partition by anno, provincia order by ctot_cent_kg desc)
        end as rank_provincia
    from base
)
select * from enriched
order by anno, provincia, comune;
