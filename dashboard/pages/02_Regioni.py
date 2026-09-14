"""Regioni — Benchmark regionale RD% e costi."""

import streamlit as st
import plotly.express as px
import pandas as pd
from sources import load_mart_all, fmt_num, fmt_pct, YEARS

st.title("🗺️ Benchmark Regionale")

year = st.selectbox("Anno", YEARS, index=len(YEARS) - 1, key="regioni_year")

# ── RD% per regione ───────────────────────────────────────────────────────
st.subheader("📊 Classifica Regioni per RD%")

df = load_mart_all("base", "mart_comuni", (year,))

if df is None or df.empty:
    st.warning("Nessun dato disponibile.")
    st.stop()

df_reg = df.groupby('regione').agg(
    rd_pct=('percentuale_rd', 'mean'),
    produzione=('totale_ru_tonnellate', 'sum'),
    rd=('totale_rd_tonnellate', 'sum'),
    popolazione=('popolazione', 'sum'),
).reset_index().sort_values('rd_pct', ascending=False)

df_reg['kg_procapite'] = df_reg['produzione'] * 1e6 / df_reg['popolazione']
rd_nazionale = df_reg['rd_pct'].mean()

col1, col2 = st.columns(2)

with col1:
    fig = px.bar(df_reg, x='regione', y='rd_pct', color='rd_pct',
                 color_continuous_scale=['#ef4444', '#f59e0b', '#22c55e'],
                 title="RD% per Regione",
                 labels={'rd_pct': 'RD%', 'regione': 'Regione'})
    fig.add_hline(y=rd_nazionale, line_dash="dash", line_color="white",
                  annotation_text=f"Media: {rd_nazionale:.1f}%")
    fig.update_layout(height=500, xaxis_tickangle=-45)
    st.plotly_chart(fig, width="stretch")

with col2:
    fig2 = px.scatter(df_reg, x='kg_procapite', y='rd_pct', size='popolazione',
                      color='regione', hover_data=['produzione'],
                      title="Produzione vs RD% per Regione",
                      labels={'kg_procapite': 'kg/abitante', 'rd_pct': 'RD%'})
    fig2.update_layout(height=500, showlegend=False)
    st.plotly_chart(fig2, width="stretch")

# ── Tabella ────────────────────────────────────────────────────────────────
st.subheader("📋 Dettaglio Regioni")
df_display = df_reg.copy()
df_display['produzione'] = df_display['produzione'].apply(lambda x: f"{fmt_num(int(x))} t")
df_display['rd'] = df_display['rd'].apply(lambda x: f"{fmt_num(int(x))} t")
df_display['popolazione'] = df_display['popolazione'].apply(lambda x: fmt_num(int(x)))
df_display['rd_pct'] = df_display['rd_pct'].apply(lambda x: fmt_pct(x))
df_display['kg_procapite'] = df_display['kg_procapite'].apply(lambda x: f"{x:.1f}")
st.dataframe(df_display, use_container_width=True, hide_index=True)

# ── Trend top 5 ───────────────────────────────────────────────────────────
st.subheader("📈 Trend RD% Top 5 Regioni (2018-2024)")
top_regions = df_reg.nlargest(5, 'rd_pct')['regione'].tolist()

df_all = load_mart_all("base", "mart_comuni", tuple(YEARS))
if df_all is not None and not df_all.empty:
    df_top = df_all[df_all['regione'].isin(top_regions)]
    df_trend = df_top.groupby(['anno', 'regione']).agg(rd_pct=('percentuale_rd', 'mean')).reset_index()

    if not df_trend.empty:
        fig_trend = px.line(df_trend, x='anno', y='rd_pct', color='regione', markers=True,
                            title="Top 5 Regioni - Trend RD%",
                            labels={'rd_pct': 'RD%', 'anno': 'Anno'})
        fig_trend.update_layout(height=400)
        st.plotly_chart(fig_trend, width="stretch")

st.caption(f"Dati: ISPRA Catasto Rifiuti Nazionale · Anno {year} · CC BY 4.0")
