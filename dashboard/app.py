#!/usr/bin/env python3
"""
ISPRA Rifiuti Urbani · Dashboard Streamlit
Monitoraggio, esplorazione e benchmark dei rifiuti urbani e speciali in Italia.
"""

import streamlit as st
from lab_connectors.dashboard import DashboardConfig, run_dashboard

config = DashboardConfig(
    title="ISPRA Rifiuti Urbani · Dashboard",
    icon="♻️",
    repo_name="rifiuti-urbani",
    repo_url="https://github.com/dataciviclab/rifiuti-urbani",
    sources_text="Dati: ISPRA Catasto Rifiuti Nazionale",
)

pages = {
    "Monitoraggio": [
        st.Page("pages/01_Panoramica.py", title="Panoramica", icon="📊", default=True),
        st.Page("pages/07_Frazioni.py", title="Frazioni Merceologiche", icon="🗑️"),
        st.Page("pages/06_RSpeciale.py", title="Rifiuti Speciali", icon="🏭"),
    ],
    "Benchmark": [
        st.Page("pages/02_Regioni.py", title="Regioni", icon="🗺️"),
        st.Page("pages/03_Comuni.py", title="Comuni", icon="🏘️"),
    ],
    "Esplorazione": [
        st.Page("pages/04_Flussi.py", title="Flussi", icon="🚛"),
        st.Page("pages/05_SQL.py", title="Query SQL", icon="🧪"),
    ],
}

run_dashboard(config, pages)
