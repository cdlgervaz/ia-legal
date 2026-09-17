#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

INDICE="data/chroma/chroma.sqlite3"
PARTES="data/chroma_parts"

if [ ! -f "$INDICE" ]; then
  echo "[erro] Índice não encontrado: $INDICE" >&2
  exit 1
fi

rm -f "$PARTES"/chroma.sqlite3.part.*
mkdir -p "$PARTES"
split -b 45m "$INDICE" "$PARTES/chroma.sqlite3.part."

echo "[ok] Índice dividido em partes (cada uma abaixo de 100 MB):"
ls -lh "$PARTES" | tail -n +2 | awk '{print "  " $5, $9}'
