"""Comuni — Benchmark e analisi comunale."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sources import query, YEARS

st.title("🏘️ Benchmark Comunale")

col1, col2 = st.columns([1, 2])
with col1:
    year = st.selectbox("Anno", YEARS, index=len(YEARS) - 1, key="comuni_year")

df_all = query("base", """
    SELECT codice_comune_istat, comune, regione, provincia, popolazione
    FROM clean_input WHERE totale_ru_tonnellate > 0 ORDER BY comune
""", years=(year,))

if df_all.empty:
    st.warning("Nessun dato disponibile.")
    st.stop()

comuni_list = df_all['comune'].unique().tolist()
with col2:
    comune = st.selectbox("Cerca comune", comuni_list,
                          index=comuni_list.index("Roma") if "Roma" in comuni_list else 0)

df_comune = query("base", f"SELECT * FROM clean_input WHERE comune = '{comune}' LIMIT 1",
                  years=(year,))

if df_comune.empty:
    st.warning(f"Nessun dato per {comune}.")
    st.stop()

st.subheader(f"📊 {comune}")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Popolazione", f"{df_comune['popolazione'].iloc[0]:,.0f}")
k2.metric("Produzione RU", f"{df_comune['totale_ru_tonnellate'].iloc[0]:,.0f} t")
k3.metric("RD%", f"{df_comune['percentuale_rd'].iloc[0]:.1f}%")
k4.metric("Procapite", f"{df_comune['kg_ru_per_abitante'].iloc[0]:.1f} kg/ab")

try:
    df_costi = query("costi_pc", f"""
        SELECT * FROM clean_input WHERE comune_o_aggregazione = '{comune}' LIMIT 1
    """, years=(year,))
    if not df_costi.empty:
        k5, k6, k7 = st.columns(3)
        k5.metric("Costo Totale", f"{df_costi['ctot_euro_ab'].iloc[0]:.2f} EUR/ab")
        k6.metric("Raccolta", f"{df_costi['crt_euro_ab'].iloc[0]:.2f} EUR/ab")
        k7.metric("Smaltimento", f"{df_costi['crd_euro_ab'].iloc[0]:.2f} EUR/ab")
except Exception:
    pass

st.divider()

# ── Benchmark ──────────────────────────────────────────────────────────────
st.subheader("⚖️ Confronto con Benchmark")
provincia = df_comune['provincia'].iloc[0]
regione = df_comune['regione'].iloc[0]
rd_comune = df_comune['percentuale_rd'].iloc[0]

df_prov = query("base", f"""
    SELECT avg(percentuale_rd) as rd_medio FROM clean_input
    WHERE totale_ru_tonnellate > 0 AND provincia = '{provincia}'
""", years=(year,))

df_reg = query("base", f"""
    SELECT avg(percentuale_rd) as rd_medio FROM clean_input
    WHERE totale_ru_tonnellate > 0 AND regione = '{regione}'
""", years=(year,))

df_naz = query("base", """
    SELECT avg(percentuale_rd) as rd_medio FROM clean_input WHERE totale_ru_tonnellate > 0
""", years=(year,))

col1, col2, col3 = st.columns(3)
with col1:
    rd_prov = df_prov['rd_medio'].iloc[0] if not df_prov.empty else 0
    st.metric(f"vs Provincia ({provincia})", f"{rd_comune:.1f}%",
              delta=f"{rd_comune - rd_prov:+.1f}pp vs media prov.",
              delta_color="normal" if rd_comune >= rd_prov else "inverse")
with col2:
    rd_reg = df_reg['rd_medio'].iloc[0] if not df_reg.empty else 0
    st.metric(f"vs Regione ({regione})", f"{rd_comune:.1f}%",
              delta=f"{rd_comune - rd_reg:+.1f}pp vs media reg.",
              delta_color="normal" if rd_comune >= rd_reg else "inverse")
with col3:
    rd_naz = df_naz['rd_medio'].iloc[0] if not df_naz.empty else 0
    st.metric("vs Nazionale", f"{rd_comune:.1f}%",
              delta=f"{rd_comune - rd_naz:+.1f}pp vs media naz.",
              delta_color="normal" if rd_comune >= rd_naz else "inverse")

# ── Distribuzione provincia ────────────────────────────────────────────────
st.subheader("📊 Distribuzione RD% nella Provincia")
df_dist = query("base", f"""
    SELECT comune, percentuale_rd FROM clean_input
    WHERE totale_ru_tonnellate > 0 AND provincia = '{provincia}'
    ORDER BY percentuale_rd
""", years=(year,))

if not df_dist.empty:
    fig = px.histogram(df_dist, x='percentuale_rd', nbins=20,
                       title=f"Distribuzione RD% - Provincia di {provincia}",
                       labels={'percentuale_rd': 'RD%', 'count': 'Comuni'})
    fig.add_vline(x=rd_comune, line_dash="dash", line_color="red",
                  annotation_text=f"{comune}: {rd_comune:.1f}%")
    fig.update_layout(height=350)
    st.plotly_chart(fig, width="stretch")

st.caption(f"Dati: ISPRA Catasto Rifiuti Nazionale · Anno {year} · CC BY 4.0")
