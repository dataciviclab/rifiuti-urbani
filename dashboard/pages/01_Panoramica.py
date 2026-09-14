"""Panoramica — KPI nazionali e trend 2018-2024."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from sources import load_mart, load_mart_all, fmt_eur, fmt_num, fmt_pct, YEARS

st.title("📊 Panoramica Nazionale")

year = st.selectbox("Anno", YEARS, index=len(YEARS) - 1, key="panoramica_year")

# ── KPI principali ────────────────────────────────────────────────────────
df = load_mart("base", "mart_comuni", year)

if df is None or df.empty:
    st.warning("Nessun dato disponibile.")
    st.stop()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Popolazione", fmt_num(df['popolazione'].sum()))
k2.metric("Produzione RU", f"{fmt_num(int(df['totale_ru_tonnellate'].sum()))} t")
k3.metric("Raccolta Differenziata", f"{fmt_num(int(df['totale_rd_tonnellate'].sum()))} t")
k4.metric("RD%", fmt_pct(df['percentuale_rd'].mean()))

k5, k6, k7, k8 = st.columns(4)
kg_procapite = df['totale_ru_tonnellate'].sum() * 1e6 / df['popolazione'].sum()
k5.metric("Procapite", f"{kg_procapite:.1f} kg/ab")
k6.metric("Comuni", fmt_num(len(df)))

try:
    costi = load_mart("costi_pc", "mart_comuni", year)
    if costi is not None and not costi.empty:
        k7.metric("Costo Medio", fmt_eur(costi['ctot_euro_ab'].mean()))
    else:
        k7.metric("Costo Medio", "N/A")
except Exception:
    k7.metric("Costo Medio", "N/A")

rd_pct = df['percentuale_rd'].mean()
k8.metric("Obiettivo UE 65%", fmt_pct(rd_pct), delta=f"{rd_pct - 65.0:+.1f}pp")

st.divider()

# ── Trend (usa load_mart_all) ─────────────────────────────────────────────
st.subheader("📈 Trend 2018-2024")

df_trend_base = load_mart_all("base", "mart_comuni", tuple(YEARS))
if df_trend_base is not None and not df_trend_base.empty:
    df_trend = df_trend_base.groupby('anno').agg(
        produzione=('totale_ru_tonnellate', 'sum'),
        rd=('totale_rd_tonnellate', 'sum'),
        rd_pct=('percentuale_rd', 'mean'),
    ).reset_index()

    col1, col2 = st.columns(2)
    with col1:
        fig_rd = px.line(df_trend, x='anno', y='rd_pct', markers=True,
                         title="RD% Nazionale", labels={'rd_pct': 'RD%', 'anno': 'Anno'})
        fig_rd.add_hline(y=65, line_dash="dash", line_color="red", annotation_text="Obiettivo UE 65%")
        fig_rd.update_layout(height=350)
        st.plotly_chart(fig_rd, width="stretch")
    with col2:
        fig_prod = go.Figure()
        fig_prod.add_trace(go.Bar(x=df_trend['anno'], y=df_trend['produzione'], name='Produzione', marker_color='#3b82f6'))
        fig_prod.add_trace(go.Bar(x=df_trend['anno'], y=df_trend['rd'], name='Raccolta Differenziata', marker_color='#22c55e'))
        fig_prod.update_layout(title="Produzione vs Raccolta Differenziata", barmode='group', height=350)
        st.plotly_chart(fig_prod, width="stretch")

    st.subheader("💰 Trend Costi Gestione")
    df_trend_costi = load_mart_all("costi_pc", "mart_comuni", tuple(YEARS))
    if df_trend_costi is not None and not df_trend_costi.empty:
        df_costi = df_trend_costi.groupby('anno').agg(
            media=('ctot_euro_ab', 'mean'),
            mediana=('ctot_euro_ab', 'median'),
        ).reset_index()
        fig_costi = px.line(df_costi, x='anno', y=['media', 'mediana'], markers=True,
                            title="Costo Gestione per Abitante",
                            labels={'value': 'EUR/ab', 'anno': 'Anno', 'variable': 'Metrica'})
        fig_costi.update_layout(height=350)
        st.plotly_chart(fig_costi, width="stretch")

st.caption(f"Dati: ISPRA Catasto Rifiuti Nazionale · Anno {year} · CC BY 4.0")
