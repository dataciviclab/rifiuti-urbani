"""Regioni — Benchmark regionale RD% e costi."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from sources import query, YEARS

st.title("🗺️ Benchmark Regionale")

year = st.selectbox("Anno", YEARS, index=len(YEARS) - 1, key="regioni_year")

# ── RD% per regione ───────────────────────────────────────────────────────
st.subheader("📊 Classifica Regioni per RD%")

df = query(
    "base",
    """
    SELECT regione,
           avg(percentuale_rd) as rd_pct,
           sum(totale_ru_tonnellate) as produzione,
           sum(totale_rd_tonnellate) as rd,
           sum(popolazione) as popolazione,
           avg(kg_ru_per_abitante) as kg_procapite
    FROM clean_input
    WHERE totale_ru_tonnellate > 0 AND regione != 'Italia'
    GROUP BY regione
    ORDER BY rd_pct DESC
    """,
    years=(year,),
)

if df.empty:
    st.warning("Nessun dato disponibile.")
    st.stop()

rd_nazionale = df['rd_pct'].mean()

col1, col2 = st.columns(2)

with col1:
    fig = px.bar(
        df, x='regione', y='rd_pct', color='rd_pct',
        color_continuous_scale=['#ef4444', '#f59e0b', '#22c55e'],
        title="RD% per Regione",
        labels={'rd_pct': 'RD%', 'regione': 'Regione'},
    )
    fig.add_hline(y=rd_nazionale, line_dash="dash", line_color="white",
                  annotation_text=f"Media: {rd_nazionale:.1f}%")
    fig.update_layout(height=500, xaxis_tickangle=-45)
    st.plotly_chart(fig, width="stretch")

with col2:
    fig2 = px.scatter(
        df, x='kg_procapite', y='rd_pct', size='popolazione',
        color='regione', hover_data=['produzione'],
        title="Produzione vs RD% per Regione",
        labels={'kg_procapite': 'kg/abitante', 'rd_pct': 'RD%'},
    )
    fig2.update_layout(height=500, showlegend=False)
    st.plotly_chart(fig2, width="stretch")

# ── Tabella ────────────────────────────────────────────────────────────────
st.subheader("📋 Dettaglio Regioni")
df_display = df.copy()
df_display['produzione'] = df_display['produzione'].apply(lambda x: f"{x:,.0f} t")
df_display['rd'] = df_display['rd'].apply(lambda x: f"{x:,.0f} t")
df_display['popolazione'] = df_display['popolazione'].apply(lambda x: f"{x:,.0f}")
df_display['rd_pct'] = df_display['rd_pct'].apply(lambda x: f"{x:.1f}%")
df_display['kg_procapite'] = df_display['kg_procapite'].apply(lambda x: f"{x:.1f}")
st.dataframe(df_display, use_container_width=True, hide_index=True)

# ── Trend top 5 ───────────────────────────────────────────────────────────
st.subheader("📈 Trend RD% Top 5 Regioni (2018-2024)")
top_regions = df.nlargest(5, 'rd_pct')['regione'].tolist()

trend_data = []
for y in YEARS:
    try:
        row = query("base", f"""
            SELECT regione, avg(percentuale_rd) as rd_pct
            FROM clean_input
            WHERE totale_ru_tonnellate > 0
              AND regione IN ({','.join(repr(r) for r in top_regions)})
            GROUP BY regione
        """, years=(y,))
        if not row.empty:
            row['anno'] = y
            trend_data.append(row)
    except Exception:
        pass

if trend_data:
    df_trend = pd.concat(trend_data, ignore_index=True)
    fig_trend = px.line(df_trend, x='anno', y='rd_pct', color='regione', markers=True,
                        title="Top 5 Regioni - Trend RD%",
                        labels={'rd_pct': 'RD%', 'anno': 'Anno'})
    fig_trend.update_layout(height=400)
    st.plotly_chart(fig_trend, width="stretch")

st.caption(f"Dati: ISPRA Catasto Rifiuti Nazionale · Anno {year} · CC BY 4.0")
