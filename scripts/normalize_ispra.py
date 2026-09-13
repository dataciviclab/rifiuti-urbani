#!/usr/bin/env python3
"""Normalize ISPRA multi-section CSVs."""
import csv
import re
import sys
from pathlib import Path

AREAS = {'Nord', 'Centro', 'Sud', 'Italia'}


def normalize_ispra(input_path: Path, output_path: Path) -> None:
    rows = []
    current_section = None

    with open(input_path, encoding="utf-8-sig") as f:
        for raw_line in f:
            line = raw_line.rstrip("\r\n")
            if not line:
                continue

            raw_starts_tab = line.startswith("\t")
            stripped = line.strip()
            has_semi = ";" in stripped

            if not has_semi:
                # No semicolons: could be title (tab + text) or empty
                if raw_starts_tab:
                    text = stripped.lstrip("\t").strip()
                    if text and text not in AREAS and not text.startswith("Area"):
                        current_section = text
                continue

            # Has semicolons
            before_semi = stripped.split(";")[0].strip()

            # Title detection: long text (>30 chars), not area, not number, not header
            is_title = (
                len(before_semi) > 30
                and before_semi not in AREAS
                and not re.match(r'^\d', before_semi)
                and 'Totale' not in before_semi
                and 'Area geografica' not in before_semi
                and 'Descrizione' not in before_semi
            )

            if is_title:
                current_section = before_semi
                continue

            # Data row (with or without tab prefix)
            if current_section:
                parts = [p.strip() for p in stripped.split(";")]
                while parts and not parts[-1]:
                    parts.pop()
                if parts and parts[0]:
                    rows.append([current_section] + parts)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["sezione", "col1", "col2", "col3", "col4", "col5"])
        for r in rows:
            padded = r + [""] * (6 - len(r))
            writer.writerow(padded[:6])

    print(f"Extracted {len(rows)} rows -> {output_path}")
    from collections import Counter
    sections = Counter(r[0][:70] for r in rows)
    for s, n in sections.most_common():
        print(f"  {n:3d}  {s[:70]}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <input.csv> <output.csv>")
        sys.exit(1)
    normalize_ispra(Path(sys.argv[1]), Path(sys.argv[2]))
