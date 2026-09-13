#!/usr/bin/env python3
"""Normalize ISPRA multi-section CSV to uniform 3-column format.

The raw CSV has sections separated by title rows with different column counts.
DuckDB's union_by_name sniffing fails on this. This script:
1. Reads the raw CSV
2. Identifies sections by title rows
3. Outputs a normalized CSV with: sezione, col1, col2, col3
"""
import csv
import sys
from pathlib import Path

SECTIONS = {
    "organica": "frazione_organica",
    "incenerimento": "incenerimento",
    "discarica": "discarica",
}

def normalize(input_path: Path, output_path: Path) -> None:
    rows = []
    current_section = None

    with open(input_path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.rstrip("\r\n")
            if not line.strip():
                continue

            # Title row detection
            for keyword, section_name in SECTIONS.items():
                if keyword in line.lower() and "quantitativi" in line.lower():
                    current_section = section_name
                    break
            else:
                # Data or header row
                if current_section is None:
                    continue

                parts = line.split(";")
                if len(parts) < 2:
                    continue

                col1 = parts[0].strip().lstrip("\t")
                col2 = parts[1].strip() if len(parts) > 1 else ""

                # Skip header rows
                if col1.lower().startswith("regione") or col1.lower().startswith("area"):
                    continue

                # Valid area names
                valid_areas = {
                    "piemonte", "valle d'aosta", "lombardia", "trentino alto adige",
                    "trentino-alto adige", "veneto", "friuli venezia giulia",
                    "friuli-venezia giulia", "liguria", "emilia romagna",
                    "emilia-romagna", "toscana", "umbria", "marche", "lazio",
                    "abruzzo", "molise", "campania", "puglia", "basilicata",
                    "calabria", "sicilia", "sardegna", "italia",
                    "piemonte", "lombardia", "veneto", "liguria", "toscana",
                    "lazio", "campania", "sicilia", "sardegna",
                }
                if col1.lower() not in valid_areas:
                    continue

                col3 = parts[2].strip() if len(parts) > 2 else ""
                rows.append([current_section, col1, col2, col3])

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["sezione", "col1", "col2", "col3"])
        writer.writerows(rows)

    print(f"Normalized {len(rows)} data rows -> {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input.csv> <output.csv>")
        sys.exit(1)
    normalize(Path(sys.argv[1]), Path(sys.argv[2]))
