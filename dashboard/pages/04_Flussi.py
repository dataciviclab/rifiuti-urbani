"""Flussi — Movimenti fuori regione, commercio estero e destinazioni."""

import pandas as pd
import plotly.express as px
import streamlit as st
from sources import YEARS, YEARS_REGIONI, load_mart, load_mart_all

st.title("🚛 Flussi Rifiuti")

year = st.selectbox("Anno", YEARS, index=len(YEARS) - 1, key="flussi_year")

TIPI_FLUSSO = {
    "Frazione organica": "organico",
    "Incenerimento": "incenerimento",
    "Discarica": "discarica",
}

# ── Movimenti fuori regione ────────────────────────────────────────────────
# Tre flussi distinti: non si sommano, la fonte non pubblica il totale.
st.subheader("📊 Uscite fuori regione")
tipo_label = st.radio(
    "Tipo di flusso",
    list(TIPI_FLUSSO),
    horizontal=True,
    key="flussi_tipo",
)
try:
    df_flussi = load_mart("ispra_ru_flussi", "mart_flussi", year)
    if df_flussi is not None and not df_flussi.empty:
        df_tipo = df_flussi[
            (df_flussi["regione"] != "Italia")
            & (df_flussi["tipo_flusso"] == TIPI_FLUSSO[tipo_label])
        ].sort_values("quantita_t", ascending=False)
        fig = px.bar(
            df_tipo,
            x="regione",
            y="quantita_t",
            color="quantita_t",
            color_continuous_scale="Blues",
            title=f"{tipo_label} avviata fuori regione",
            labels={"quantita_t": "Tonnellate", "regione": "Regione"},
        )
        fig.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig, width="stretch")
        st.caption(
            "Rifiuti urbani (e rifiuti dal loro trattamento) avviati a impianti "
            "in un'altra regione. Il blocco incenerimento è pubblicato da ISPRA "
            "solo dal 2020."
        )
except Exception as e:
    st.info(f"Flussi non disponibili: {e}")

st.divider()

# ── Commercio estero ───────────────────────────────────────────────────────
st.subheader("🔄 Commercio estero RU")
st.caption(
    "Import ed export verso l'estero. I movimenti tra regioni italiane sono "
    "nella sezione precedente: sono due grandezze diverse."
)
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Import per regione**")
    try:
        df_imp = load_mart("ispra_ru_import", "mart_import", year)
        if df_imp is not None and not df_imp.empty:
            df_imp = df_imp[df_imp["dimensione"] == "regione"]
            fig_imp = px.pie(
                df_imp, values="totale_t", names="territorio",
                title="Import RU per regione di destinazione",
            )
            fig_imp.update_layout(height=350)
            st.plotly_chart(fig_imp, width="stretch")
    except Exception:
        st.info("Import non disponibili")

with col2:
    st.markdown("**Export per regione**")
    try:
        df_exp = load_mart("ispra_ru_export", "mart_import", year)
        if df_exp is not None and not df_exp.empty:
            df_exp = df_exp[df_exp["dimensione"] == "regione"]
            fig_exp = px.pie(
                df_exp, values="totale_t", names="territorio",
                title="Export RU per regione di origine",
            )
            fig_exp.update_layout(height=350)
            st.plotly_chart(fig_exp, width="stretch")
    except Exception:
        st.info("Export non disponibili")

# ── Destinazioni estere ────────────────────────────────────────────────────
st.subheader("🌍 Paesi di destinazione e provenienza")
col3, col4 = st.columns(2)

with col3:
    try:
        df_exp = load_mart("ispra_ru_export", "mart_import", year)
        if df_exp is not None and not df_exp.empty:
            df_paesi = (
                df_exp[df_exp["dimensione"] == "paese"]
                .nlargest(12, "totale_t")
                .sort_values("totale_t")
            )
            fig_paesi = px.bar(
                df_paesi, x="totale_t", y="territorio", orientation="h",
                title="Export RU: primi 12 Paesi di destinazione",
                labels={"totale_t": "Tonnellate", "territorio": ""},
            )
            fig_paesi.update_layout(height=400)
            st.plotly_chart(fig_paesi, width="stretch")
    except Exception:
        st.info("Destinazioni non disponibili")

with col4:
    try:
        df_imp = load_mart("ispra_ru_import", "mart_import", year)
        if df_imp is not None and not df_imp.empty:
            df_paesi = (
                df_imp[df_imp["dimensione"] == "paese"]
                .nlargest(12, "totale_t")
                .sort_values("totale_t")
            )
            fig_paesi = px.bar(
                df_paesi, x="totale_t", y="territorio", orientation="h",
                title="Import RU: primi 12 Paesi di provenienza",
                labels={"totale_t": "Tonnellate", "territorio": ""},
            )
            fig_paesi.update_layout(height=400)
            st.plotly_chart(fig_paesi, width="stretch")
    except Exception:
        st.info("Provenienze non disponibili")

# ── Saldo estero ───────────────────────────────────────────────────────────
st.subheader("⚖️ Saldo del commercio estero per regione")
try:
    imp = load_mart("ispra_ru_import", "mart_import", year)
    exp = load_mart("ispra_ru_export", "mart_import", year)
    if imp is not None and exp is not None and not imp.empty and not exp.empty:
        imp = imp[imp["dimensione"] == "regione"][["territorio", "totale_t"]].rename(
            columns={"totale_t": "import_val"}
        )
        exp = exp[exp["dimensione"] == "regione"][["territorio", "totale_t"]].rename(
            columns={"totale_t": "export_val"}
        )
        bil = pd.merge(imp, exp, on="territorio", how="outer").fillna(0)
        bil["saldo"] = bil["import_val"] - bil["export_val"]
        bil = bil.sort_values("saldo", ascending=False)
        fig_bil = px.bar(
            bil, x="territorio", y="saldo", color="saldo",
            color_continuous_scale=["#ef4444", "#22c55e"],
            title="Saldo estero (negativo = esportatore netto)",
            labels={"saldo": "Tonnellate", "territorio": "Regione"},
        )
        fig_bil.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig_bil, width="stretch")
        st.caption(
            "Import meno export verso l'estero. Non misura la dipendenza "
            "impiantistica: un saldo estero nullo convive con forti flussi "
            "verso altre regioni."
        )
except Exception:
    st.info("Saldo non disponibile.")

# ── Trend ──────────────────────────────────────────────────────────────────
st.subheader("📈 Trend uscite fuori regione (2018-2024)")
try:
    df_trend_all = load_mart_all("ispra_ru_flussi", "mart_flussi", tuple(YEARS))
    if df_trend_all is not None and not df_trend_all.empty:
        df_trend = (
            df_trend_all[df_trend_all["regione"] == "Italia"]
            .groupby(["anno", "tipo_flusso"])
            .agg(tonnellate=("quantita_t", "sum"))
            .reset_index()
        )
        if not df_trend.empty:
            fig_trend = px.line(
                df_trend, x="anno", y="tonnellate", color="tipo_flusso",
                markers=True,
                title="Totale nazionale per tipo di flusso",
                labels={"tonnellate": "Tonnellate", "anno": "Anno", "tipo_flusso": ""},
            )
            fig_trend.update_layout(height=350)
            st.plotly_chart(fig_trend, width="stretch")
except Exception:
    st.info("Trend non disponibile.")

# ── Export sulla produzione ────────────────────────────────────────────────
st.subheader("📤 Export estero sulla produzione")

anno_reg = st.selectbox(
    "Anno (vista regionale)",
    YEARS_REGIONI,
    index=len(YEARS_REGIONI) - 1,
    key="flussi_reg_year",
)
df_reg = load_mart("regioni", "mart_regioni", anno_reg)

if df_reg is not None and not df_reg.empty:
    reg = df_reg[
        ["regione", "export_estero_t", "export_estero_su_prodotto_pct"]
    ].sort_values("export_estero_su_prodotto_pct", ascending=False)
    fig_share = px.bar(
        reg,
        x="regione",
        y="export_estero_su_prodotto_pct",
        color="export_estero_su_prodotto_pct",
        color_continuous_scale="Blues",
        title="Export RU verso l'estero sulla produzione (%)",
        labels={
            "export_estero_su_prodotto_pct": "% del prodotto",
            "regione": "Regione",
        },
    )
    fig_share.update_layout(height=400, xaxis_tickangle=-45)
    st.plotly_chart(fig_share, width="stretch")
    st.caption(
        "Quota dei RU prodotta esportata verso l'estero, non verso altre "
        "regioni. Fonte: compose regionale `rifiuti_regioni`."
    )
else:
    st.info("Vista regionale non disponibile.")

st.caption(f"Dati: ISPRA Catasto Rifiuti Nazionale · Anno {year} · CC BY 4.0")
