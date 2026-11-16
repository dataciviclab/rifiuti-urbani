"""Contract test della guardia sui download ISPRA.

Regressione reale: `curl -s` senza `-f` salvava le pagine 404 come CSV. Il
file `ru_gestione_comunale.csv` era una pagina HTML in tutti gli anni presenti
in `raw/`, e il conteggio finale lo considerava scaricato (non è più nella
lista dei download, ma il meccanismo era armato per tutti gli altri).

I test eseguono la funzione `dl` dello script contro un `curl` finto: le
asserzioni sul testo dello script non bastano, perché un refactor può tenere
le stringhe e rompere la logica.
"""

from __future__ import annotations

import os
import pathlib
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "rifiuti-ispra-raw" / "download_multiyear.sh"

CURL_STUB = """#!/usr/bin/env bash
# curl finto: scrive nel file indicato da -o secondo FAKE_MODE
out=""
prev=""
for a in "$@"; do
  if [ "$prev" = "-o" ]; then out="$a"; fi
  prev="$a"
done
case "${FAKE_MODE}" in
  http404) exit 22 ;;
  html)    printf '<!DOCTYPE html><html><body>a;b</body></html>' > "$out" ;;
  csv)     printf 'Regione;Anno;Quantitativo (t)\\nLombardia;2024;10\\n' > "$out" ;;
  *)       exit 99 ;;
esac
"""


def _dl_function() -> str:
    """Estrae la sola definizione di `dl` dallo script, senza eseguirlo."""
    text = SCRIPT.read_text()
    start = text.index("dl() {")
    end = text.index("\n}\n", start) + 3
    return text[start:end]


def _run_dl(tmp_path: pathlib.Path, mode: str) -> tuple[int, int]:
    """Esegue `dl` con un curl finto. Ritorna (fallimenti, file prodotti)."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    stub = bindir / "curl"
    stub.write_text(CURL_STUB)
    stub.chmod(0o755)

    fn_file = tmp_path / "dl.sh"
    fn_file.write_text(_dl_function())

    outdir = tmp_path / "out"
    runner = tmp_path / "run.sh"
    runner.write_text(
        "set -uo pipefail\n"
        "FAILED=()\n"
        "COOKIE_JAR=/dev/null\n"
        f"source '{fn_file}'\n"
        f"dl 'http://finto/test.csv' '{outdir}' 'test.csv'\n"
        'echo "${#FAILED[@]}"\n'
        f"ls '{outdir}' 2>/dev/null | wc -l\n"
    )
    env = dict(os.environ)
    env["PATH"] = f"{bindir}:{env['PATH']}"
    env["FAKE_MODE"] = mode
    res = subprocess.run(
        ["bash", str(runner)], capture_output=True, text=True, env=env, timeout=30
    )
    assert res.returncode == 0, res.stderr
    # stdout contiene anche il WARN della guardia: gli ultimi due valori sono
    # il conteggio dei fallimenti e dei file prodotti.
    fails, files = res.stdout.strip().splitlines()[-2:]
    return int(fails), int(files)


@pytest.mark.contract
class TestDownloadGuard:
    def test_script_esiste(self):
        assert SCRIPT.exists()

    def test_http_error_non_produce_file(self, tmp_path):
        """Una 404 non deve lasciare un CSV: meglio assente che finto."""
        fails, files = _run_dl(tmp_path, "http404")
        assert (fails, files) == (1, 0)

    def test_html_con_puntoevirgola_viene_rifiutato(self, tmp_path):
        """Una pagina HTML può contenere ';': va riconosciuta come HTML."""
        fails, files = _run_dl(tmp_path, "html")
        assert (fails, files) == (1, 0)

    def test_csv_valido_viene_conservato(self, tmp_path):
        fails, files = _run_dl(tmp_path, "csv")
        assert (fails, files) == (0, 1)

    def test_curl_fallisce_su_http_error(self):
        # guardia ulteriore: senza -f curl non esce non-zero su 404
        assert "curl -sf" in SCRIPT.read_text()

    def test_il_conteggio_non_basta_la_dimensione(self):
        assert "count_valid" in SCRIPT.read_text(), (
            "il conteggio dei file deve escludere le pagine di errore: "
            "`-size +100c` accettava una pagina 404 da 500 byte"
        )
