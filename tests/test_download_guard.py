"""Contract test della guardia sui download ISPRA.

Regressione reale: `curl -s` senza `-f` salvava le pagine 404 come CSV. Per
undici anni `ru_gestione_comunale.csv` è stato una pagina HTML, contata come
"file scaricato" perché il conteggio guardava solo la dimensione.
"""

from __future__ import annotations

import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "rifiuti-ispra-raw" / "download_multiyear.sh"


@pytest.mark.contract
class TestDownloadGuard:
    def test_script_esiste(self):
        assert SCRIPT.exists()

    def test_curl_fallisce_su_http_error(self):
        assert "curl -sf" in SCRIPT.read_text(), (
            "senza -f una 404 viene salvata come se fosse un CSV"
        )

    def test_rifiuta_risposte_html(self):
        testo = SCRIPT.read_text()
        assert "404 not found" in testo.lower()
        assert "DOCTYPE" in testo or "doctype" in testo.lower(), (
            "il contenuto va validato: ISPRA restituisce HTML anche con status 200"
        )

    def test_il_conteggio_non_basta_la_dimensione(self):
        testo = SCRIPT.read_text()
        assert "count_valid" in testo, (
            "il conteggio dei file deve escludere le pagine di errore: "
            "`-size +100c` accettava una pagina 404 da 500 byte"
        )
