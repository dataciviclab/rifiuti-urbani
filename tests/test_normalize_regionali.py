"""Pure unit test per i normalizzatori dei dataset regionali ISPRA.

I file regionali hanno tre trappole già viste nei dataset nazionali:

1. un blocco "sintesi" (R1-R12 / D1-D14) che, se letto insieme ai blocchi di
   dettaglio, conta due volte le stesse tonnellate;
2. righe di totale ("TOTALE") dentro i blocchi, con le colonne spostate:
   se non scartate producono comune="250" e totali falsi;
3. nomi regione maiuscoli e senza trattino ("TRENTINO ALTO ADIGE"), che
   rompono i join con costi e ru_base.
"""

from __future__ import annotations

import csv
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from normalize_ispra_all import (  # noqa: E402
    canonical_region,
    normalize_csv,
    normalize_gestione_rs_regione,
    normalize_gestione_ru_impianto,
    normalize_gestione_ru_regione,
    normalize_impianti_regione,
    normalize_rs_produzione_regione,
)


@pytest.mark.pure_unit
def test_canonical_region_joins_names():
    assert canonical_region("TRENTINO ALTO ADIGE") == "Trentino-Alto Adige"
    assert canonical_region("Friuli Venezia Giulia") == "Friuli-Venezia Giulia"
    assert canonical_region("valle d'aosta") == "Valle d'Aosta"
    assert canonical_region("ITALIA") == "Italia"


@pytest.mark.pure_unit
def test_gestione_ru_regione_keeps_italy_and_canonicalizes():
    lines = [
        "Gestione dei rifiuti urbani per regione - Italia - 2024 (ISPRA);",
        "Compostaggio",
        "Regione;Numero impianti;Frazione umida (t);Verde (t);Tot. RU (t);Fanghi (t);Altro (t);Totale (t)",
        "TRENTINO ALTO ADIGE;11;1.000,0;2.000,0;3.000,0;0,0;0,0;3.000,0;",
        "ITALIA;250;1.000,0;2.000,0;3.000,0;0,0;0,0;3.000,0;",
        "Andamento del numero di impianti per tipologia",
        "Anno;Compostaggio (n.)",
        "2024;250",
    ]
    rows = normalize_gestione_ru_regione(lines)
    regs = {r["area_geografica"] for r in rows}
    assert regs == {"Trentino-Alto Adige", "Italia"}
    assert rows[0]["numero_impianti"] == "11"
    assert rows[0]["totale_t"] == "3.000,0"


@pytest.mark.pure_unit
def test_gestione_ru_impianto_drops_totale_rows():
    lines = [
        "Gestione dei rifiuti urbani, elenco completo impianti - anno 2024 (ISPRA);",
        "Compostaggio",
        "Regione;Provincia;Comune;Frazione umida (t);Verde (t);Tot. RU (t);Fanghi (t);Altro (t);Totale (t)",
        "PIEMONTE;TORINO;ALBIANO;0,0;8.224,0;8.224,0;0,0;599,0;8.823,0;",
        "TOTALE;;250;1.098.319,0;1.339.074,0;2.437.393,0;608.297,0;386.031,0;3.431.721,0;",
    ]
    rows = normalize_gestione_ru_impianto(lines)
    assert len(rows) == 1
    assert rows[0]["regione"] == "Piemonte"
    assert rows[0]["comune"] == "ALBIANO"
    assert rows[0]["totale_t"] == "8.823,0"


@pytest.mark.pure_unit
def test_gestione_rs_regione_skips_summary_block():
    lines = [
        "Gestione dei rifiuti speciali - 2024 (ISPRA);",
        "Regione;R1-R12 (t);R13 al 31/12 (t);Tot. R1-R13 (t);D1-D14 (t);D15 al 31/12 (t);Tot. D1-D15 (t);Totale (t)",
        "Lombardia;999;999;999;999;999;999;999;",
        "Operazioni di recupero dei rifiuti non pericolosi - 2024 (ISPRA);",
        "Regione;R1 (t);R2 (t);R13 al 31/12 (t);Totale (t)",
        "Lombardia;100;200;300;600;",
    ]
    rows = normalize_gestione_rs_regione(lines)
    codici = {(r["codice"], r["natura"]) for r in rows}
    assert codici == {("R1", "flusso"), ("R2", "flusso"), ("R13", "giacenza")}
    assert all(r["ripartizione"] == "np" for r in rows)
    assert all(r["area_geografica"] == "Lombardia" for r in rows)


@pytest.mark.pure_unit
def test_rs_produzione_regione_long_form():
    lines = [
        "Produzione regionale dei rifiuti speciali - 2024 (ISPRA);",
        "Regione;RS NP (t);RS P(t);RS codice CER ND (t);Totale (t);",
        "LOMBARDIA;32.869.577;3.566.532;0;36.436.109;",
        "Italia;161.256.298;10.794.252;0;172.050.550;",
    ]
    rows = normalize_rs_produzione_regione(lines)
    assert len(rows) == 2
    first = rows[0]
    assert first["dimensione"] == "area"
    assert first["etichetta"] == "Lombardia"
    assert first["area_geografica"] == "Lombardia"
    assert first["ripartizione"] == "totale"
    assert first["np_t"] == "32.869.577"
    assert first["totale_t"] == "36.436.109"


@pytest.mark.pure_unit
def test_impianti_regione_reads_both_geo_headers():
    lines = [
        "Censimento impianti di gestione dei rifiuti speciali - anno 2024 (ISPRA);",
        "Compostaggio",
        "Area geografica;Numero impianti;Fanghi (t);Altri RS (t);Totale RS (t)",
        "LOMBARDIA;24;78.627;219.959;298.586;",
        "Italia;250;1;2;3;",
        "Impianti di stoccaggio",
        "Regione;Numero impianti;RS NP(t);RS P(t)",
        "PIEMONTE;5;100;0;",
    ]
    rows = normalize_impianti_regione(lines)
    by_area = {r["area_geografica"]: r for r in rows}
    assert set(by_area) == {"Lombardia", "Italia", "Piemonte"}
    assert by_area["Lombardia"]["numero_impianti"] == "24"
    assert by_area["Piemonte"]["tipo_impianto"] == "Impianti di stoccaggio"


@pytest.mark.pure_unit
def test_html_entity_apostrophe_does_not_shift_columns(tmp_path):
    """`&apos;` contiene un ';' e spezzava il CSV (regressione 2022)."""
    raw = tmp_path / "in.csv"
    raw.write_text(
        "Censimento impianti di gestione dei rifiuti speciali - anno 2022 (ISPRA);\n"
        "Demolitori veicoli (d.lgs 209/2003)\n"
        "Area geografica;Numero impianti;Veicoli (t)\n"
        "VALLE D&apos;AOSTA;5;3.216;\n",
        encoding="utf-8",
    )
    out = tmp_path / "out.csv"
    normalize_csv(raw, out, "impianti_regione", 2022)
    rows = list(csv.DictReader(out.open(encoding="utf-8"), delimiter=";"))
    assert len(rows) == 1
    assert rows[0]["area_geografica"] == "Valle d'Aosta"
    assert rows[0]["numero_impianti"] == "5"
    assert rows[0]["totale_t"] == "3.216"
