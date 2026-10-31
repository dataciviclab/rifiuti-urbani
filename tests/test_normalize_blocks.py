"""Contract test del normalizzatore multi-blocco ISPRA.

I file ISPRA contengono più tabelle con schemi diversi. Il parser deve
mappare per nome di colonna, non per posizione, e i risultati devono
quadrare con le tabelle di riepilogo che la fonte stessa pubblica:
quelle tabelle sono l'ancora, non un numero scritto a mano qui.

Anno usato: 2024 (file presente in `rifiuti-ispra-raw/raw-2024/`).
"""

from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "rifiuti-ispra-raw" / "raw-2024"
sys.path.insert(0, str(ROOT / "scripts"))

from normalize_ispra_all import (  # noqa: E402
    normalize_gestione_rs,
    normalize_gestione_ru,
    normalize_impianti,
    normalize_produzione_rs,
    parse_blocks,
)


def _lines(name: str) -> list[str]:
    path = RAW / f"{name}.csv"
    if not path.exists():
        pytest.skip(f"raw {name} 2024 non disponibile")
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def _num(value: str) -> float:
    value = (value or "").strip()
    if value in ("", "-"):
        return 0.0
    return float(value.replace(".", "").replace(",", "."))


def _riepilogo_totale(lines: list[str]) -> float:
    """TOTALE della tabella 'Riepilogo' ufficiale degli impianti."""
    for block in parse_blocks(lines):
        if "riepilogo" not in block["title"].lower():
            continue
        for row in block["rows"]:
            if row and row[0].strip().upper() == "TOTALE":
                return _num(row[1])
    pytest.skip("tabella Riepilogo non presente in questo anno")


@pytest.mark.contract
class TestImpianti:
    def test_conteggi_quadrano_col_riepilogo(self):
        lines = _lines("rs_impianti")
        atteso = _riepilogo_totale(lines)
        rows = normalize_impianti(lines)
        italia = [r for r in rows if r["area_geografica"] == "Italia"]
        totale = sum(_num(r["numero_impianti"]) for r in italia)
        assert totale == atteso

    def test_nessuna_riga_di_totale(self):
        rows = normalize_impianti(_lines("rs_impianti"))
        assert not [r for r in rows if r["tipo_impianto"].lower().startswith("totale")]

    def test_conteggi_con_separatore_migliaia(self):
        """Il bug originale: cast_bigint('1.409') → NULL."""
        rows = normalize_impianti(_lines("rs_impianti"))
        demolitori = [
            r for r in rows
            if "demolitori" in r["tipo_impianto"].lower() and r["area_geografica"] == "Italia"
        ]
        assert demolitori and _num(demolitori[0]["numero_impianti"]) > 1000

    def test_aree_sommano_alla_riga_italia(self):
        rows = normalize_impianti(_lines("rs_impianti"))
        per_tipo: dict[str, dict[str, float]] = {}
        for r in rows:
            per_tipo.setdefault(r["tipo_impianto"], {})[r["area_geografica"]] = _num(
                r["numero_impianti"]
            )
        for tipo, aree in per_tipo.items():
            if "Italia" not in aree:
                continue
            somma = sum(v for k, v in aree.items() if k != "Italia")
            assert somma == aree["Italia"], f"{tipo}: aree {somma} != Italia {aree['Italia']}"


@pytest.mark.contract
class TestProduzione:
    def test_attivita_somma_alla_sintesi(self):
        lines = _lines("rs_produzione")
        rows = normalize_produzione_rs(lines)
        sintesi = [r for r in rows if r["dimensione"] == "area" and r["area_geografica"] == "Italia"]
        atteso = _num(sintesi[0]["totale_t"])
        attivita = sum(
            _num(r["totale_t"]) for r in rows
            if r["dimensione"] == "attivita"
            and r["ripartizione"] == "totale"
            and r["area_geografica"] == "Italia"
        )
        assert attivita == atteso

    def test_pericolosi_piu_non_pericolosi_fa_il_totale(self):
        rows = normalize_produzione_rs(_lines("rs_produzione"))
        def somma(rip: str) -> float:
            return sum(
                _num(r["totale_t"] or r["np_t"] or r["p_t"]) for r in rows
                if r["dimensione"] == "attivita" and r["ripartizione"] == rip
                and r["area_geografica"] == "Italia"
            )
        assert somma("np") + somma("p") == somma("totale")


@pytest.mark.contract
class TestGestioneRS:
    def test_flussi_e_giacenze_separati(self):
        rows = normalize_gestione_rs(_lines("rs_gestione"))
        def somma(natura: str) -> float:
            return sum(
                _num(r["quantita_t"]) for r in rows
                if r["area_geografica"] == "Italia"
                and r["ripartizione"] == "totale"
                and r["tipo_operazione"] == "recupero"
                and r["natura"] == natura
            )
        flussi, giacenze = somma("flusso"), somma("giacenza")
        assert flussi > 0 and giacenze > 0
        assert flussi + giacenze > flussi  # non sono la stessa grandezza

    def test_ripartizioni_sommano_al_totale(self):
        rows = normalize_gestione_rs(_lines("rs_gestione"))
        def somma(rip: str) -> float:
            return sum(
                _num(r["quantita_t"]) for r in rows
                if r["area_geografica"] == "Italia"
                and r["ripartizione"] == rip
                and r["tipo_operazione"] == "recupero"
            )
        assert somma("np") + somma("p") == somma("totale")


@pytest.mark.contract
class TestGestioneRU:
    def test_conteggi_per_tipo_quadrano_con_andamento(self):
        """La tabella 'Andamento' è la serie ufficiale dei conteggi per tipo."""
        lines = _lines("ru_gestione")
        rows = normalize_gestione_ru(lines)

        andamento = next(
            (b for b in parse_blocks(lines) if "andamento" in b["title"].lower()), None
        )
        if andamento is None:
            pytest.skip("blocco Andamento non presente")

        riga = next((r for r in andamento["rows"] if r and r[0].strip() == "2024"), None)
        if riga is None:
            pytest.skip("anno 2024 non presente nella tabella Andamento")

        per_tipo = {
            r["tipo_impianto"]: _num(r["numero_impianti"])
            for r in rows if r["area_geografica"] == "Italia"
        }
        # l'ultima colonna dell'Andamento è il totale degli impianti RU
        assert sum(per_tipo.values()) == _num(riga[-1])
        assert len(per_tipo) == len(andamento["header"]) - 2  # -Anno, -Totale
