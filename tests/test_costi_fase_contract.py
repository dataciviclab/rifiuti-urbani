"""Contract test: il compose RU espone il costo del recupero vs smaltimento.

`rifiuti_urbani_unified` dichiara di unificare RD% e costi. Il suo clean.sql
leggeva CTS (trattamento e smaltimento) e CTR (trattamento e recupero) da
`ispra_ru_costi_procapite` ma non li propagava: nessun consumer poteva
confrontare il costo del recupero con quello dello smaltimento. Il test
protegge il contratto pubblico (colonne esposte e indicatori derivati),
non l'implementazione interna.
"""

from __future__ import annotations

import pathlib

import duckdb
import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
COMPOSE = ROOT / "compose" / "rifiuti-urbani-unified"
DATASET_YML = COMPOSE / "dataset.yml"
CLEAN_SQL = COMPOSE / "sql" / "clean.sql"
MART_COMUNI_SQL = COMPOSE / "sql" / "mart_comuni.sql"
MART_COSTI_SQL = COMPOSE / "sql" / "mart_costi_fase.sql"

CLEAN_INPUT_COLUMNS = {
    "anno": "INTEGER",
    "codice_comune_istat": "VARCHAR",
    "regione": "VARCHAR",
    "provincia": "VARCHAR",
    "comune": "VARCHAR",
    "popolazione": "BIGINT",
    "classe_demografica": "VARCHAR",
    "percentuale_rd": "DOUBLE",
    "kg_ru_per_abitante": "DOUBLE",
    "totale_ru_tonnellate": "DOUBLE",
    "totale_rd_tonnellate": "DOUBLE",
    "crt_euro_ab": "DOUBLE",
    "cts_euro_ab": "DOUBLE",
    "crd_euro_ab": "DOUBLE",
    "ctr_euro_ab": "DOUBLE",
    "csl_euro_ab": "DOUBLE",
    "cc_euro_ab": "DOUBLE",
    "ck_euro_ab": "DOUBLE",
    "ctot_euro_ab": "DOUBLE",
}


@pytest.mark.contract
class TestCostItemsPropagated:
    """CTS e CTR devono sopravvivere dal clean al mart del compose."""

    def test_clean_propagates_disposal_and_recovery_cost(self):
        sql = CLEAN_SQL.read_text()
        for col in ("cts_euro_ab", "ctr_euro_ab"):
            assert col in sql, (
                f"clean.sql del compose non espone {col}: il costo di "
                "smaltimento/recupero arriva da ispra_ru_costi_procapite e "
                "va propagato, altrimenti nessun consumer può confrontarlo"
            )

    def test_mart_comuni_propagates_disposal_and_recovery_cost(self):
        sql = MART_COMUNI_SQL.read_text()
        for col in ("cts_euro_ab", "ctr_euro_ab"):
            assert col in sql, f"mart_comuni.sql non espone {col}"


@pytest.mark.contract
class TestCostiFaseContract:
    """Il mart costi_per_fase è dichiarato e protetto dalla validazione."""

    def test_mart_declared_with_required_columns(self):
        cfg = yaml.safe_load(DATASET_YML.read_text())
        mart = cfg["mart"]
        table_names = {t["name"] for t in mart["tables"]}
        assert "mart_costi_fase" in table_names
        assert "mart_costi_fase" in mart["required_tables"]

        rule = mart["validate"]["table_rules"]["mart_costi_fase"]
        assert "primary_key" in rule
        for col in (
            "quota_cts_pct",
            "quota_ctr_pct",
            "rapporto_recupero_smaltimento",
            "costo_per_punto_rd_euro",
        ):
            assert col in rule["required_columns"], (
                f"mart_costi_fase non protegge la colonna {col}"
            )


@pytest.mark.pure_unit
class TestCostiFaseSemantics:
    """Gli indicatori derivati rispettano le unità e gestiscono i casi limite."""

    @pytest.fixture
    def result(self):
        con = duckdb.connect()
        columns = ", ".join(f"{name} {typ}" for name, typ in CLEAN_INPUT_COLUMNS.items())
        con.execute(f"CREATE TABLE clean_input ({columns})")
        con.execute(
            """
            INSERT INTO clean_input VALUES
              -- completo e coerente: 200 €/ab, RD 50%, 500 kg/ab
              (2024, 'A', 'Regione', 'Prov', 'Comune A', 1000, 'media',
               50.0, 500.0, 500.0, 250.0,
               20, 60, 40, 40, 20, 15, 5, 200),
              -- CTS assente e RD 0: i rapporti non devono esplodere
              (2024, 'B', 'Regione', 'Prov', 'Comune B', 1000, 'media',
               0.0, 500.0, 500.0, 0.0,
               20, NULL, 40, 10, 20, 15, 5, 100),
              -- ctot nullo/zero: escluse dal mart
              (2024, 'C', 'Regione', 'Prov', 'Comune C', 1000, 'media',
               40.0, 400.0, 400.0, 160.0,
               10, 20, 10, 20, 10, 10, 10, 0),
              (2024, 'D', 'Regione', 'Prov', 'Comune D', 1000, 'media',
               40.0, 400.0, 400.0, 160.0,
               10, 20, 10, 20, 10, 10, 10, NULL)
            """
        )
        df = con.execute(MART_COSTI_SQL.read_text()).fetchdf().set_index("codice_comune_istat")
        con.close()
        return df

    def test_filters_unusable_costs(self, result):
        assert set(result.index) == {"A", "B"}

    def test_composition_and_ratio(self, result):
        a = result.loc["A"]
        assert a["quota_cts_pct"] == pytest.approx(30.0)
        assert a["quota_ctr_pct"] == pytest.approx(20.0)
        assert a["quota_altri_pct"] == pytest.approx(0.0, abs=0.01)
        assert a["quota_costo_fisso_pct"] == pytest.approx(20.0)
        assert a["quota_costo_variabile_pct"] == pytest.approx(80.0)
        assert a["rapporto_recupero_smaltimento"] == pytest.approx(40 / 60, abs=1e-3)

    def test_efficiency_indicators(self, result):
        a = result.loc["A"]
        assert a["costo_per_punto_rd_euro"] == pytest.approx(4.0)
        assert a["costo_per_tonnellata_euro"] == pytest.approx(400.0)
        assert a["cts_cent_kg"] == pytest.approx(12.0)
        assert a["ctr_cent_kg"] == pytest.approx(8.0)

    def test_missing_disposal_cost_does_not_divide_by_zero(self, result):
        b = result.loc["B"]
        assert b["quota_cts_pct"] is None or b["quota_cts_pct"] != b["quota_cts_pct"]
        assert b["rapporto_recupero_smaltimento"] is None or (
            b["rapporto_recupero_smaltimento"] != b["rapporto_recupero_smaltimento"]
        )
        assert b["costo_per_punto_rd_euro"] is None or (
            b["costo_per_punto_rd_euro"] != b["costo_per_punto_rd_euro"]
        )
