#!/usr/bin/env bash
# Download ISPRA Catasto Rifiuti CSV for multiple years
# Usage: ./download_multiyear.sh [start_year] [end_year]
# Example: ./download_multiyear.sh 2015 2024
set -euo pipefail

START=${1:-2018}
END=${2:-2024}

BASE="https://www.catasto-rifiuti.isprambiente.it"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Cookie acceptance
COOKIE_JAR="$SCRIPT_DIR/.cookies.txt"
curl -s -c "$COOKIE_JAR" -b "$COOKIE_JAR" "${BASE}/index.php?pg=&advice=si" -o /dev/null

dl() {
  local url="$1"
  local outdir="$2"
  local fname="$3"
  mkdir -p "$outdir"
  curl -s -b "$COOKIE_JAR" -c "$COOKIE_JAR" "$url" -o "$outdir/$fname" 2>/dev/null || echo "  WARN: failed $fname"
}

for YEAR in $(seq "$START" "$END"); do
  echo ""
  echo "=== YEAR $YEAR ==="

  OUTDIR="$SCRIPT_DIR/raw-$YEAR"
  mkdir -p "$OUTDIR"

  echo "[1/13] Costi comunali pro capite..."
  dl "${BASE}/costi/getCostiComunaleproc.csv.php?costicomuneproc&aa=${YEAR}&regid=1&regid2=Italia&reg1=Italia&p=1" "$OUTDIR" "costi_procapite.csv"

  echo "[2/13] Costi comunali per kg..."
  dl "${BASE}/costi/getCostiComunalechilo.csv.php?costicomuneproc&aa=${YEAR}&regid=1&regid2=Italia&reg1=Italia&p=1" "$OUTDIR" "costi_kg.csv"

  echo "[3/13] Dettaglio comunale RU..."
  dl "${BASE}/get/getDettaglioComunale.csv.php?&aa=${YEAR}" "$OUTDIR" "ru_produzione_comunale.csv"

  echo "[4/13] Gestione nazionale RU..."
  dl "${BASE}/gestione/getGestioneNazionale.csv.php?pg=nazione&aa=${YEAR}" "$OUTDIR" "ru_gestione.csv"

  echo "[5/13] Flussi extraregionali RU..."
  dl "${BASE}/obiettivi/flussiru.csv.php?pg=flussiregru&aa=${YEAR}&regid=&areaid=Italia&impid=" "$OUTDIR" "ru_flussi.csv"

  echo "[6/13] Export RU..."
  dl "${BASE}/obiettivi/exportru.csv.php?pg=exportru&aa=${YEAR}&regid=&areaid=Italia&impid=" "$OUTDIR" "ru_export.csv"

  echo "[7/13] Import RU..."
  dl "${BASE}/obiettivi/importru.csv.php?pg=importru&aa=${YEAR}&regid=&areaid=Italia&impid=" "$OUTDIR" "ru_import.csv"

  echo "[8/13] Produzione RS nazionale..."
  dl "${BASE}/speciali/getProduzioneRSNazionale.csv.php?pg=prodrsnazione&aa=${YEAR}" "$OUTDIR" "rs_produzione.csv"

  echo "[9/13] Gestione RS nazionale..."
  dl "${BASE}/speciali/getGestioneRSNazionale.csv.php?pg=gestrsnazione&aa=${YEAR}" "$OUTDIR" "rs_gestione.csv"

  echo "[10/13] Censimento impianti RS..."
  dl "${BASE}/speciali/getGestioneRSNazionaleCensimentoImp.csv.php?pg=nazione&aa=${YEAR}" "$OUTDIR" "rs_impianti.csv"

  echo "[11/13] Import RS..."
  dl "${BASE}/obiettivi/importrs.csv.php?pg=importrs&aa=${YEAR}&regid=&areaid=Italia&impid=" "$OUTDIR" "rs_import.csv"

  echo "[12/13] Export RS..."
  dl "${BASE}/obiettivi/exportrs.csv.php?pg=exportrs&aa=${YEAR}&regid=&areaid=Italia&impid=" "$OUTDIR" "rs_export.csv"

  echo "[13/13] Gestione RU comunale..."
  dl "${BASE}/gestione/getGestioneComunale.csv.php?pg=nazione&aa=${YEAR}" "$OUTDIR" "ru_gestione_comunale.csv"

  FILES=$(find "$OUTDIR" -name "*.csv" -size +100c | wc -l)
  echo "  Downloaded: $FILES files"
done

echo ""
echo "=== DONE ==="
echo "Years: $START-$END"
for d in "$SCRIPT_DIR"/raw-*/; do
  year=$(basename "$d")
  count=$(find "$d" -name "*.csv" -size +100c | wc -l)
  echo "  $year: $count files"
done
