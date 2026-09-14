"""Fonti dati per la dashboard ISPRA Rifiuti Urbani.

Wrappa lab_connectors.duckdb.queries con @st.cache_data.
"""

from __future__ import annotations

import streamlit as st

from lab_connectors.duckdb.queries import (
    load_mart_table as _load_mart_table,
    query_clean as _query_clean,
)

PREFIX = "rifiuti-urbani/"
YEARS = list(range(2018, 2025))

SLUGS = {
    "base": "ispra_ru_base",
    "costi_pc": "ispra_ru_costi_procapite",
    "costi_kg": "ispra_ru_costi_kg",
    "flussi": "ispra_ru_flussi",
    "import_ru": "ispra_ru_import",
    "export_ru": "ispra_ru_export",
    "gestione_ru": "ispra_ru_gestione",
    "import_rs": "ispra_rs_import",
    "export_rs": "ispra_rs_export",
    "produzione_rs": "ispra_rs_produzione",
    "gestione_rs": "ispra_rs_gestione",
    "impianti_rs": "ispra_rs_impianti",
    "unified": "rifiuti_urbani_unified",
}


@st.cache_data(ttl=3600, show_spinner=False)
def load_mart(slug: str, table: str, year: int = 2024):
    """Carica un singolo mart table da GCS (cached 1h)."""
    return _load_mart_table(SLUGS[slug], table, year, prefix=PREFIX)


@st.cache_data(ttl=3600, show_spinner=False)
def query(slug: str, sql: str, years: tuple[int, ...] = tuple(YEARS)):
    """Esegue SQL sul clean layer (cached 1h)."""
    return _query_clean(SLUGS[slug], sql, list(years), prefix=PREFIX)
