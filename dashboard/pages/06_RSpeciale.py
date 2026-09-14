"""Speciale — Analisi rifiuti speciali (produzione, gestione, impianti)."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from sources import load_mart, load_mart_all, fmt_num, fmt_pct, safe_int, YEARS

st.title("🏭 Rifiuti Speciali")

year = st.selectbox("Anno", YEARS, index=len(YEARS) - 1, key="rs_year")

# ── KPI Nazionale ──────────────────────────────────────────────────────────
st.subheader("📊 Panoramica Nazionale RS")

df_prod = load_mart("produzione_rs", "mart_produzione", year)
df_gest = load_mart("gestione_rs", "mart_gestione", year)
df_imp = load_mart("impianti_rs", "mart_impianti", year)

if df_prod is not None and not df_prod.empty:
    # Get Italia row
    italia_prod = df_prod[df_prod['area_geografica'] == 'Italia']
    if not italia_prod.empty:
        k1, k2, k3, k4 = st.columns(4)
        totale = italia_prod['totale_t'].iloc[0]
        k1.metric("Produzione Totale RS", f"{totale/1e6:.1f} M t")
        k2.metric("RS Non Pericolose", f"{italia_prod['rs_np_t'].iloc[0]/1e6:.1f} M t")
        k3.metric("RS Pericolose", f"{italia_prod['rs_p_t'].iloc[0]/1e6:.1f} M t")

        if df_imp is not None and not df_imp.empty:
            italia_imp = df_imp[df_imp['area_geografica'] == 'Italia']
            if not italia_imp.empty:
                imp_val = italia_imp['numero_impianti'].iloc[0]
                k4.metric("Impianti", fmt_num(int(imp_val)) if pd.notna(imp_val) else "N/A")
else:
    st.warning("Dati RS non disponibili.")
    st.stop()

st.divider()

# ── Produzione per area geografica ─────────────────────────────────────────
st.subheader("📊 Produzione RS per Area Geografica")

if df_prod is not None and not df_prod.empty:
    df_area = df_prod[df_prod['area_geografica'] != 'Italia'].copy()

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(df_area, x='area_geografica', y='totale_t',
                     color='area_geografica',
                     title="Produzione Totale RS",
                     labels={'totale_t': 'Tonnnellate', 'area_geografica': 'Area'})
        fig.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig, width="stretch")

    with col2:
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name='Non Pericolose', x=df_area['area_geografica'],
                              y=df_area['rs_np_t'], marker_color='#3b82f6'))
        fig2.add_trace(go.Bar(name='Pericolose', x=df_area['area_geografica'],
                              y=df_area['rs_p_t'], marker_color='#ef4444'))
        fig2.update_layout(title="Composizione RS per Area", barmode='group', height=350)
        st.plotly_chart(fig2, width="stretch")

st.divider()

# ── Trend produzione RS ────────────────────────────────────────────────────
st.subheader("📈 Trend Produzione RS (2018-2024)")

df_trend_all = load_mart_all("produzione_rs", "mart_produzione", tuple(YEARS))
if df_trend_all is not None and not df_trend_all.empty:
    df_italia = df_trend_all[df_trend_all['area_geografica'] == 'Italia']
    if not df_italia.empty:
        fig_trend = px.line(df_italia, x='anno', y='totale_t', markers=True,
                            title="Produzione RS Nazionale",
                            labels={'totale_t': 'Tonnnellate', 'anno': 'Anno'})
        fig_trend.update_layout(height=350)
        st.plotly_chart(fig_trend, width="stretch")

# ── Gestione RS ────────────────────────────────────────────────────────────
st.subheader("🔄 Gestione RS per Area")

if df_gest is not None and not df_gest.empty:
    df_gest_area = df_gest[df_gest['area_geografica'] != 'Italia'].copy()

    fig_gest = px.bar(df_gest_area, x='area_geografica', y=['rs_np_t', 'rs_p_t'],
                      title="Gestione RS per Area",
                      labels={'value': 'Tonnnellate', 'area_geografica': 'Area', 'variable': 'Tipo'},
                      barmode='group')
    fig_gest.update_layout(height=400)
    st.plotly_chart(fig_gest, width="stretch")

# ── Impianti ───────────────────────────────────────────────────────────────
st.subheader("🏗️ Impianti di Gestione RS")

if df_imp is not None and not df_imp.empty:
    df_imp_area = df_imp[df_imp['area_geografica'] != 'Italia'].copy()

    col1, col2 = st.columns(2)

    with col1:
        fig_imp = px.bar(df_imp_area, x='area_geografica', y='numero_impianti',
                         color='area_geografica',
                         title="Numero Impianti per Area",
                         labels={'numero_impianti': 'Impianti', 'area_geografica': 'Area'})
        fig_imp.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig_imp, width="stretch")

    with col2:
        fig_cap = px.bar(df_imp_area, x='area_geografica', y='totale_rs_t',
                         color='area_geografica',
                         title="Capacità Impianti (t)",
                         labels={'totale_rs_t': 'Tonnnellate', 'area_geografica': 'Area'})
        fig_cap.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig_cap, width="stretch")

st.caption(f"Dati: ISPRA Catasto Rifiuti Speciali · Anno {year} · CC BY 4.0")
