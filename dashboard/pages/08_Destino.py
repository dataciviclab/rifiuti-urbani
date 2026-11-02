"""Destino & Costi — mix impiantistico, efficienza e autosufficienza per regione.

Legge il compose regionale `rifiuti_regioni` (grain regione x anno), che unisce
RD%, costi, mix impiantistico, movimentazione e rifiuti speciali.
"""

import pandas as pd
import plotly.express as px
import streamlit as st
from sources import (
    YEARS_REGIONI,
    fmt_eur,
    fmt_num,
    fmt_pct,
    load_mart,
    load_mart_all,
)

NORD = {
    "Piemonte",
    "Valle d'Aosta",
    "Lombardia",
    "Trentino-Alto Adige",
    "Veneto",
    "Friuli-Venezia Giulia",
    "Liguria",
    "Emilia-Romagna",
}
CENTRO = {"Toscana", "Umbria", "Marche", "Lazio"}


def macroarea(regione: str) -> str:
    if regione in NORD:
        return "Nord"
    if regione in CENTRO:
        return "Centro"
    return "Sud"


st.title("♻️ Destino & Costi")

year = st.selectbox(
    "Anno", YEARS_REGIONI, index=len(YEARS_REGIONI) - 1, key="destino_year"
)
df = load_mart("regioni", "mart_regioni", year)

if df is None or df.empty:
    st.warning("Dati regionali non disponibili.")
    st.stop()

df = df.copy()
df["macroarea"] = df["regione"].apply(macroarea)
df["organico_t"] = (
    df["compostaggio_t"].fillna(0)
    + df["trattamento_integrato_t"].fillna(0)
    + df["digestione_t"].fillna(0)
)
df["senza_organico"] = df["organico_t"] <= 0

# ── KPI nazionali ──────────────────────────────────────────────────────────
pop = df["popolazione"].sum()
ru = df["totale_ru_tonnellate"].sum()
rd = df["totale_rd_tonnellate"].sum()
rd_pct = rd / ru * 100 if ru else float("nan")

trattamenti = df["trattamenti_finali_t"].sum()
discarica = df["discarica_t"].sum()
incenerimento = df["incenerimento_t"].sum()
organico = (
    df["compostaggio_t"].sum()
    + df["trattamento_integrato_t"].sum()
    + df["digestione_t"].sum()
)
export = df["export_t"].sum()
costo = (df["ctot_euro_ab"] * df["popolazione"]).sum() / pop if pop else float("nan")

k1, k2, k3, k4 = st.columns(4)
k1.metric("RD% (pesata)", fmt_pct(rd_pct, signed=False))
k2.metric(
    "Discarica sui sink finali (TMB escluso)",
    fmt_pct(discarica / trattamenti * 100 if trattamenti else float("nan"), signed=False),
)
k3.metric("Incenerimento", f"{incenerimento / 1e6:.2f} Mt")
k4.metric("Riciclo organico", f"{organico / 1e6:.2f} Mt")

k5, k6, k7, k8 = st.columns(4)
k5.metric("RU prodotti", f"{ru / 1e6:.2f} Mt")
k6.metric(
    "Export",
    f"{export / 1e6:.2f} Mt",
    delta=f"{export / ru * 100:.1f}% del prodotto" if ru else None,
    delta_color="off",
)
k7.metric("Costo medio", fmt_eur(costo))
k8.metric(
    "Impianti",
    fmt_num(int(df["n_impianti"].fillna(0).sum())),
)

st.caption(
    "Discarica e incenerimento sono throughput impiantistico: la stessa tonnellata "
    "può transitare più volte (TMB → incenerimento/discarica). I tassi escludono il "
    "TMB (pre-trattamento) e non includono il riciclo delle frazioni secche: non "
    "sono il tasso di discarica ufficiale."
)

st.divider()

# ── Tabella regioni ────────────────────────────────────────────────────────
st.subheader("📋 Scorecard regionale")

tab = df[
    [
        "regione",
        "macroarea",
        "percentuale_rd",
        "kg_ru_per_abitante",
        "pct_discarica_su_trattamenti_finali",
        "tmb_t",
        "incenerimento_t",
        "export_su_prodotto_pct",
        "ctot_euro_ab",
        "costo_per_punto_rd_euro",
        "rs_recupero_su_gestito_pct",
        "senza_organico",
    ]
].sort_values("percentuale_rd", ascending=False)

st.dataframe(
    tab,
    width="stretch",
    hide_index=True,
    column_config={
        "regione": st.column_config.TextColumn("Regione"),
        "macroarea": st.column_config.TextColumn("Area"),
        "percentuale_rd": st.column_config.NumberColumn("RD%", format="%.1f"),
        "kg_ru_per_abitante": st.column_config.NumberColumn("kg/ab", format="%.0f"),
        "pct_discarica_su_trattamenti_finali": st.column_config.NumberColumn(
            "Discarica % (sink finali)", format="%.1f"
        ),
        "tmb_t": st.column_config.NumberColumn("TMB t (pre-tratt.)", format="%.0f"),
        "incenerimento_t": st.column_config.NumberColumn("Incenerimento t", format="%.0f"),
        "export_su_prodotto_pct": st.column_config.NumberColumn("Export %", format="%.1f"),
        "ctot_euro_ab": st.column_config.NumberColumn("Costo €/ab", format="%.0f"),
        "costo_per_punto_rd_euro": st.column_config.NumberColumn(
            "€ per punto RD", format="%.1f"
        ),
        "rs_recupero_su_gestito_pct": st.column_config.NumberColumn(
            "RS recupero %", format="%.1f"
        ),
        "senza_organico": st.column_config.CheckboxColumn("Senza organico"),
    },
)

senza = df.loc[df["organico_t"] <= 0, "regione"].tolist()
if senza:
    st.caption(
        f"⚠️ Senza impianto organico in regione nel {year}: {', '.join(senza)}. "
        "Raccolgono comunque frazione organica (export dichiarato ~0): il mix "
        "non spiega dove viene trattata. La quota discarica è calcolata sui soli "
        "sink finali, TMB escluso."
    )

st.divider()

# ── Mix impiantistico per regione ──────────────────────────────────────────
st.subheader("🏭 Mix impiantistico per regione")
st.caption(
    "Quote sui soli trattamenti finali (TMB escluso). Ogni regione somma a 100%."
)

mix_cols = {
    "discarica_t": "Discarica",
    "incenerimento_t": "Incenerimento",
    "coincenerimento_t": "Coincenerimento",
    "compostaggio_t": "Compostaggio",
    "trattamento_integrato_t": "Tratt. integrato",
    "digestione_t": "Digestione",
}

df_mix = df[["regione", "trattamenti_finali_t", *mix_cols]].copy()
for col in mix_cols:
    df_mix[col] = df_mix[col].fillna(0)
denom = df_mix["trattamenti_finali_t"].replace(0, pd.NA)
for col in mix_cols:
    df_mix[col] = df_mix[col] / denom * 100
df_mix = df_mix.rename(columns=mix_cols)

df_long = df_mix.melt(
    id_vars=["regione"],
    value_vars=list(mix_cols.values()),
    var_name="Destino",
    value_name="Quota %",
).dropna()

if not df_long.empty:
    fig_mix = px.bar(
        df_long,
        x="regione",
        y="Quota %",
        color="Destino",
        barmode="stack",
        title="Composizione dei trattamenti finali",
        category_orders={"regione": tab["regione"].tolist()},
    )
    fig_mix.update_layout(height=480, xaxis_tickangle=-45)
    st.plotly_chart(fig_mix, width="stretch")

st.divider()

# ── Efficienza: RD% vs costo per punto ─────────────────────────────────────
st.subheader("🎯 Efficienza: RD% vs costo per punto di RD")

fig_eff = px.scatter(
    df,
    x="costo_per_punto_rd_euro",
    y="percentuale_rd",
    size="popolazione",
    color="macroarea",
    hover_name="regione",
    hover_data={
        "ctot_euro_ab": ":.0f",
        "pct_discarica_su_trattamenti_finali": ":.1f",
        "popolazione": ":,.0f",
    },
    labels={
        "costo_per_punto_rd_euro": "€/ab per punto di RD%",
        "percentuale_rd": "RD%",
        "macroarea": "Area",
    },
)
fig_eff.update_layout(height=480)
st.plotly_chart(fig_eff, width="stretch")

st.caption(
    "Più in alto a sinistra = più RD% a costo unitario più basso. "
    "Il costo è la media pesata sui comuni che dichiarano il costo."
)

st.divider()

# ── Trend nazionale ────────────────────────────────────────────────────────
st.subheader("📈 Trend nazionale 2018–2024")

df_all = load_mart_all("regioni", "mart_regioni", tuple(YEARS_REGIONI))
if df_all is not None and not df_all.empty:
    trend = (
        df_all.assign(
            organico=df_all["compostaggio_t"].fillna(0)
            + df_all["trattamento_integrato_t"].fillna(0)
            + df_all["digestione_t"].fillna(0),
            costo_w=df_all["ctot_euro_ab"] * df_all["popolazione"],
        )
        .groupby("anno")
        .agg(
            discarica=("discarica_t", "sum"),
            incenerimento=("incenerimento_t", "sum"),
            organico=("organico", "sum"),
            export=("export_t", "sum"),
            costo_w=("costo_w", "sum"),
            popolazione=("popolazione", "sum"),
        )
        .reset_index()
    )
    trend["costo"] = trend["costo_w"] / trend["popolazione"]

    col1, col2 = st.columns(2)
    with col1:
        fig_trend = px.line(
            trend,
            x="anno",
            y=["discarica", "incenerimento", "organico", "export"],
            markers=True,
            title="Tonnellate per destino (Mt)",
            labels={"value": "Tonnellate", "anno": "Anno", "variable": "Voce"},
        )
        fig_trend.update_layout(height=380)
        st.plotly_chart(fig_trend, width="stretch")

    with col2:
        fig_costo = px.line(
            trend,
            x="anno",
            y="costo",
            markers=True,
            title="Costo medio (€/abitante)",
            labels={"costo": "€/ab", "anno": "Anno"},
        )
        fig_costo.update_layout(height=380)
        st.plotly_chart(fig_costo, width="stretch")

st.caption(f"Dati: ISPRA Catasto Rifiuti Nazionale · Anno {year} · CC BY 4.0")
