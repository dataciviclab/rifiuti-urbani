"""Contract test per il compose regionale `rifiuti_regioni`.

Due regressioni reali viste costruendolo:

1. I support vanno letti dal **clean** (glob multi-anno) e joinati su `anno`.
   `{support.X.mart.TABLE}` risolve al primo anno del support, non all'anno
   del candidate: il compose mostrava i dati 2018 anche per il 2024.
2. Le fonti regionali alternano "PIEMONTE", "Piemonte" e
   "Friuli-Venezia Giulia": il join deve usare una chiave regione
   normalizzata, altrimenti import/export restano NULL.
"""

from __future__ import annotations

import pathlib

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
COMPOSE = ROOT / "compose" / "rifiuti-regioni"
DATASET_YML = COMPOSE / "dataset.yml"
CLEAN_SQL = COMPOSE / "sql" / "clean.sql"


@pytest.mark.contract
class TestComposeRegioniContract:
    def test_clean_reads_support_clean_not_mart(self):
        sql = CLEAN_SQL.read_text()
        assert "{support." in sql, "il compose non usa i placeholder support"
        assert ".clean}'" in sql, (
            "il compose deve leggere il clean multi-anno dei support: "
            "il placeholder .mart.TABLE è single-year (primo anno)"
        )
        assert ".mart." not in sql, (
            "il compose usa {support.*.mart.*}, che risolve al primo anno "
            "del support invece dell'anno del candidate"
        )

    def test_clean_joins_every_support_on_anno(self):
        sql = CLEAN_SQL.read_text()
        # Una condizione b.anno = <alias>.anno per ogni support joinato.
        assert sql.count("b.anno = ") >= 6, (
            "ogni support deve essere joinato su anno, altrimenti si sommano "
            "anni diversi"
        )
        for alias in ("g", "i", "e", "f", "p", "r"):
            assert f"b.anno = {alias}.anno" in sql, (
                f"join del support '{alias}' senza condizione sull'anno"
            )

    def test_clean_normalizes_region_key(self):
        sql = CLEAN_SQL.read_text()
        assert "lower(replace(" in sql, (
            "il join regione deve normalizzare maiuscole e trattini: "
            "'PIEMONTE' e 'Piemonte' sono la stessa regione"
        )

    def test_dataset_declares_regional_mart(self):
        cfg = yaml.safe_load(DATASET_YML.read_text())
        assert cfg["dataset"]["name"] == "rifiuti_regioni"
        mart = cfg["mart"]
        table_names = {t["name"] for t in mart["tables"]}
        assert "mart_regioni" in table_names
        assert "mart_regioni" in mart["required_tables"]
        rule = mart["validate"]["table_rules"]["mart_regioni"]
        assert rule["primary_key"] == ["anno", "regione"]
