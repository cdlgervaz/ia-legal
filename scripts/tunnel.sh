#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PORT="${PORT:-8000}"
CLOUDFLARED=".tools/cloudflared"
RUN_DIR=".run"
mkdir -p "$RUN_DIR/logs"

if [ ! -x "$CLOUDFLARED" ]; then
  ARCH="$(uname -m)"
  case "$ARCH" in
    x86_64|amd64) BIN="cloudflared-linux-amd64" ;;
    aarch64|arm64) BIN="cloudflared-linux-arm64" ;;
    *) echo "[erro] Arquitetura não suportada: $ARCH" >&2; exit 1 ;;
  esac
  curl -L "https://github.com/cloudflare/cloudflared/releases/latest/download/$BIN" -o "$CLOUDFLARED"
  chmod +x "$CLOUDFLARED"
fi

"$CLOUDFLARED" tunnel --no-autoupdate --url "http://localhost:$PORT" 2>&1 | while IFS= read -r linha; do
  printf '%s\n' "$linha"
  url="$(printf '%s' "$linha" | grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' || true)"
  if [ -n "$url" ]; then
    printf '%s' "$url" > "$RUN_DIR/link.txt"
  fi
done
