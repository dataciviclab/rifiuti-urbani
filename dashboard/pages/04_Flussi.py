"""Flussi — Analisi import/export e movimenti rifiuti."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from sources import query, YEARS

st.title("🚛 Flussi Rifiuti")

year = st.selectbox("Anno", YEARS, index=len(YEARS) - 1, key="flussi_year")

# ── Flussi extraregionali ────────────────────────────────────────────────
st.subheader("📊 Flussi Extraregionali RU")
df_flussi = query("flussi", """
    SELECT regione, quantita_t FROM clean_input
    WHERE regione != 'Italia' ORDER BY quantita_t DESC
""", years=(year,))

if not df_flussi.empty:
    fig = px.bar(df_flussi, x='regione', y='quantita_t', color='quantita_t',
                 color_continuous_scale='Blues',
                 title="Flussi Extraregionali per Regione",
                 labels={'quantita_t': 'Tonnnellate', 'regione': 'Regione'})
    fig.update_layout(height=400, xaxis_tickangle=-45)
    st.plotly_chart(fig, width="stretch")

st.divider()

# ── Import/Export ──────────────────────────────────────────────────────────
st.subheader("🔄 Import/Export Rifiuti Urbani")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Import RU**")
    df_imp = query("import_ru", """
        SELECT regione, totale_t FROM clean_input
        WHERE regione != 'Italia' ORDER BY totale_t DESC
    """, years=(year,))
    if not df_imp.empty:
        fig_imp = px.pie(df_imp, values='totale_t', names='regione',
                         title="Import RU per Regione")
        fig_imp.update_layout(height=350)
        st.plotly_chart(fig_imp, width="stretch")

with col2:
    st.markdown("**Export RU**")
    df_exp = query("export_ru", """
        SELECT regione, totale_t FROM clean_input
        WHERE regione != 'Italia' ORDER BY totale_t DESC
    """, years=(year,))
    if not df_exp.empty:
        fig_exp = px.pie(df_exp, values='totale_t', names='regione',
                         title="Export RU per Regione")
        fig_exp.update_layout(height=350)
        st.plotly_chart(fig_exp, width="stretch")

# ── Bilancio ───────────────────────────────────────────────────────────────
st.subheader("⚖️ Bilancio Import/Export per Regione")
try:
    imp = query("import_ru", "SELECT regione, totale_t as import_val FROM clean_input WHERE regione != 'Italia'",
                years=(year,))
    exp = query("export_ru", "SELECT regione, totale_t as export_val FROM clean_input WHERE regione != 'Italia'",
                years=(year,))
    if not imp.empty and not exp.empty:
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
trend_data = []
for y in YEARS:
    try:
        row = query("flussi", """
            SELECT sum(quantita_t) as totale FROM clean_input WHERE regione = 'Italia'
        """, years=(y,))
        if not row.empty:
            row['anno'] = y
            trend_data.append(row)
    except Exception:
        pass

if trend_data:
    df_trend = pd.concat(trend_data, ignore_index=True)
    fig_trend = px.line(df_trend, x='anno', y='totale', markers=True,
                        title="Totale Flussi Extraregionali",
                        labels={'totale': 'Tonnnellate', 'anno': 'Anno'})
    fig_trend.update_layout(height=350)
    st.plotly_chart(fig_trend, width="stretch")

st.caption(f"Dati: ISPRA Catasto Rifiuti Nazionale · Anno {year} · CC BY 4.0")
