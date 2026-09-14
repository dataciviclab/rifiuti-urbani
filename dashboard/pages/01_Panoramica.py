"""Panoramica — KPI nazionali e trend 2018-2024."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from sources import load_mart, YEARS

st.title("📊 Panoramica Nazionale")

year = st.selectbox("Anno", YEARS, index=len(YEARS) - 1, key="panoramica_year")

# ── KPI principali (dal mart) ─────────────────────────────────────────────
df = load_mart("base", "mart_comuni", year)

if df is None or df.empty:
    st.warning("Nessun dato disponibile.")
    st.stop()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Popolazione", f"{df['popolazione'].sum():,.0f}")
k2.metric("Produzione RU", f"{df['totale_ru_tonnellate'].sum():,.0f} t")
k3.metric("Raccolta Differenziata", f"{df['totale_rd_tonnellate'].sum():,.0f} t")
k4.metric("RD%", f"{df['percentuale_rd'].mean():.1f}%")

k5, k6, k7, k8 = st.columns(4)
k5.metric("Procapite", f"{(df['totale_ru_tonnellate'].sum() * 1e6 / df['popolazione'].sum()):.1f} kg/ab")
k6.metric("Comuni", f"{len(df):,}")

try:
    from sources import load_mart as load_costi
    costi = load_costi("costi_pc", "mart_comuni", year)
    if costi is not None and not costi.empty:
        k7.metric("Costo Medio", f"{costi['ctot_euro_ab'].mean():.2f} EUR/ab")
    else:
        k7.metric("Costo Medio", "N/A")
except Exception:
    k7.metric("Costo Medio", "N/A")

rd_pct = df['percentuale_rd'].mean()
k8.metric("Obiettivo UE 65%", f"{rd_pct:.1f}%", delta=f"{rd_pct - 65.0:+.1f}pp")

st.divider()

# ── Trend ──────────────────────────────────────────────────────────────────
st.subheader("📈 Trend 2018-2024")
trend_data = []
for y in YEARS:
    try:
        m = load_mart("base", "mart_comuni", y)
        if m is not None and not m.empty:
            trend_data.append({
                'anno': y,
                'produzione': m['totale_ru_tonnellate'].sum(),
                'rd': m['totale_rd_tonnellate'].sum(),
                'rd_pct': m['percentuale_rd'].mean(),
            })
    except Exception:
        pass

if trend_data:
    df_trend = pd.DataFrame(trend_data)
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
    costi_trend = []
    for y in YEARS:
        try:
            c = load_mart("costi_pc", "mart_comuni", y)
            if c is not None and not c.empty:
                costi_trend.append({
                    'anno': y,
                    'media': c['ctot_euro_ab'].mean(),
                    'mediana': c['ctot_euro_ab'].median(),
                })
        except Exception:
            pass
    if costi_trend:
        df_costi = pd.DataFrame(costi_trend)
        fig_costi = px.line(df_costi, x='anno', y=['media', 'mediana'], markers=True,
                            title="Costo Gestione per Abitante", labels={'value': 'EUR/ab', 'anno': 'Anno'})
        fig_costi.update_layout(height=350)
        st.plotly_chart(fig_costi, width="stretch")

st.caption(f"Dati: ISPRA Catasto Rifiuti Nazionale · Anno {year} · CC BY 4.0")
