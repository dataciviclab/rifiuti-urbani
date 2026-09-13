#!/usr/bin/env python3
"""Remove title rows from ISPRA CSVs that have multi-line headers.

ISPRA CSVs have a pattern:
  Line 1: Title description (e.g., "Quantitativi di rifiuti...")
  Line 2: Header with tab prefix (e.g., "\tRegione;Anno;...")
  Line 3+: Data rows

DuckDB fails on line 1 because it has different column count.
This script outputs only lines 2+ (header + data), removing the title.
"""
import csv
import sys
from pathlib import Path


def clean_ispra_csv(input_path: Path, output_path: Path) -> None:
    """Skip title rows, keep header + data."""
    with open(input_path, encoding="utf-8-sig") as fin, \
         open(output_path, "w", newline="", encoding="utf-8") as fout:
        writer = csv.writer(fout, delimiter=";")
        for i, line in enumerate(fin):
            line = line.rstrip("\r\n")
            if not line.strip():
                continue
            # Skip title rows (no semicolons or starts with text before semicolons)
            parts = line.split(";")
            if len(parts) < 3:
                continue
            # Clean tab prefix from first column
            row = [p.strip().lstrip("\t") for p in parts]
            writer.writerow(row)
    print(f"Cleaned {input_path.name} -> {output_path.name}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input.csv> <output.csv>")
        sys.exit(1)
    clean_ispra_csv(Path(sys.argv[1]), Path(sys.argv[2]))
