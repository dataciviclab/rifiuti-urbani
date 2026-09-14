"""Flussi — Analisi import/export e movimenti rifiuti."""

import streamlit as st
import plotly.express as px
import pandas as pd
from sources import load_mart, load_mart_all, fmt_num, YEARS

st.title("🚛 Flussi Rifiuti")

year = st.selectbox("Anno", YEARS, index=len(YEARS) - 1, key="flussi_year")

# ── Flussi extraregionali ────────────────────────────────────────────────
st.subheader("📊 Flussi Extraregionali RU")
try:
    df_flussi = load_mart("flussi", "mart_flussi", year)
    if df_flussi is not None and not df_flussi.empty:
        df_flussi = df_flussi[df_flussi['regione'] != 'Italia'].sort_values('quantita_t', ascending=False)
        fig = px.bar(df_flussi, x='regione', y='quantita_t', color='quantita_t',
                     color_continuous_scale='Blues',
                     title="Flussi Extraregionali per Regione",
                     labels={'quantita_t': 'Tonnnellate', 'regione': 'Regione'})
        fig.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig, width="stretch")
except Exception as e:
    st.info(f"Flussi non disponibili: {e}")

st.divider()

# ── Import/Export ──────────────────────────────────────────────────────────
st.subheader("🔄 Import/Export Rifiuti Urbani")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Import RU**")
    try:
        df_imp = load_mart("import_ru", "mart_import", year)
        if df_imp is not None and not df_imp.empty:
            df_imp = df_imp[df_imp['regione'] != 'Italia']
            fig_imp = px.pie(df_imp, values='totale_t', names='regione',
                             title="Import RU per Regione")
            fig_imp.update_layout(height=350)
            st.plotly_chart(fig_imp, width="stretch")
    except Exception:
        st.info("Import non disponibili")

with col2:
    st.markdown("**Export RU**")
    try:
        df_exp = load_mart("export_ru", "mart_import", year)
        if df_exp is not None and not df_exp.empty:
            df_exp = df_exp[df_exp['regione'] != 'Italia']
            fig_exp = px.pie(df_exp, values='totale_t', names='regione',
                             title="Export RU per Regione")
            fig_exp.update_layout(height=350)
            st.plotly_chart(fig_exp, width="stretch")
    except Exception:
        st.info("Export non disponibili")

# ── Bilancio ───────────────────────────────────────────────────────────────
st.subheader("⚖️ Bilancio Import/Export per Regione")
try:
    imp = load_mart("import_ru", "mart_import", year)
    exp = load_mart("export_ru", "mart_import", year)
    if imp is not None and exp is not None and not imp.empty and not exp.empty:
        imp = imp[imp['regione'] != 'Italia'][['regione', 'totale_t']].rename(columns={'totale_t': 'import_val'})
        exp = exp[exp['regione'] != 'Italia'][['regione', 'totale_t']].rename(columns={'totale_t': 'export_val'})
        bil = pd.merge(imp, exp, on='regione')
        bil['bilancio'] = bil['import_val'] - bil['export_val']
        bil = bil.sort_values('bilancio', ascending=False)
        fig_bil = px.bar(bil, x='regione', y='bilancio', color='bilancio',
                         color_continuous_scale=['#ef4444', '#22c55e'],
                         title="Bilancio (negativo = esportatore netto)",
                         labels={'bilancio': 'Tonnnellate', 'regione': 'Regione'})
        fig_bil.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig_bil, width="stretch")
except Exception:
    st.info("Bilancio non disponibile.")

# ── Trend ──────────────────────────────────────────────────────────────────
st.subheader("📈 Trend Flussi Extraregionali (2018-2024)")
try:
    df_trend_all = load_mart_all("flussi", "mart_flussi", tuple(YEARS))
    if df_trend_all is not None and not df_trend_all.empty:
        df_italia = df_trend_all[df_trend_all['regione'] == 'Italia']
        if not df_italia.empty:
            df_trend = df_italia.groupby('anno').agg(totale=('quantita_t', 'sum')).reset_index()
            fig_trend = px.line(df_trend, x='anno', y='totale', markers=True,
                                title="Totale Flussi Extraregionali",
                                labels={'totale': 'Tonnnellate', 'anno': 'Anno'})
            fig_trend.update_layout(height=350)
            st.plotly_chart(fig_trend, width="stretch")
except Exception:
    st.info("Trend non disponibile.")

st.caption(f"Dati: ISPRA Catasto Rifiuti Nazionale · Anno {year} · CC BY 4.0")
