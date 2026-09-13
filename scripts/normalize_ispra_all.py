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
import sys
from pathlib import Path


def strip_crlf(line: str) -> str:
    return line.rstrip("\r\n")


def normalize_header_cell(cell: str) -> str:
    """Normalize a header cell: strip tabs, collapse whitespace."""
    return re.sub(r"\s+", " ", cell.strip().strip("\t")).strip()


def detect_type(lines: list[str]) -> str:
    """Detect ISPRA CSV type from raw lines."""
    # Find first non-empty, non-title line
    for line in lines:
        stripped = strip_crlf(line).strip()
        if not stripped:
            continue
        # Title lines contain "costi" or "(ISPRA)"
        if "costi" in stripped.lower() or "(ISPRA)" in stripped:
            continue
        # Subtitle lines
        if stripped.startswith("(") and "dati" in stripped.lower():
            continue
        # Header line - check columns
        cells = stripped.split(";")
        first = normalize_header_cell(cells[0]).lower()
        if first == "istatcomune":
            return "costi"
        if first in ("regione", "\tregione"):
            # Check if it's flussi or import/export
            if any("quantitativi" in strip_crlf(l).lower() for l in lines[:3]):
                return "flussi"
            if any("importati" in strip_crlf(l).lower() for l in lines[:3]):
                return "import"
            if any("esportati" in strip_crlf(l).lower() for l in lines[:3]):
                return "export"
            return "regione"  # generic region-level
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

    out_cols = ["istat_comune", "comune", "provincia", "numero_comuni",
                "popolazione", "crt", "cts", "crd", "ctr", "csl", "cc", "ck", "ctot"]

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
    # Find header line (starts with sezione)
    header_idx = None
    for i, line in enumerate(lines):
        stripped = strip_crlf(line).strip().lstrip("\t")
        if stripped.lower().startswith("sezione"):
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


def normalize_csv(input_path: Path, output_path: Path, csv_type: str = "auto", year: int = 0) -> str:
    """Normalize a single ISPRA CSV file. Returns detected type."""
    raw = input_path.read_bytes()
    # Decode: try utf-8 first, then latin-1
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
    elif detected == "sezione":
        rows = normalize_sezione(lines, year)
        if not rows:
            return "empty"
        out_cols = list(rows[0].keys())
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
                                 "rs_region", "sezione"],
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
