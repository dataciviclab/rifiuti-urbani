"""Panoramica — KPI nazionali, trend e insight strategici."""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sources import (
    YEARS_BASE,
    YEARS_COSTI,
    YEARS_UNIFIED,
    calc_kg_procapite,
    fmt_eur,
    fmt_num,
    fmt_pct,
    load_mart,
    load_mart_all,
)

st.title("📊 Panoramica Nazionale")

year = st.selectbox("Anno", YEARS_BASE, index=len(YEARS_BASE) - 1, key="panoramica_year")

# ── KPI principali ────────────────────────────────────────────────────────
df = load_mart("ispra_ru_base", "mart_comuni", year)

if df is None or df.empty:
    st.warning("Nessun dato disponibile.")
    st.stop()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Popolazione", fmt_num(df['popolazione'].sum()))
k2.metric("Produzione RU", f"{fmt_num(int(df['totale_ru_tonnellate'].sum()))} t")
k3.metric("Raccolta Differenziata", f"{fmt_num(int(df['totale_rd_tonnellate'].sum()))} t")
rd_pct_naz = (
    df['totale_rd_tonnellate'].sum() / df['totale_ru_tonnellate'].sum() * 100
    if df['totale_ru_tonnellate'].sum() else float('nan')
)
k4.metric("RD% (pesata)", fmt_pct(rd_pct_naz, signed=False))

k5, k6, k7, k8 = st.columns(4)
kg_procapite = calc_kg_procapite(df)
k5.metric("Procapite", f"{kg_procapite:.1f} kg/ab")
k6.metric("Comuni", fmt_num(len(df)))

costi = None
try:
    costi = load_mart("ispra_ru_costi_procapite", "mart_comuni", year)
    if costi is not None and not costi.empty:
        costo_pesato = (
            (costi['ctot_euro_ab'] * costi['popolazione']).sum()
            / costi['popolazione'].sum()
        )
        k7.metric("Costo Medio", fmt_eur(costo_pesato))
    else:
        k7.metric("Costo Medio", "N/A")
except Exception:
    k7.metric("Costo Medio", "N/A")

k8.metric("Indifferenziato", f"{fmt_num(int(df['indifferenziato_t'].sum()))} t")
st.caption(
    "Il target UE del 65% al 2035 è sul **riciclo effettivo**, non sulla RD%: "
    "ISPRA riporta 52,3% di riciclo nel 2024. La RD% qui è pesata sulla produzione."
)
if costi is not None and not costi.empty:
    base_pop = df['popolazione'].sum()
    pop_costi = costi['popolazione'].sum()
    copertura = pop_costi / base_pop * 100 if base_pop else float('nan')
    st.caption(
        f"Copertura costi: {copertura:.1f}% della popolazione "
        f"({fmt_num(int(pop_costi))} abitanti su {fmt_num(int(base_pop))}). "
        "La media è calcolata solo sui comuni che dichiarano il costo."
    )

st.divider()

# ── Insight Strategy ───────────────────────────────────────────────────────
st.subheader("💡 Insight Strategici")

# Calcola insight
df_trend_all = load_mart_all("ispra_ru_base", "mart_comuni", tuple(YEARS_BASE))
df_costi_all = load_mart_all("ispra_ru_costi_procapite", "mart_comuni", tuple(YEARS_COSTI))
df_compose = load_mart("rifiuti_urbani_unified", "mart_comuni", year) if year in YEARS_UNIFIED else None

insights = []

if df_trend_all is not None and not df_trend_all.empty:
    # Trend RD% (pesata sulla produzione)
    trend = df_trend_all.groupby('anno').agg(
        ru=('totale_ru_tonnellate', 'sum'),
        rd=('totale_rd_tonnellate', 'sum'),
    ).reset_index()
    trend['rd_pct'] = trend['rd'] / trend['ru'] * 100
    rd_first = trend['rd_pct'].iloc[0]
    rd_last = trend['rd_pct'].iloc[-1]
    rd_delta = rd_last - rd_first

    # Trend costi (pesato sulla popolazione)
    if df_costi_all is not None and not df_costi_all.empty:
        trend_costi = df_costi_all.assign(
            costo_w=df_costi_all['ctot_euro_ab'] * df_costi_all['popolazione']
        ).groupby('anno').agg(
            costo_w=('costo_w', 'sum'),
            popolazione=('popolazione', 'sum'),
        ).reset_index()
        trend_costi['costo'] = trend_costi['costo_w'] / trend_costi['popolazione']
        cost_first = trend_costi['costo'].iloc[0]
        cost_last = trend_costi['costo'].iloc[-1]
        efficiency_first = cost_first / rd_first
        efficiency_last = cost_last / rd_last

        if efficiency_last > efficiency_first:
            insights.append({
                "icon": "📈",
                "title": "Crescita a costi crescenti",
                "text": f"RD% +{rd_delta:.1f}pp in 6 anni, ma costo/punto RD% +{((efficiency_last/efficiency_first)-1)*100:.0f}% ({efficiency_first:.2f} → {efficiency_last:.2f} EUR/punto)",
                "color": "orange",
            })
        else:
            insights.append({
                "icon": "✅",
                "title": "Efficienza in miglioramento",
                "text": f"RD% +{rd_delta:.1f}pp e costo/punto RD% in diminuzione",
                "color": "green",
            })

    # Gap Nord-Sud
    gap_data = df_trend_all.copy()
    gap_data['macroarea'] = gap_data['regione'].apply(
        lambda x: 'NORD' if x in ['Piemonte', "Valle d'Aosta", 'Lombardia', 'Trentino-Alto Adige', 'Veneto', 'Friuli-Venezia Giulia', 'Liguria', 'Emilia-Romagna']
        else ('SUD' if x in ['Calabria', 'Basilicata', 'Sicilia', 'Sardegna', 'Campania', 'Puglia', 'Molise'] else 'CENTRO')
    )
    gap_trend = gap_data.groupby(['anno', 'macroarea']).agg(
        ru=('totale_ru_tonnellate', 'sum'),
        rd=('totale_rd_tonnellate', 'sum'),
    ).reset_index()
    gap_trend['rd_pct'] = gap_trend['rd'] / gap_trend['ru'] * 100
    gap_nord = gap_trend[gap_trend['macroarea'] == 'NORD'].set_index('anno')['rd_pct']
    gap_sud = gap_trend[gap_trend['macroarea'] == 'SUD'].set_index('anno')['rd_pct']

    if not gap_nord.empty and not gap_sud.empty:
        gap_2018 = gap_nord.get(2018, 0) - gap_sud.get(2018, 0)
        gap_2024 = gap_nord.get(2024, 0) - gap_sud.get(2024, 0)
        if gap_2024 < gap_2018:
            insights.append({
                "icon": "🗺️",
                "title": "Gap territoriale in riduzione",
                "text": f"Gap Nord-Sud: {gap_2018:.1f}pp → {gap_2024:.1f}pp (-{gap_2018-gap_2024:.1f}pp)",
                "color": "green",
            })
        else:
            insights.append({
                "icon": "⚠️",
                "title": "Gap territoriale persistente",
                "text": f"Gap Nord-Sud resta a {gap_2024:.1f}pp",
                "color": "orange",
            })

    # Classi demografiche
    if df_compose is not None and not df_compose.empty:
        classi = df_compose.groupby('classe_demografica').agg(
            rd=('percentuale_rd', 'mean'),
            costo=('ctot_euro_ab', 'mean'),
        ).reset_index()
        if not classi.empty:
            best = classi.loc[classi['rd'].idxmax()]
            worst = classi.loc[classi['rd'].idxmin()]
            insights.append({
                "icon": "🏘️",
                "title": "La dimensione conta",
                "text": f"Migliori: {best['classe_demografica']} (RD {best['rd']:.0f}%, {best['costo']:.0f} EUR). Peggiori: {worst['classe_demografica']} (RD {worst['rd']:.0f}%, {worst['costo']:.0f} EUR)",
                "color": "blue" if best['classe_demografica'] != worst['classe_demografica'] else "gray",
            })

# Render insights
if insights:
    for i in range(0, len(insights), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            if i + j < len(insights):
                ins = insights[i + j]
                with col:
                    st.info(f"**{ins['icon']} {ins['title']}**\n\n{ins['text']}")

st.divider()

# ── Trend ──────────────────────────────────────────────────────────────────
st.subheader("📈 Trend 2018-2024")

if df_trend_all is not None and not df_trend_all.empty:
    df_trend = df_trend_all.groupby('anno').agg(
        produzione=('totale_ru_tonnellate', 'sum'),
        rd=('totale_rd_tonnellate', 'sum'),
    ).reset_index()
    df_trend['rd_pct'] = df_trend['rd'] / df_trend['produzione'] * 100

    col1, col2 = st.columns(2)
    with col1:
        fig_rd = px.line(df_trend, x='anno', y='rd_pct', markers=True,
                         title="RD% Nazionale (pesata)", labels={'rd_pct': 'RD%', 'anno': 'Anno'})
        fig_rd.update_layout(height=350)
        st.plotly_chart(fig_rd, width="stretch")
    with col2:
        fig_prod = go.Figure()
        fig_prod.add_trace(go.Bar(x=df_trend['anno'], y=df_trend['produzione'], name='Produzione', marker_color='#3b82f6'))
        fig_prod.add_trace(go.Bar(x=df_trend['anno'], y=df_trend['rd'], name='Raccolta Differenziata', marker_color='#22c55e'))
        fig_prod.update_layout(title="Produzione vs Raccolta Differenziata", barmode='group', height=350)
        st.plotly_chart(fig_prod, width="stretch")

    st.subheader("💰 Trend Costi Gestione")
    if df_costi_all is not None and not df_costi_all.empty:
        df_costi_trend = df_costi_all.assign(
            costo_w=df_costi_all['ctot_euro_ab'] * df_costi_all['popolazione']
        ).groupby('anno').agg(
            costo_w=('costo_w', 'sum'),
            popolazione=('popolazione', 'sum'),
            mediana=('ctot_euro_ab', 'median'),
        ).reset_index()
        df_costi_trend['media'] = (
            df_costi_trend['costo_w'] / df_costi_trend['popolazione']
        )
        fig_costi = px.line(df_costi_trend, x='anno', y=['media', 'mediana'], markers=True,
                            title="Costo Gestione per Abitante",
                            labels={'value': 'EUR/ab', 'anno': 'Anno', 'variable': 'Metrica'})
        fig_costi.update_layout(height=350)
        st.plotly_chart(fig_costi, width="stretch")

        st.subheader("♻️ Costo: recupero vs smaltimento")
        quota = df_costi_all.assign(
            cts_w=df_costi_all['cts_euro_ab'] * df_costi_all['popolazione'],
            ctr_w=df_costi_all['ctr_euro_ab'] * df_costi_all['popolazione'],
            ctot_w=df_costi_all['ctot_euro_ab'] * df_costi_all['popolazione'],
        ).groupby('anno')[['cts_w', 'ctr_w', 'ctot_w']].sum().reset_index()
        quota['Quota CTS (smaltimento)'] = quota['cts_w'] / quota['ctot_w'] * 100
        quota['Quota CTR (recupero)'] = quota['ctr_w'] / quota['ctot_w'] * 100
        fig_quota = px.line(
            quota, x='anno', y=['Quota CTS (smaltimento)', 'Quota CTR (recupero)'],
            markers=True, title="Quota del costo: smaltimento vs recupero",
            labels={'value': '% del costo totale', 'anno': 'Anno'},
        )
        fig_quota.update_layout(height=350)
        st.plotly_chart(fig_quota, width="stretch")

st.caption(f"Dati: ISPRA Catasto Rifiuti Nazionale · Anno {year} · CC BY 4.0")
