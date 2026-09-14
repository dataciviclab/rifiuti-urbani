"""Comuni — Benchmark e analisi comunale."""

import streamlit as st
import plotly.express as px
from sources import load_mart, fmt_eur, fmt_num, fmt_pct, safe_int, YEARS

st.title("🏘️ Benchmark Comunale")

col1, col2 = st.columns([1, 2])
with col1:
    year = st.selectbox("Anno", YEARS, index=len(YEARS) - 1, key="comuni_year")

df_all = load_mart("base", "mart_comuni", year)

if df_all is None or df_all.empty:
    st.warning("Nessun dato disponibile.")
    st.stop()

comuni_list = sorted(df_all['comune'].unique().tolist())
with col2:
    comune = st.selectbox("Cerca comune", comuni_list,
                          index=comuni_list.index("Roma") if "Roma" in comuni_list else 0)

df_comune = df_all[df_all['comune'] == comune]

if df_comune.empty:
    st.warning(f"Nessun dato per {comune}.")
    st.stop()

row = df_comune.iloc[0]

st.subheader(f"📊 {comune}")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Popolazione", fmt_num(safe_int(row["popolazione"])))
k2.metric("Produzione RU", f"{fmt_num(safe_int(row["totale_ru_tonnellate"]))} t")
k3.metric("RD%", fmt_pct(row['percentuale_rd']))
k4.metric("Procapite", f"{row['kg_ru_per_abitante']:.1f} kg/ab")

try:
    costi = load_mart("costi_pc", "mart_comuni", year)
    if costi is not None and not costi.empty:
        c = costi[costi['codice_comune_istat'] == row['codice_comune_istat']]
        if not c.empty:
            k5, k6, k7 = st.columns(3)
            k5.metric("Costo Totale", fmt_eur(c['ctot_euro_ab'].iloc[0]))
            k6.metric("Raccolta", fmt_eur(c['crt_euro_ab'].iloc[0]))
            k7.metric("Smaltimento", fmt_eur(c['crd_euro_ab'].iloc[0]))
except Exception:
    pass

st.divider()

# ── Benchmark ──────────────────────────────────────────────────────────────
st.subheader("⚖️ Confronto con Benchmark")
provincia = row['provincia']
regione = row['regione']
rd_comune = row['percentuale_rd']

rd_prov = df_all[df_all['provincia'] == provincia]['percentuale_rd'].mean()
rd_reg = df_all[df_all['regione'] == regione]['percentuale_rd'].mean()
rd_naz = df_all['percentuale_rd'].mean()

col1, col2, col3 = st.columns(3)
with col1:
    delta = rd_comune - rd_prov
    st.metric(
        f"Provincia ({provincia})",
        f"{fmt_pct(rd_prov)}",
        delta=f"{comune}: {delta:+.1f}pp",
        delta_color="normal" if delta >= 0 else "inverse",
    )
with col2:
    delta = rd_comune - rd_reg
    st.metric(
        f"Regione ({regione})",
        f"{fmt_pct(rd_reg)}",
        delta=f"{comune}: {delta:+.1f}pp",
        delta_color="normal" if delta >= 0 else "inverse",
    )
with col3:
    delta = rd_comune - rd_naz
    st.metric(
        "Nazionale",
        f"{fmt_pct(rd_naz)}",
        delta=f"{comune}: {delta:+.1f}pp",
        delta_color="normal" if delta >= 0 else "inverse",
    )

# ── Distribuzione provincia ────────────────────────────────────────────────
st.subheader("📊 Distribuzione RD% nella Provincia")
df_dist = df_all[df_all['provincia'] == provincia].sort_values('percentuale_rd')

if not df_dist.empty:
    fig = px.histogram(df_dist, x='percentuale_rd', nbins=20,
                       title=f"Distribuzione RD% - Provincia di {provincia}",
                       labels={'percentuale_rd': 'RD%', 'count': 'Comuni'})
    fig.add_vline(x=rd_comune, line_dash="dash", line_color="red",
                  annotation_text=f"{comune}: {rd_comune:.1f}%")
    fig.update_layout(height=350)
    st.plotly_chart(fig, width="stretch")

st.caption(f"Dati: ISPRA Catasto Rifiuti Nazionale · Anno {year} · CC BY 4.0")
