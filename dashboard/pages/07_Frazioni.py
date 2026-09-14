"""Frazioni Merceologiche — Analisi composizione rifiuti."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from sources import load_mart, load_mart_all, fmt_num, fmt_pct, YEARS

st.title("🗑️ Frazioni Merceologiche")

year = st.selectbox("Anno", YEARS, index=len(YEARS) - 1, key="frazioni_year")

# ── Carica dati ────────────────────────────────────────────────────────────
df = load_mart("base", "mart_comuni", year)

if df is None or df.empty:
    st.warning("Nessun dato disponibile.")
    st.stop()

# ── KPI nazionale ──────────────────────────────────────────────────────────
st.subheader("📊 Composizione Nazionale RU")

frazioni_cols = {
    'frazione_umida_t': 'Umida',
    'verde_t': 'Verde',
    'carta_t': 'Carta',
    'vetro_t': 'Vetro',
    'legno_t': 'Legno',
    'metallo_t': 'Metallo',
    'plastica_t': 'Plastica',
    'raee_t': 'RAEE',
    'tessili_t': 'Tessili',
    'selettiva_t': 'Selettiva',
    'cd_t': 'C&D',
    'pulizia_stradale_t': 'Pulizia Stradale',
    'ingombranti_t': 'Ingombranti',
    'altro_t': 'Altro',
}

# Calcola totali nazionali
totale_ru = df['totale_ru_tonnellate'].sum()
totale_rd = df['totale_rd_tonnellate'].sum()
indiff = df['indifferenziato_t'].sum()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Totale RU", f"{totale_ru/1e6:.1f} M t")
k2.metric("Totale RD", f"{totale_rd/1e6:.1f} M t")
k3.metric("Indifferenziato", f"{indiff/1e6:.1f} M t")
k4.metric("RD%", fmt_pct(totale_rd / totale_ru * 100 if totale_ru > 0 else 0))

st.divider()

# ── Composizione RD ────────────────────────────────────────────────────────
st.subheader("📈 Composizione Raccolta Differenziata")

# Calcola totali per frazione
frazioni_data = []
for col, name in frazioni_cols.items():
    total = df[col].sum()
    if total > 0:
        frazioni_data.append({'Frazione': name, 'Tonnnellate': total, 'Perc': total / totale_rd * 100})

df_frazioni = pd.DataFrame(frazioni_data).sort_values('Tonnnellate', ascending=False)

col1, col2 = st.columns(2)

with col1:
    fig = px.pie(df_frazioni, values='Tonnnellate', names='Frazione',
                 title="Composizione RD (%)",
                 hole=0.3)
    fig.update_layout(height=400)
    st.plotly_chart(fig, width="stretch")

with col2:
    fig2 = px.bar(df_frazioni, x='Frazione', y='Tonnnellate',
                  color='Frazione',
                  title="RD per Frazione (t)",
                  labels={'Tonnnellate': 'Tonnnellate', 'Frazione': 'Frazione'})
    fig2.update_layout(height=400, xaxis_tickangle=-45, showlegend=False)
    st.plotly_chart(fig2, width="stretch")

# ── Trend frazioni ─────────────────────────────────────────────────────────
st.subheader("📈 Trend Frazioni Principali (2018-2024)")

df_all = load_mart_all("base", "mart_comuni", tuple(YEARS))
if df_all is not None and not df_all.empty:
    top_frazioni = ['frazione_umida_t', 'carta_t', 'plastica_t', 'vetro_t', 'metallo_t']
    trend_data = []
    for y in YEARS:
        df_y = df_all[df_all['anno'] == y]
        if not df_y.empty:
            row = {'anno': y}
            for col in top_frazioni:
                row[col] = df_y[col].sum() / 1e6
            trend_data.append(row)

    if trend_data:
        df_trend = pd.DataFrame(trend_data)
        fig_trend = px.line(df_trend, x='anno', y=top_frazioni,
                            title="Trend Frazioni Principali (Milioni t)",
                            labels={'value': 'Milioni t', 'anno': 'Anno', 'variable': 'Frazione'},
                            markers=True)
        fig_trend.update_layout(height=400)
        st.plotly_chart(fig_trend, width="stretch")

# ── Composizione per regione ───────────────────────────────────────────────
st.subheader("🗺️ Composizione RD per Regione")

df_reg = df.groupby('regione').agg(
    umida=('frazione_umida_t', 'sum'),
    carta=('carta_t', 'sum'),
    plastica=('plastica_t', 'sum'),
    vetro=('vetro_t', 'sum'),
    metallo=('metallo_t', 'sum'),
    totale=('totale_rd_tonnellate', 'sum'),
).reset_index()

df_reg['pct_umida'] = df_reg['umida'] / df_reg['totale'] * 100
df_reg['pct_carta'] = df_reg['carta'] / df_reg['totale'] * 100
df_reg['pct_plastica'] = df_reg['plastica'] / df_reg['totale'] * 100

fig_reg = px.bar(df_reg, x='regione', y=['pct_umida', 'pct_carta', 'pct_plastica'],
                 title="Composizione RD per Regione (%)",
                 labels={'value': '%', 'regione': 'Regione', 'variable': 'Frazione'},
                 barmode='group')
fig_reg.update_layout(height=400, xaxis_tickangle=-45)
st.plotly_chart(fig_reg, width="stretch")

# ── Tabella dettaglio ──────────────────────────────────────────────────────
st.subheader("📋 Dettaglio Frazioni Nazionali")

df_display = df_frazioni.copy()
df_display['Tonnnellate'] = df_display['Tonnnellate'].apply(lambda x: f"{fmt_num(int(x))} t")
df_display['Perc'] = df_display['Perc'].apply(lambda x: f"{x:.1f}%")
st.dataframe(df_display, use_container_width=True, hide_index=True)

st.caption(f"Dati: ISPRA Catasto Rifiuti Nazionale · Anno {year} · CC BY 4.0")
