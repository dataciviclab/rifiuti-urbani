#!/usr/bin/env bash
# Download ISPRA Catasto Rifiuti CSV for multiple years
# Usage: ./download_multiyear.sh [start_year] [end_year]
# Example: ./download_multiyear.sh 2015 2024
set -euo pipefail

START=${1:-2018}
END=${2:-2024}

BASE="https://www.catasto-rifiuti.isprambiente.it"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Cookie acceptance first
COOKIE_JAR="$SCRIPT_DIR/.cookies.txt"
curl -s -c "$COOKIE_JAR" -b "$COOKIE_JAR" "${BASE}/index.php?pg=&advice=si" -o /dev/null

FAILED=()

# Scarica e valida. Senza `curl -f` una pagina 404 viene salvata come CSV: è
# già successo con `ru_gestione_comunale.csv`, che era una pagina HTML in tutti
# gli anni presenti in `raw/` (quel file non è più nella lista dei download).
# Meglio un file mancante che un file che sembra dati.
dl() {
  local url="$1"
  local outdir="$2"
  local fname="$3"
  mkdir -p "$outdir"
  local out="$outdir/$fname"

  if ! curl -sf -b "$COOKIE_JAR" -c "$COOKIE_JAR" "$url" -o "$out" 2>/dev/null; then
    rm -f "$out"
    FAILED+=("$fname: HTTP error")
    echo "  WARN: download fallita $fname"
    return 0
  fi

  # Content guard: le risposte di errore ISPRA sono pagine HTML o righe vuote.
  if head -c 200 "$out" | grep -qi '<html\|<!doctype\|404 not found'; then
    rm -f "$out"
    FAILED+=("$fname: risposta HTML")
    echo "  WARN: risposta HTML al posto del CSV: $fname"
    return 0
  fi

  if ! grep -q ';' "$out"; then
    rm -f "$out"
    FAILED+=("$fname: nessun delimitatore")
    echo "  WARN: CSV senza delimitatore ';': $fname"
    return 0
  fi

  return 0
}

# Un file è valido solo se non è una pagina di errore.
count_valid() {
  local dir="$1"
  local n=0
  local f
  for f in "$dir"/*.csv; do
    [ -e "$f" ] || continue
    if head -c 200 "$f" | grep -qi '<html\|<!doctype\|404 not found'; then
      continue
    fi
    n=$((n + 1))
  done
  echo "$n"
}

for YEAR in $(seq "$START" "$END"); do
  echo ""
  echo "=== YEAR $YEAR ==="

  OUTDIR="$SCRIPT_DIR/raw-$YEAR"
  mkdir -p "$OUTDIR"

  echo "[1/17] Costi comunali pro capite..."
  dl "${BASE}/costi/getCostiComunaleproc.csv.php?costicomuneproc&aa=${YEAR}&regid=1&regid2=Italia&reg1=Italia&p=1" "$OUTDIR" "costi_procapite.csv"

  echo "[2/17] Costi comunali per kg..."
  dl "${BASE}/costi/getCostiComunalechilo.csv.php?costicomuneproc&aa=${YEAR}&regid=1&regid2=Italia&reg1=Italia&p=1" "$OUTDIR" "costi_kg.csv"

  echo "[3/17] Dettaglio comunale RU..."
  dl "${BASE}/get/getDettaglioComunale.csv.php?&aa=${YEAR}" "$OUTDIR" "ru_produzione_comunale.csv"

  echo "[4/17] Gestione nazionale RU..."
  dl "${BASE}/gestione/getGestioneNazionale.csv.php?pg=nazione&aa=${YEAR}" "$OUTDIR" "ru_gestione.csv"

  echo "[5/17] Flussi extraregionali RU..."
  dl "${BASE}/obiettivi/flussiru.csv.php?pg=flussiregru&aa=${YEAR}&regid=&areaid=Italia&impid=" "$OUTDIR" "ru_flussi.csv"

  echo "[6/17] Export RU..."
  dl "${BASE}/obiettivi/exportru.csv.php?pg=exportru&aa=${YEAR}&regid=&areaid=Italia&impid=" "$OUTDIR" "ru_export.csv"

  echo "[7/17] Import RU..."
  dl "${BASE}/obiettivi/importru.csv.php?pg=importru&aa=${YEAR}&regid=&areaid=Italia&impid=" "$OUTDIR" "ru_import.csv"

  echo "[8/17] Produzione RS nazionale..."
  dl "${BASE}/speciali/getProduzioneRSNazionale.csv.php?pg=prodrsnazione&aa=${YEAR}" "$OUTDIR" "rs_produzione.csv"

  echo "[9/17] Gestione RS nazionale..."
  dl "${BASE}/speciali/getGestioneRSNazionale.csv.php?pg=gestrsnazione&aa=${YEAR}" "$OUTDIR" "rs_gestione.csv"

  echo "[10/17] Censimento impianti RS..."
  dl "${BASE}/speciali/getGestioneRSNazionaleCensimentoImp.csv.php?pg=nazione&aa=${YEAR}" "$OUTDIR" "rs_impianti.csv"

  echo "[11/17] Import RS..."
  dl "${BASE}/obiettivi/importrs.csv.php?pg=importrs&aa=${YEAR}&regid=&areaid=Italia&impid=" "$OUTDIR" "rs_import.csv"

  echo "[12/17] Export RS..."
  dl "${BASE}/obiettivi/exportrs.csv.php?pg=exportrs&aa=${YEAR}&regid=&areaid=Italia&impid=" "$OUTDIR" "rs_export.csv"

  echo "[13/17] Gestione RU regionale..."
  dl "${BASE}/gestione/getGestioneRegione.csv.php?pg=gestregione&aa=${YEAR}&regid=&areaid=Italia" "$OUTDIR" "ru_gestione_regionale.csv"

  echo "[14/17] Elenco impianti RU (per comune)..."
  dl "${BASE}/gestione/getDettaglioImpianto.csv.php?&aa=${YEAR}" "$OUTDIR" "ru_gestione_impianti.csv"

  echo "[15/17] Produzione RS regionale..."
  dl "${BASE}/speciali/getProduzioneRSRegione.csv.php?pg=prodrsnazione&aa=${YEAR}&regid=" "$OUTDIR" "rs_produzione_regionale.csv"

  echo "[16/17] Gestione RS regionale..."
  dl "${BASE}/speciali/getGestioneRSRegione.csv.php?pg=gestrsregione&aa=${YEAR}&regid=" "$OUTDIR" "rs_gestione_regionale.csv"

  echo "[17/17] Impianti RS regionali..."
  dl "${BASE}/speciali/getGestioneRSRegionaleCensimentoImp.csv.php?pg=gestregione&aa=${YEAR}&regid=&areaid=Italia" "$OUTDIR" "rs_impianti_regionali.csv"

  FILES=$(count_valid "$OUTDIR")
  echo "  Downloaded: $FILES files"
done

echo ""
echo "=== DONE ==="
echo "Years: $START-$END"
for d in "$SCRIPT_DIR"/raw-*/; do
  year=$(basename "$d")
  count=$(count_valid "$d")
  echo "  $year: $count files"
done

if [ ${#FAILED[@]} -gt 0 ]; then
  echo ""
  echo "⚠️  ${#FAILED[@]} download fallite:"
  printf '  - %s\n' "${FAILED[@]}"
  exit 1
fi
