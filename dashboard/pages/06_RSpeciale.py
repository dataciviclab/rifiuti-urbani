"""Speciale — Analisi rifiuti speciali (produzione, gestione, impianti)."""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sources import YEARS_RS, fmt_num, load_mart, load_mart_all

st.title("🏭 Rifiuti Speciali")

year = st.selectbox("Anno", YEARS_RS, index=len(YEARS_RS) - 1, key="rs_year")

df_prod = load_mart("ispra_rs_produzione", "mart_produzione", year)
df_gest = load_mart("ispra_rs_gestione", "mart_gestione", year)
df_imp = load_mart("ispra_rs_impianti", "mart_impianti", year)

if df_prod is None or df_prod.empty:
    st.warning("Dati RS non disponibili.")
    st.stop()

# Nei mart le righe Italia non ci sono: i valori nazionali arrivano come
# colonne (totale_italia_t, flussi_italia_t, n_italia_tipo).
prod_area = df_prod[(df_prod["dimensione"] == "area") & (df_prod["ripartizione"] == "totale")]

# ── KPI Nazionale ──────────────────────────────────────────────────────────
st.subheader("📊 Panoramica Nazionale RS")

k1, k2, k3, k4 = st.columns(4)
if not prod_area.empty:
    riga = prod_area.iloc[0]
    k1.metric("Produzione Totale RS", f"{riga['totale_italia_t'] / 1e6:.1f} M t")
    k2.metric("RS Non Pericolose", f"{riga['np_italia_t'] / 1e6:.1f} M t")
    k3.metric("RS Pericolose", f"{riga['p_italia_t'] / 1e6:.1f} M t")

if df_imp is not None and not df_imp.empty:
    tipi = df_imp.drop_duplicates("tipo_impianto")
    k4.metric("Impianti (Italia)", fmt_num(int(tipi["n_italia_tipo"].fillna(0).sum())))

st.caption(
    "Il conteggio impianti include recupero e stoccaggio: dal 2023 ISPRA "
    "pubblica anche le 'altre tipologie', prima assenti."
)

st.divider()

# ── Produzione per area geografica ─────────────────────────────────────────
st.subheader("📊 Produzione RS per Area Geografica")

if not prod_area.empty:
    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(prod_area, x="area_geografica", y="totale_t",
                     color="area_geografica",
                     title="Produzione Totale RS",
                     labels={"totale_t": "Tonnellate", "area_geografica": "Area"})
        fig.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig, width="stretch")

    with col2:
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name="Non Pericolose", x=prod_area["area_geografica"],
                              y=prod_area["np_t"], marker_color="#3b82f6"))
        fig2.add_trace(go.Bar(name="Pericolose", x=prod_area["area_geografica"],
                              y=prod_area["p_t"], marker_color="#ef4444"))
        fig2.update_layout(title="Composizione RS per Area", barmode="group", height=350)
        st.plotly_chart(fig2, width="stretch")

st.divider()

# ── Trend produzione RS ────────────────────────────────────────────────────
st.subheader("📈 Trend Produzione RS")

df_trend_all = load_mart_all("ispra_rs_produzione", "mart_produzione", tuple(YEARS_RS))
if df_trend_all is not None and not df_trend_all.empty:
    trend = df_trend_all[
        (df_trend_all["dimensione"] == "area") & (df_trend_all["ripartizione"] == "totale")
    ].drop_duplicates("anno")
    if not trend.empty:
        fig_trend = px.line(trend, x="anno", y="totale_italia_t", markers=True,
                            title="Produzione RS Nazionale",
                            labels={"totale_italia_t": "Tonnellate", "anno": "Anno"})
        fig_trend.update_layout(height=350)
        st.plotly_chart(fig_trend, width="stretch")

st.divider()

# ── Gestione RS ────────────────────────────────────────────────────────────
st.subheader("🔄 Gestione RS: recupero e smaltimento")

if df_gest is not None and not df_gest.empty:
    gest = df_gest[df_gest["ripartizione"] == "totale"].copy()
    fig_gest = px.bar(
        gest, x="area_geografica", y="flussi_t", color="tipo_operazione",
        barmode="group", title="Rifiuti speciali gestiti (flussi, esclusa giacenza)",
        labels={"flussi_t": "Tonnellate", "area_geografica": "Area",
                "tipo_operazione": "Operazione"},
    )
    fig_gest.update_layout(height=400)
    st.plotly_chart(fig_gest, width="stretch")
    st.caption(
        "R13 e D15 sono giacenze a fine anno, non flussi: sono tenute separate "
        "nella colonna `giacenza_t`."
    )

st.divider()

# ── Impianti ───────────────────────────────────────────────────────────────
st.subheader("🏗️ Impianti di Gestione RS per tipologia")

if df_imp is not None and not df_imp.empty:
    tipi = (
        df_imp.drop_duplicates("tipo_impianto")
        .sort_values("totale_italia_tipo", ascending=False)
        .head(12)
    )

    col1, col2 = st.columns(2)

    with col1:
        fig_imp = px.bar(tipi, x="n_italia_tipo", y="tipo_impianto", orientation="h",
                         color="categoria",
                         title="Numero impianti (Italia)",
                         labels={"n_italia_tipo": "Impianti", "tipo_impianto": ""})
        fig_imp.update_layout(height=420, showlegend=True)
        st.plotly_chart(fig_imp, width="stretch")

    with col2:
        fig_cap = px.bar(tipi, x="totale_italia_tipo", y="tipo_impianto", orientation="h",
                         color="categoria",
                         title="Rifiuti trattati (Italia)",
                         labels={"totale_italia_tipo": "Tonnellate", "tipo_impianto": ""})
        fig_cap.update_layout(height=420, showlegend=False)
        st.plotly_chart(fig_cap, width="stretch")

    st.caption(
        "I tonnellaggi degli impianti di recupero e stoccaggio sono throughput "
        "(lo stesso rifiuto transita più volte) e non vanno sommati a quelli "
        "degli impianti di trattamento e smaltimento."
    )

st.caption(f"Dati: ISPRA Catasto Rifiuti Speciali · Anno {year} · CC BY 4.0")
