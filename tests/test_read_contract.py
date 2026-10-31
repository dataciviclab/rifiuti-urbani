"""Contract tests sulla lettura raw e sulle righe di totale.

Due classi di bug già viste in questo repo (e in altri repo del Lab):

1. `clean.read.source: auto` fa tipizzare DOUBLE le colonne di numeri in
   formato italiano senza separatore delle migliaia. Le macro
   `normalize_italian_*` lavorano su stringhe: il valore viene corrotto
   (×100 / ÷10). Rimedio contrattuale: `all_varchar: true` oppure colonne
   dichiarate VARCHAR (toolkit#520, dichiarazioni-italia#21).
2. Le fonti regionali ISPRA includono una riga di totale `Italia` accanto
   alle regioni: sommarla raddoppia i totali (export RU 2,6 Mt invece di
   1,3 Mt). Rimedio: colonna `is_aggregato` nel clean, esclusa nei mart.
"""

from __future__ import annotations

import pathlib
import re

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATASETS_DIR = ROOT / "datasets"

NUMERIC_MACROS = ("normalize_italian_number", "normalize_italian_integer", "remove_dot_thousands")

# Dataset regionali la cui fonte espone la riga di totale nazionale.
REGIONAL_DATASETS = (
    "ispra_ru_export",
    "ispra_ru_import",
    "ispra_rs_export",
    "ispra_rs_import",
    "ispra_ru_flussi",
)


def _entries() -> list[tuple[str, pathlib.Path]]:
    return [
        (d.name, d)
        for d in sorted(DATASETS_DIR.iterdir())
        if (d / "dataset.yml").exists()
    ]


ENTRIES = _entries()
IDS = [name for name, _ in ENTRIES]


def _load(dirpath: pathlib.Path) -> dict:
    return yaml.safe_load((dirpath / "dataset.yml").read_text())


def _macro_columns(sql: str) -> set[str]:
    """Nomi di colonna passati alle macro numeriche (con o senza virgolette)."""
    cols: set[str] = set()
    for macro in NUMERIC_MACROS:
        for match in re.finditer(rf"{macro}\(\s*\"?([A-Za-z0-9_ .()]+)\"?\s*\)", sql):
            cols.add(match.group(1).strip())
    return cols


@pytest.mark.policy
class TestVarcharReadContract:
    """Chi usa le macro numeriche su raw italiano deve leggere VARCHAR."""

    @pytest.fixture(params=ENTRIES, ids=IDS)
    def entry(self, request):
        name, path = request.param
        return name, path, _load(path)

    def test_numeric_macros_get_varchar_input(self, entry):
        name, path, cfg = entry
        clean = cfg.get("clean", {}) or {}
        sql_path = path / clean["sql"]
        sql = sql_path.read_text()
        macro_cols = _macro_columns(sql)
        if not macro_cols:
            pytest.skip(f"{name}: nessuna macro numerica")

        read = clean.get("read", {}) or {}
        if read.get("all_varchar") is True:
            return  # tutto VARCHAR: le macro sono l'unico punto di conversione

        declared = read.get("columns") or {}
        if not declared:
            pytest.fail(
                f"{name}: clean.read usa source auto senza all_varchar né colonne "
                f"dichiarate; le macro numeriche ({sorted(macro_cols)}) possono "
                f"ricevere DOUBLE e corrompere i valori (toolkit#520)"
            )

        non_varchar = [
            col for col in macro_cols
            if col in declared and "VARCHAR" not in str(declared[col]).upper()
        ]
        assert not non_varchar, (
            f"{name}: colonne passate a macro numeriche dichiarate non-VARCHAR: {non_varchar}"
        )


@pytest.mark.policy
class TestAggregateRowsContract:
    """I dataset regionali devono marcare la riga di totale e non sommarla."""

    @pytest.fixture(params=[n for n, _ in ENTRIES if n in REGIONAL_DATASETS])
    def entry(self, request):
        name = request.param
        path = DATASETS_DIR / name
        return name, path, _load(path)

    def test_clean_marks_aggregate_row(self, entry):
        name, path, cfg = entry
        sql = (path / cfg["clean"]["sql"]).read_text()
        assert "is_aggregato" in sql, (
            f"{name}: clean.sql non marca la riga di totale nazionale (is_aggregato)"
        )

    def test_mart_excludes_aggregate_row(self, entry):
        name, path, cfg = entry
        for table in cfg.get("mart", {}).get("tables", []):
            sql = (path / table["sql"]).read_text()
            assert "NOT is_aggregato" in sql, (
                f"{name}/{table['name']}: mart somma anche la riga di totale "
                f"nazionale (manca NOT is_aggregato)"
            )
