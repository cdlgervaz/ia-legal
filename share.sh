#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

PORT="${PORT:-8000}"
HOST="${HOST:-0.0.0.0}"
NO_TUNNEL=0

for arg in "$@"; do
  case "$arg" in
    --no-tunnel) NO_TUNNEL=1 ;;
    --port=*) PORT="${arg#*=}" ;;
    --host=*) HOST="${arg#*=}" ;;
    -h|--help)
      echo "Uso: ./share.sh [--no-tunnel] [--port=8000] [--host=0.0.0.0]"
      echo "  --no-tunnel   apenas rede local, sem link público"
      exit 0
      ;;
    *)
      echo "Argumento desconhecido: $arg" >&2
      exit 1
      ;;
  esac
done

TOOLS_DIR=".tools"
LOG_DIR="${TMPDIR:-/tmp}/ialegal-share"
mkdir -p "$TOOLS_DIR" "$LOG_DIR"

if [ ! -d ".venv" ]; then
  echo "[setup] Criando ambiente virtual e instalando dependências..."
  python3 -m venv --without-pip .venv
  if [ -f /tmp/opencode/get-pip.py ]; then
    cp /tmp/opencode/get-pip.py .venv/_get-pip.py
  else
    curl -sSL https://bootstrap.pypa.io/get-pip.py -o .venv/_get-pip.py
  fi
  .venv/bin/python .venv/_get-pip.py --quiet
  rm -f .venv/_get-pip.py
  .venv/bin/python -m pip install -r requirements.txt
fi

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "[setup] Arquivo .env criado. Configure LLM_API_KEY para respostas com IA."
fi

SERVER_LOG="$LOG_DIR/server.log"
.venv/bin/python -m uvicorn app.main:app --host "$HOST" --port "$PORT" > "$SERVER_LOG" 2>&1 &
SERVER_PID=$!

cleanup() {
  echo
  echo "[info] Encerrando servidor e túnel..."
  if [ -n "${TUNNEL_PID:-}" ]; then kill "$TUNNEL_PID" 2>/dev/null || true; fi
  if [ -n "${SERVER_PID:-}" ]; then kill "$SERVER_PID" 2>/dev/null || true; fi
  wait 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 0' INT TERM

for _ in $(seq 1 40); do
  if curl -sf "http://127.0.0.1:$PORT/api/health" >/dev/null 2>&1; then break; fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "[erro] O servidor não iniciou. Veja $SERVER_LOG" >&2
    exit 1
  fi
  sleep 1
done

echo "[ok] Servidor em http://$HOST:$PORT  (log: $SERVER_LOG)"

if [ "$NO_TUNNEL" = "1" ]; then
  LAN_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
  if [ -n "${LAN_IP:-}" ]; then
    echo "[ok] Na rede local, acesse: http://$LAN_IP:$PORT"
  fi
  echo "[info] Ctrl+C para encerrar."
  wait "$SERVER_PID"
  exit 0
fi

CLOUDFLARED="$TOOLS_DIR/cloudflared"
if [ ! -x "$CLOUDFLARED" ]; then
  echo "[setup] Baixando cloudflared..."
  ARCH="$(uname -m)"
  case "$ARCH" in
    x86_64|amd64) BIN="cloudflared-linux-amd64" ;;
    aarch64|arm64) BIN="cloudflared-linux-arm64" ;;
    *) echo "[erro] Arquitetura não suportada: $ARCH" >&2; exit 1 ;;
  esac
  curl -L "https://github.com/cloudflare/cloudflared/releases/latest/download/$BIN" -o "$CLOUDFLARED"
  chmod +x "$CLOUDFLARED"
fi

TUNNEL_LOG="$LOG_DIR/tunnel.log"
"$CLOUDFLARED" tunnel --no-autoupdate --url "http://localhost:$PORT" > "$TUNNEL_LOG" 2>&1 &
TUNNEL_PID=$!

URL=""
for _ in $(seq 1 60); do
  URL="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$TUNNEL_LOG" | head -1 || true)"
  if [ -n "$URL" ]; then break; fi
  if ! kill -0 "$TUNNEL_PID" 2>/dev/null; then
    echo "[erro] O cloudflared encerrou. Veja $TUNNEL_LOG" >&2
    exit 1
  fi
  sleep 1
done

echo
if [ -n "$URL" ]; then
  echo "=============================================================="
  echo " Link público para testar (envie para a pessoa):"
  echo "   $URL"
  echo "=============================================================="
  echo " O link fica ativo enquanto este terminal estiver aberto."
  echo " Ctrl+C para encerrar o servidor e o túnel."
else
  echo "[erro] Não foi possível obter o link público. Veja $TUNNEL_LOG" >&2
  exit 1
fi

wait
