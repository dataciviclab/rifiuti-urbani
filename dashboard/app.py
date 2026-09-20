"""
ISPRA Rifiuti Urbani · Dashboard Streamlit
Monitoraggio, esplorazione e benchmark dei rifiuti urbani e speciali in Italia.
"""

import streamlit as st

st.set_page_config(
    page_title="ISPRA Rifiuti Urbani · Dashboard",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded",
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

pg = st.navigation(pages, position="sidebar")

st.sidebar.markdown("---")
st.sidebar.caption("Dati: ISPRA Catasto Rifiuti Nazionale")
st.sidebar.caption(
    "Codice: [dataciviclab/rifiuti-urbani](https://github.com/dataciviclab/rifiuti-urbani)"
)
st.sidebar.caption("[DataCivicLab](https://dataciviclab.org/) · CC BY 4.0")

pg.run()
