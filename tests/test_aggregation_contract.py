"""Policy test: le aggregazioni di comuni non vanno scartate.

ISPRA attribuisce i dati di alcuni comuni a un'unione ("Aggregazione: X"):
la riga del capofila porta i dati dell'unione, i comuni aderenti
("Vedi aggregazione: X") portano solo la popolazione. Filtrare
`Dato riferito a = 'Comune'` sembra innocuo ma perde 20 unità e 114 comuni:
la Valle d'Aosta restava rappresentata dal solo comune di Aosta (RD 78,6%)
invece che dall'intera regione (71,7%, dato ufficiale ISPRA).
"""

from __future__ import annotations

import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
CLEAN_SQL = ROOT / "datasets" / "ispra-ru-base" / "sql" / "clean.sql"


@pytest.mark.policy
class TestAggregationUnits:
    def test_clean_classifies_units(self):
        sql = CLEAN_SQL.read_text()
        assert "tipo_dato" in sql, (
            "clean.sql non distingue comuni e aggregazioni (tipo_dato): "
            "i consumatori non possono ricostruire l'unità di rilevazione"
        )

    def test_clean_uses_adherent_rows_for_population(self):
        sql = CLEAN_SQL.read_text()
        assert "Vedi aggregazione" in sql, (
            "clean.sql non legge le righe 'Vedi aggregazione': senza quelle "
            "la popolazione dell'aggregazione resta quella del solo capofila "
            "e i pro-capite sono sbagliati"
        )
        assert "popolazione_unita" in sql, (
            "clean.sql non calcola la popolazione dell'unità (capofila + aderenti)"
        )

    def test_clean_does_not_drop_aggregations(self):
        sql = CLEAN_SQL.read_text()
        assert "dato_riferito_a) = 'Comune'" not in sql, (
            "clean.sql torna a filtrare i soli comuni: le aggregazioni "
            "sparirebbero dal layer pubblicato"
        )
