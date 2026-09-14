"""Panoramica — KPI nazionali e trend 2018-2024."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from sources import query, YEARS

st.title("📊 Panoramica Nazionale")

year = st.selectbox("Anno", YEARS, index=len(YEARS) - 1, key="panoramica_year")

# ── KPI principali ────────────────────────────────────────────────────────
df = query("base", """
    SELECT
        sum(totale_ru_tonnellate) as produzione,
        sum(totale_rd_tonnellate) as rd,
        avg(percentuale_rd) as rd_pct,
        sum(kg_ru_per_abitante * popolazione) / sum(popolazione) as kg_procapite,
        count(*) as n_comuni,
        sum(popolazione) as popolazione
    FROM clean_input WHERE totale_ru_tonnellate > 0
""", years=(year,))

if df.empty:
    st.warning("Nessun dato disponibile.")
    st.stop()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Popolazione", f"{df['popolazione'].iloc[0]:,.0f}")
k2.metric("Produzione RU", f"{df['produzione'].iloc[0]:,.0f} t")
k3.metric("Raccolta Differenziata", f"{df['rd'].iloc[0]:,.0f} t")
k4.metric("RD%", f"{df['rd_pct'].iloc[0]:.1f}%")

k5, k6, k7, k8 = st.columns(4)
k5.metric("Procapite", f"{df['kg_procapite'].iloc[0]:.1f} kg/ab")
k6.metric("Comuni", f"{df['n_comuni'].iloc[0]:,}")

try:
    costi = query("costi_pc", "SELECT avg(ctot_euro_ab) as costo_medio FROM clean_input WHERE ctot_euro_ab > 0", years=(year,))
    k7.metric("Costo Medio", f"{costi['costo_medio'].iloc[0]:.2f} EUR/ab" if not costi.empty else "N/A")
except Exception:
    k7.metric("Costo Medio", "N/A")

rd_pct = df['rd_pct'].iloc[0]
k8.metric("Obiettivo UE 65%", f"{rd_pct:.1f}%", delta=f"{rd_pct - 65.0:+.1f}pp")

st.divider()

# ── Trend ──────────────────────────────────────────────────────────────────
st.subheader("📈 Trend 2018-2024")
trend_data = []
for y in YEARS:
    try:
        row = query("base", """
            SELECT sum(totale_ru_tonnellate) as produzione,
                   sum(totale_rd_tonnellate) as rd,
                   avg(percentuale_rd) as rd_pct
            FROM clean_input WHERE totale_ru_tonnellate > 0
        """, years=(y,))
        if not row.empty:
            row['anno'] = y
            trend_data.append(row)
    except Exception:
        pass

if trend_data:
    df_trend = pd.concat(trend_data, ignore_index=True)
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
            c = query("costi_pc", """
                SELECT avg(ctot_euro_ab) as media,
                       percentile_cont(0.5) within group (order by ctot_euro_ab) as mediana
                FROM clean_input WHERE ctot_euro_ab > 0
            """, years=(y,))
            if not c.empty:
                c['anno'] = y
                costi_trend.append(c)
        except Exception:
            pass
    if costi_trend:
        df_costi = pd.concat(costi_trend, ignore_index=True)
        fig_costi = px.line(df_costi, x='anno', y=['media', 'mediana'], markers=True,
                            title="Costo Gestione per Abitante", labels={'value': 'EUR/ab', 'anno': 'Anno'})
        fig_costi.update_layout(height=350)
        st.plotly_chart(fig_costi, width="stretch")

st.caption(f"Dati: ISPRA Catasto Rifiuti Nazionale · Anno {year} · CC BY 4.0")
