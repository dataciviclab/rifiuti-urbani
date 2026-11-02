"""Impianti — dove sono e quanto trattano gli impianti che gestiscono RU."""

import plotly.express as px
import streamlit as st
from sources import YEARS_IMPIANTI, fmt_num, load_mart

st.title("🏗️ Impianti RU")

year = st.selectbox(
    "Anno", YEARS_IMPIANTI, index=len(YEARS_IMPIANTI) - 1, key="impianti_year"
)
df = load_mart("ru_gestione_impianti", "mart_impianti", year)

if df is None or df.empty:
    st.warning("Dati impianti non disponibili.")
    st.stop()

tipi = sorted(df["tipo_impianto"].dropna().unique())
regioni = sorted(df["regione"].dropna().unique())

c1, c2 = st.columns(2)
with c1:
    tipi_sel = st.multiselect("Tipo impianto", tipi, default=tipi, key="imp_tipi")
with c2:
    regioni_sel = st.multiselect("Regione", regioni, default=regioni, key="imp_regioni")

dff = df[df["tipo_impianto"].isin(tipi_sel) & df["regione"].isin(regioni_sel)]
if dff.empty:
    st.warning("Nessun impianto con i filtri selezionati.")
    st.stop()

k1, k2, k3 = st.columns(3)
k1.metric("Impianti", fmt_num(int(dff["n_impianti"].fillna(0).sum())))
k2.metric("Comuni con impianti", fmt_num(dff["comune"].nunique()))
k3.metric("Tonnellate (throughput)", f"{dff['totale_t'].fillna(0).sum() / 1e6:.2f} Mt")

st.caption(
    "Le tonnellate sono throughput impiantistico e non vanno sommate tra "
    "tipologie diverse: la stessa tonnellata può passare da TMB a "
    "incenerimento/discarica. Il conteggio impianti è invece sommabile."
)

# ── Top comuni ─────────────────────────────────────────────────────────────
top = (
    dff.assign(
        etichetta=dff["comune"].str.title() + " (" + dff["provincia"].str.title() + ")"
    )
    .groupby(["etichetta", "regione"], as_index=False)
    .agg(n_impianti=("n_impianti", "sum"), totale_t=("totale_t", "sum"))
    .sort_values("totale_t", ascending=False)
    .head(20)
)

if not top.empty:
    fig = px.bar(
        top,
        x="totale_t",
        y="etichetta",
        orientation="h",
        color="regione",
        title="Top 20 comuni per tonnellate trattate",
        labels={"totale_t": "Tonnellate", "etichetta": "", "regione": "Regione"},
    )
    fig.update_layout(height=560, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, width="stretch")

# ── Per tipo impianto ──────────────────────────────────────────────────────
per_tipo = (
    dff.groupby("tipo_impianto", as_index=False)
    .agg(n_impianti=("n_impianti", "sum"), totale_t=("totale_t", "sum"))
    .sort_values("totale_t", ascending=False)
)

if not per_tipo.empty:
    fig2 = px.bar(
        per_tipo,
        x="totale_t",
        y="tipo_impianto",
        orientation="h",
        title="Tonnellate per tipo impianto",
        labels={"totale_t": "Tonnellate", "tipo_impianto": ""},
    )
    fig2.update_layout(height=440, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig2, width="stretch")

# ── Tabella ────────────────────────────────────────────────────────────────
st.subheader("📋 Dettaglio comuni")
st.dataframe(
    top.rename(
        columns={
            "etichetta": "Comune",
            "regione": "Regione",
            "n_impianti": "Impianti",
            "totale_t": "Tonnellate",
        }
    ),
    width="stretch",
    hide_index=True,
)

st.caption(f"Dati: ISPRA Catasto Rifiuti Nazionale · Anno {year} · CC BY 4.0")
