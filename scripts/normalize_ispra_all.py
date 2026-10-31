#!/usr/bin/env python3
"""Normalize ISPRA CSVs into a consistent format.

Handles:
  - Costi procapite / costi per kg (2018-2024, varying columns)
  - Flussi / import / export (3-section title+header+data)
  - RS import / export (header+data, no title)
  - RS produzione / gestione / impianti (multi-section with 'sezione')

Usage:
  python normalize_ispra_all.py --input raw.csv --output clean.csv --type costi
  python normalize_ispra_all.py --input raw.csv --output clean.csv --type auto
  python normalize_ispra_all.py --batch --indir raw/ --outdir normalized/
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


def strip_crlf(line: str) -> str:
    return line.rstrip("\r\n")


def normalize_header_cell(cell: str) -> str:
    """Normalize a header cell: strip tabs, collapse whitespace."""
    return re.sub(r"\s+", " ", cell.strip().strip("\t")).strip()


def detect_type(lines: list[str]) -> str:
    """Detect ISPRA CSV type from raw lines."""
    # Find first non-empty, non-title, non-subtitle line
    for line in lines:
        stripped = strip_crlf(line).strip()
        if not stripped:
            continue
        # Title lines contain "costi" or "(ISPRA)"
        if "costi" in stripped.lower() or "(ISPRA)" in stripped:
            continue
        # Subtitle lines (e.g., "Compostaggio", "(i dati sui costi...)")
        if stripped.startswith("(") and "dati" in stripped.lower():
            continue
        # Skip subtitle lines that don't contain semicolons (not headers)
        if ";" not in stripped and len(stripped) < 50:
            continue
        # Header line - check columns
        cells = stripped.split(";")
        first = normalize_header_cell(cells[0]).lower()
        if first == "istatcomune":
            return "costi"
        if first in ("regione", "\tregione"):
            # Check if it's flussi or import/export
            if any("quantitativi" in strip_crlf(ln).lower() for ln in lines[:5]):
                return "flussi"
            if any("importati" in strip_crlf(ln).lower() for ln in lines[:5]):
                return "import"
            if any("esportati" in strip_crlf(ln).lower() for ln in lines[:5]):
                return "export"
            return "regione"  # generic region-level
        if first in ("area geografica", "\tarea geografica"):
            # Check if it's rs produzione/gestione/impianti
            if any("produzione" in strip_crlf(ln).lower() for ln in lines[:5]):
                return "area_produzione"
            if any("gestione" in strip_crlf(ln).lower() for ln in lines[:5]):
                return "area_gestione"
            if any("censimento" in strip_crlf(ln).lower() or "impiant" in strip_crlf(ln).lower() for ln in lines[:5]):
                return "area_impianti"
            return "area_geo"
        if first == "sezione":
            return "sezione"
        if first == "regione" and "rifiuti" in stripped.lower():
            return "rs_region"
        break
    # Fallback: check first data-like line
    for line in lines:
        stripped = strip_crlf(line).strip()
        if not stripped or "ispRA" in stripped or "costi" in stripped.lower():
            continue
        cells = stripped.split(";")
        if len(cells) >= 3:
            return "unknown"
    return "unknown"
    return "unknown"


def normalize_costi(lines: list[str], year: int) -> list[dict]:
    """Normalize costi procapite/kg CSVs.

    Costi procapite 2018-2019: CRTab;CTSab;CACab;CGINDab;CRDab;CTRab;CGDab;CSLab;CCab;CKab;CTOTab
    Costi procapite 2020+:     CRTab;CTSab;CRDab;CTRab;CSLab;CCab;CKab;Altri costi;CTOTab
    Costi kg (all years):      CRTkg;CRDkg;CSLkg;CCkg;CKkg;CTOTkg

    Output: istat_comune, comune, provincia, numero_comuni, popolazione,
            crt, cts, crd, ctr, csl, cc, ck, ctot
    (empty columns for missing values)
    """
    # Find header line (starts with IstatComune)
    header_idx = None
    for i, line in enumerate(lines):
        stripped = strip_crlf(line).strip().lstrip("\t")
        if stripped.startswith("IstatComune"):
            header_idx = i
            break
    if header_idx is None:
        return []

    raw_header = strip_crlf(lines[header_idx]).strip().lstrip("\t")
    raw_cols = [normalize_header_cell(c) for c in raw_header.split(";")]

    # Map raw column names to output names
    col_map = {}
    for i, c in enumerate(raw_cols):
        cl = c.lower()
        if cl == "istatcomune":
            col_map[i] = "istat_comune"
        elif cl == "comune o aggregazione":
            col_map[i] = "comune"
        elif cl == "provincia":
            col_map[i] = "provincia"
        elif cl == "numero di comuni":
            col_map[i] = "numero_comuni"
        elif cl in ("pop.(abitanti)", "popolazione"):
            col_map[i] = "popolazione"
        elif cl in ("crtab", "crtkg"):
            col_map[i] = "crt"
        elif cl in ("ctsab",):
            col_map[i] = "cts"
        elif cl in ("crdab", "crdkg"):
            col_map[i] = "crd"
        elif cl in ("ctrab",):
            col_map[i] = "ctr"
        elif cl in ("cslab", "cslkg"):
            col_map[i] = "csl"
        elif cl in ("ccab", "cckg"):
            col_map[i] = "cc"
        elif cl in ("ckab", "ckkg"):
            col_map[i] = "ck"
        elif cl in ("ctotab", "ctotkg"):
            col_map[i] = "ctot"
        # Skip: cacab, cgindab, cgdab, "altri costi" — not in output

    rows = []
    for line in lines[header_idx + 1:]:
        stripped = strip_crlf(line).strip()
        if not stripped:
            continue
        cells = stripped.rstrip(";").split(";")
        row = {}
        for src_idx, out_name in col_map.items():
            if src_idx < len(cells):
                row[out_name] = cells[src_idx].strip().strip("\t")
            else:
                row[out_name] = ""
        # Skip empty rows
        if not row.get("istat_comune"):
            continue
        rows.append(row)

    return rows


def normalize_region_level(lines: list[str], year: int, out_cols: list[str]) -> list[dict]:
    """Normalize region-level CSVs (flussi, import, export)."""
    # Find header line (starts with Regione or tab+Regione)
    header_idx = None
    for i, line in enumerate(lines):
        stripped = strip_crlf(line).strip().lstrip("\t")
        if stripped.startswith("Regione"):
            header_idx = i
            break
    if header_idx is None:
        return []

    raw_header = strip_crlf(lines[header_idx]).strip().lstrip("\t")
    raw_cols = [normalize_header_cell(c) for c in raw_header.split(";")]

    # Build column mapping
    col_map = {}
    for i, c in enumerate(raw_cols):
        cl = c.lower().replace("(t)", "").strip()
        if "regione" in cl:
            col_map[i] = "regione"
        elif "anno" in cl:
            col_map[i] = "anno"
        elif "non pericol" in cl:
            col_map[i] = "non_pericolosi_t"
        elif "pericol" in cl:
            col_map[i] = "pericolosi_t"
        elif "totale" in cl:
            col_map[i] = "totale_t"
        elif "quantitativ" in cl:
            col_map[i] = "quantita_t"
        elif "frazione" in cl or "organica" in cl:
            col_map[i] = "frazione_organica_t"

    rows = []
    for line in lines[header_idx + 1:]:
        stripped = strip_crlf(line).strip()
        if not stripped:
            continue
        # Stop at next section (title row, subtitle, or ANDAMENTO)
        if "(ISPRA)" in stripped or "Andamento" in stripped or "Quantitativi" in stripped:
            break
        # Stop at tab-indicating subtitle lines (no semicolons, short)
        if stripped.startswith("\t") and ";" not in stripped:
            break
        cells = stripped.rstrip(";").split(";")
        row = {}
        for src_idx, out_name in col_map.items():
            if src_idx < len(cells):
                row[out_name] = cells[src_idx].strip().strip("\t")
            else:
                row[out_name] = ""
        if not row.get("regione"):
            continue
        rows.append(row)

    return rows


def normalize_rs_region(lines: list[str], year: int) -> list[dict]:
    """Normalize RS import/export CSVs (header+data, no title)."""
    header_idx = None
    for i, line in enumerate(lines):
        stripped = strip_crlf(line).strip()
        if stripped.startswith("Regione"):
            header_idx = i
            break
    if header_idx is None:
        return []

    return normalize_region_level(lines[header_idx:], year, [])


def normalize_sezione(lines: list[str], year: int) -> list[dict]:
    """Normalize multi-section RS CSVs (produzione, gestione, impianti)."""
    # Find header line (starts with sezione or area geografica)
    header_idx = None
    for i, line in enumerate(lines):
        stripped = strip_crlf(line).strip().lstrip("\t")
        first = stripped.lower().split(";")[0].strip()
        if first.startswith("sezione") or first.startswith("area geografica"):
            header_idx = i
            break
    if header_idx is None:
        return []

    raw_header = strip_crlf(lines[header_idx]).strip().lstrip("\t")
    raw_cols = [normalize_header_cell(c) for c in raw_header.split(";")]

    # Generic column names for sezione-type CSVs
    out_cols = ["sezione"] + [f"col{i}" for i in range(1, len(raw_cols))]

    rows = []
    for line in lines[header_idx + 1:]:
        stripped = strip_crlf(line).strip()
        if not stripped:
            continue
        cells = stripped.rstrip(";").split(";")
        row = {}
        for i, col_name in enumerate(out_cols):
            if i < len(cells):
                row[col_name] = cells[i].strip().strip("\t")
            else:
                row[col_name] = ""
        if not row.get("sezione"):
            continue
        rows.append(row)

    return rows


# ── Parser multi-blocco ─────────────────────────────────────────────────────
#
# Un file ISPRA è una sequenza di blocchi: titolo (riga senza ';'), header
# (prima riga con ';') e righe dati. I blocchi hanno forme diverse: il
# mapping va fatto per nome di colonna, non per posizione.


def parse_blocks(lines: list[str]) -> list[dict]:
    """Divide un CSV ISPRA in blocchi {title, header, rows}."""
    blocks: list[dict] = []
    title: str | None = None
    current: dict | None = None

    for line in lines:
        stripped = strip_crlf(line).strip().lstrip("\t").strip()
        if not stripped:
            continue
        if ";" not in stripped:
            title = normalize_header_cell(stripped)
            current = None
            continue
        cells = [c.strip().strip("\t") for c in stripped.rstrip(";").split(";")]
        if len(cells) == 1:
            # Titolo di blocco (le righe di titolo ISPRA finiscono con ';')
            title = normalize_header_cell(cells[0])
            current = None
            continue
        if current is None:
            current = {"title": title or "", "header": [normalize_header_cell(c) for c in cells], "rows": []}
            blocks.append(current)
            title = None
        else:
            current["rows"].append(cells)

    return blocks


def _col_index(header: list[str], *needles: str, exact: bool = False) -> int | None:
    """Indice della prima colonna che contiene tutte le needles (case-insensitive)."""
    for i, col in enumerate(header):
        low = col.lower()
        if exact:
            if low == needles[0].lower() and all(n.lower() in low for n in needles):
                return i
        elif all(n.lower() in low for n in needles):
            return i
    return None


def _cell(row: list[str], idx: int | None) -> str:
    if idx is None or idx >= len(row):
        return ""
    return row[idx].strip().strip("\t")


def _first_index(header: list[str], *needle_sets: tuple[str, ...]) -> int | None:
    """Primo indice trovato tra più alternative di needles.

    Non usa `a or b`: l'indice 0 è valido (colonna in prima posizione) e
    `0 or x` lo scarterebbe.
    """
    for needles in needle_sets:
        idx = _col_index(header, *needles)
        if idx is not None:
            return idx
    return None


def _title_kind(title: str) -> str:
    """Ripartizione dedotta dal titolo del blocco."""
    low = title.lower()
    if "non pericolosi" in low and "pericolosi" not in low.replace("non pericolosi", ""):
        return "np"
    if "pericolosi" in low and "non pericolosi" not in low:
        return "p"
    if "non pericolosi" in low and "pericolosi" in low.replace("non pericolosi", ""):
        return "totale"
    return "totale"


def normalize_impianti(lines: list[str]) -> list[dict]:
    """ISPRA RS impianti: una riga per (tipo impianto, area).

    Salta il blocco "Riepilogo" (conteggio ufficiale per tipologia, usato
    come ancora di validazione nei test) e le legende.
    """
    rows: list[dict] = []
    for block in parse_blocks(lines):
        title = block["title"]
        header = block["header"]
        low_title = title.lower()
        if "riepilogo" in low_title or "legenda" in low_title:
            continue

        i_area = _col_index(header, "area geografica")
        i_tipo = _col_index(header, "tipologia")
        i_num = _col_index(header, "numero impianti")
        if i_area is None or i_num is None:
            continue

        i_np = _col_index(header, "non pericolosi")
        i_p = _col_index(header, "pericolosi") if i_np != _col_index(header, "pericolosi") else None
        i_tot = _col_index(header, "totale")
        # Incenerimento/Coincenerimento: "rifiuti combustibili" + "altri RS NP"
        i_altri_np = _col_index(header, "altri rs non pericolosi")
        i_rs_p = _col_index(header, "rs pericolosi")
        # Sezioni senza totale esplicito (TMB, demolitori): l'unica metrica è
        # l'ultima colonna, qualunque sia il nome ("RS(t)", "Veicoli (t)").
        i_unica = len(header) - 1 if i_tot is None and len(header) == 3 else None

        for row in block["rows"]:
            area = _cell(row, i_area)
            if area.lower() not in ("nord", "centro", "sud", "italia"):
                continue
            tipo = _cell(row, i_tipo) or title
            if tipo.strip().lower().startswith("totale"):
                continue  # riga di totale del blocco: è l'ancora di validazione, non un dato
            np_val = _cell(row, i_altri_np) or _cell(row, i_np)
            p_val = _cell(row, i_rs_p) or (_cell(row, i_p) if i_p not in (i_np, None) else "")
            # "non pericolosi"/"pericolosi" generici (discarica, altre tipologie)
            if i_np is not None and i_np == _col_index(header, "non pericolosi"):
                np_val = np_val or _cell(row, i_np)
            totale = _cell(row, i_tot) or _cell(row, i_unica)
            rows.append({
                "tipo_impianto": tipo,
                "area_geografica": area,
                "numero_impianti": _cell(row, i_num),
                "rs_non_pericolosi_t": np_val,
                "rs_pericolosi_t": p_val,
                "totale_t": totale,
            })
    return rows


def normalize_gestione_ru(lines: list[str]) -> list[dict]:
    """ISPRA RU gestione: una riga per (tipo impianto, area)."""
    rows: list[dict] = []
    for block in parse_blocks(lines):
        title = block["title"]
        header = block["header"]
        low_title = title.lower()
        if "andamento" in low_title or "legenda" in low_title:
            continue

        i_area = _col_index(header, "area geografica")
        i_num = _col_index(header, "numero impianti")
        if i_area is None or i_num is None:
            continue

        i_frazione = _first_index(header, ("frazione umida",), ("frazione organica",))
        i_verde = _col_index(header, "verde")
        i_ru = _first_index(header, ("tot. ru",), ("ru indiff",))
        i_fanghi = _col_index(header, "fanghi")
        i_altro = _col_index(header, "altro")
        # "Totale (t)" dove c'è; altrimenti "Tot. RU e tratt. RU (t)" (TMB, incenerimento…)
        i_tot = _first_index(header, ("totale",), ("tot.",))
        # TMB: il 7° valore (fanghi) non ha header
        extra_fanghi = len(header) == 6 and "tmb" in low_title

        for row in block["rows"]:
            area = _cell(row, i_area)
            if area.lower() not in ("nord", "centro", "sud", "italia"):
                continue
            fanghi = _cell(row, i_fanghi)
            if not fanghi and extra_fanghi:
                fanghi = row[6].strip() if len(row) > 6 else ""
            rows.append({
                "tipo_impianto": title,
                "area_geografica": area,
                "numero_impianti": _cell(row, i_num),
                "frazione_umida_t": _cell(row, i_frazione),
                "verde_t": _cell(row, i_verde),
                "tot_ru_t": _cell(row, i_ru),
                "fanghi_t": fanghi,
                "altro_t": _cell(row, i_altro),
                "totale_t": _cell(row, i_tot),
            })
    return rows


_OPERAZIONE = re.compile(r"^(R\d+|D\d+)(\s*al 31/12)?\s*(\(t\))?$", re.IGNORECASE)


def normalize_gestione_rs(lines: list[str]) -> list[dict]:
    """ISPRA RS gestione: forma lunga (area × ripartizione × operazione).

    R13/D15 sono giacenze a fine anno, non flussi: vanno marcate, altrimenti
    sommarle ai flussi gonfia i totali.
    """
    rows: list[dict] = []
    for block in parse_blocks(lines):
        title = block["title"]
        header = block["header"]
        if "legenda" in title.lower():
            continue
        i_area = _col_index(header, "area geografica")
        if i_area is None:
            continue

        ripartizione = _title_kind(title)
        # Il blocco "sintesi" aggrega R1-R12 / D1-D14 e ripeterebbe i dati
        # dei blocchi di dettaglio: si salta (le sue colonne di range non
        # matchano il regex dei codici singoli, ma R13/D15 sì).
        if any(re.match(r"^[RD]\d+\s*-\s*[RD]?\d+", col.strip(), re.IGNORECASE) for col in header):
            continue
        # blocchi "sintesi" (R1-R12, D1-D14 aggregati) non hanno operazioni singole
        operazioni = []
        for i, col in enumerate(header):
            m = _OPERAZIONE.match(col.strip())
            if m:
                codice = m.group(1).upper()
                natura = "giacenza" if "31/12" in col else "flusso"
                operazioni.append((i, codice, natura))
        if not operazioni:
            continue

        for row in block["rows"]:
            area = _cell(row, i_area)
            if area.lower() not in ("nord", "centro", "sud", "italia"):
                continue
            for idx, codice, natura in operazioni:
                rows.append({
                    "area_geografica": area,
                    "ripartizione": ripartizione,
                    "tipo_operazione": "recupero" if codice.startswith("R") else "smaltimento",
                    "codice": codice,
                    "natura": natura,
                    "quantita_t": _cell(row, idx),
                })
    return rows


def normalize_produzione_rs(lines: list[str]) -> list[dict]:
    """ISPRA RS produzione: forma lunga (dimensione × etichetta × area).

    Il file contiene 7 tabelle: sintesi per area, poi per attività economica
    e per capitolo EER, ognuna in versione totale / non pericolosi /
    pericolosi. Prima venivano accatastate come se fossero la stessa tabella.
    """
    rows: list[dict] = []
    for block in parse_blocks(lines):
        title = block["title"]
        header = block["header"]
        low_title = title.lower()
        if "legenda" in low_title:
            continue
        ripartizione = _title_kind(title)

        i_area = _col_index(header, "area geografica")
        i_etichetta = _first_index(header, ("descrizione attivita",), ("capitolo",))

        if i_area is not None and i_etichetta is None:
            # blocco "Dati di sintesi": una riga per area
            i_np = _col_index(header, "rs np")
            i_p = _col_index(header, "rs p")
            i_nd = _col_index(header, "cer nd")
            i_tot = _col_index(header, "totale")
            for row in block["rows"]:
                area = _cell(row, i_area)
                if area.lower() not in ("nord", "centro", "sud", "italia"):
                    continue
                rows.append({
                    "dimensione": "area",
                    "etichetta": area,
                    "area_geografica": area,
                    "ripartizione": "totale",
                    "np_t": _cell(row, i_np),
                    "p_t": _cell(row, i_p),
                    "cer_nd_t": _cell(row, i_nd),
                    "totale_t": _cell(row, i_tot),
                })
            continue

        if i_etichetta is None:
            continue

        # blocchi per attività / capitolo: le aree sono colonne
        cols_area = {}
        for nome in ("nord", "centro", "sud", "italia"):
            idx = _col_index(header, nome)
            if idx is not None:
                cols_area[nome.capitalize() if nome != "italia" else "Italia"] = idx
        if not cols_area:
            continue

        dimensione = "attivita" if "attivita" in low_title else "capitolo"
        for row in block["rows"]:
            etichetta = _cell(row, i_etichetta)
            if not etichetta or etichetta.strip().lower().startswith("totale"):
                continue  # riga di totale della tabella
            for area, idx in cols_area.items():
                valore = _cell(row, idx)
                rows.append({
                    "dimensione": dimensione,
                    "etichetta": etichetta,
                    "area_geografica": area,
                    "ripartizione": ripartizione,
                    "np_t": valore if ripartizione == "np" else "",
                    "p_t": valore if ripartizione == "p" else "",
                    "cer_nd_t": "",
                    "totale_t": valore if ripartizione == "totale" else "",
                })
    return rows


def normalize_csv(input_path: Path, output_path: Path, csv_type: str = "auto", year: int = 0) -> str:
    raw = input_path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")

    lines = text.splitlines()
    if not lines:
        return "empty"

    # Detect type
    if csv_type == "auto":
        detected = detect_type(lines)
    else:
        detected = csv_type

    # Normalize
    if detected == "costi":
        rows = normalize_costi(lines, year)
        if not rows:
            return "empty"
        out_cols = ["istat_comune", "comune", "provincia", "numero_comuni",
                    "popolazione", "crt", "cts", "crd", "ctr", "csl", "cc", "ck", "ctot"]
    elif detected in ("flussi", "import", "export", "regione"):
        rows = normalize_region_level(lines, year, [])
        if not rows:
            return "empty"
        out_cols = list(rows[0].keys())
    elif detected == "rs_region":
        rows = normalize_rs_region(lines, year)
        if not rows:
            return "empty"
        out_cols = list(rows[0].keys())
    elif detected in ("sezione", "area_produzione", "area_gestione", "area_impianti", "area_geo"):
        rows = normalize_sezione(lines, year)
        if not rows:
            return "empty"
        out_cols = list(rows[0].keys())
    elif detected == "impianti":
        rows = normalize_impianti(lines)
        if not rows:
            return "empty"
        out_cols = ["tipo_impianto", "area_geografica", "numero_impianti",
                    "rs_non_pericolosi_t", "rs_pericolosi_t", "totale_t"]
    elif detected == "gestione_ru":
        rows = normalize_gestione_ru(lines)
        if not rows:
            return "empty"
        out_cols = ["tipo_impianto", "area_geografica", "numero_impianti", "frazione_umida_t",
                    "verde_t", "tot_ru_t", "fanghi_t", "altro_t", "totale_t"]
    elif detected == "gestione_rs":
        rows = normalize_gestione_rs(lines)
        if not rows:
            return "empty"
        out_cols = ["area_geografica", "ripartizione", "tipo_operazione", "codice",
                    "natura", "quantita_t"]
    elif detected == "produzione_rs":
        rows = normalize_produzione_rs(lines)
        if not rows:
            return "empty"
        out_cols = ["dimensione", "etichetta", "area_geografica", "ripartizione",
                    "np_t", "p_t", "cer_nd_t", "totale_t"]
    else:
        # Unknown type: pass through with minimal normalization
        rows = []
        for line in lines:
            stripped = strip_crlf(line).strip()
            if not stripped:
                continue
            cells = stripped.rstrip(";").split(";")
            rows.append({f"col{i}": c.strip().strip("\t") for i, c in enumerate(cells)})
        if not rows:
            return "empty"
        out_cols = list(rows[0].keys())

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out_cols, delimiter=";", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    return detected


def main():
    parser = argparse.ArgumentParser(description="Normalize ISPRA CSVs")
    parser.add_argument("--input", "-i", type=Path, help="Input CSV file")
    parser.add_argument("--output", "-o", type=Path, help="Output CSV file")
    parser.add_argument("--type", "-t", default="auto",
                        choices=["auto", "costi", "flussi", "import", "export",
                                 "rs_region", "sezione", "impianti", "gestione_ru",
                                 "gestione_rs", "produzione_rs"],
                        help="CSV type (default: auto-detect)")
    parser.add_argument("--year", "-y", type=int, default=0, help="Year (for auto-naming)")
    parser.add_argument("--batch", action="store_true", help="Batch mode: process directory")
    parser.add_argument("--indir", type=Path, help="Input directory for batch mode")
    parser.add_argument("--outdir", type=Path, help="Output directory for batch mode")
    args = parser.parse_args()

    if args.batch:
        if not args.indir or not args.outdir:
            parser.error("--batch requires --indir and --outdir")
        indir = args.indir
        outdir = args.outdir
        outdir.mkdir(parents=True, exist_ok=True)

        for csv_file in sorted(indir.glob("*.csv")):
            # Extract year from filename (e.g., ispra_ru_costi_procapite_2020.csv)
            m = re.search(r"(\d{4})", csv_file.stem)
            year = int(m.group(1)) if m else 0
            out_file = outdir / csv_file.name
            detected = normalize_csv(csv_file, out_file, args.type, year)
            print(f"  {csv_file.name}: type={detected}, year={year}")
    else:
        if not args.input or not args.output:
            parser.error("--input and --output required in single mode")
        detected = normalize_csv(args.input, args.output, args.type, args.year)
        print(f"  type={detected}")


if __name__ == "__main__":
    main()
