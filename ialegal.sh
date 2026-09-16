#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"
PORT="${PORT:-8000}"
USER_UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
SERVER_UNIT="ialegal-server"
TUNNEL_UNIT="ialegal-tunnel"
RUN_DIR="$PROJECT_DIR/.run"
LOG_DIR="$RUN_DIR/logs"
LINK_FILE="$RUN_DIR/link.txt"

mkdir -p "$LOG_DIR" "$USER_UNIT_DIR"

escrever_unidades() {
  cat > "$USER_UNIT_DIR/$SERVER_UNIT.service" <<EOF
[Unit]
Description=IA Legal - servidor local
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$PROJECT_DIR
Environment=PORT=$PORT
ExecStart=$PROJECT_DIR/.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
Restart=always
RestartSec=5
StandardOutput=append:$LOG_DIR/server.log
StandardError=append:$LOG_DIR/server.log

[Install]
WantedBy=default.target
EOF

  cat > "$USER_UNIT_DIR/$TUNNEL_UNIT.service" <<EOF
[Unit]
Description=IA Legal - link publico (cloudflared)
After=$SERVER_UNIT.service network-online.target
Wants=$SERVER_UNIT.service

[Service]
Type=simple
WorkingDirectory=$PROJECT_DIR
Environment=PORT=$PORT
ExecStart=$PROJECT_DIR/scripts/tunnel.sh
Restart=always
RestartSec=5
StandardOutput=append:$LOG_DIR/tunnel.service.log
StandardError=append:$LOG_DIR/tunnel.service.log

[Install]
WantedBy=default.target
EOF
}

preparar_ambiente() {
  if [ ! -x ".venv/bin/python" ]; then
    echo "[setup] Criando ambiente virtual e instalando dependencias..."
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
}

mostrar_link() {
  for _ in $(seq 1 40); do
    if [ -s "$LINK_FILE" ]; then
      cat "$LINK_FILE"; echo
      return 0
    fi
    sleep 1
  done
  echo "Link ainda nao disponivel. Veja: ./ialegal.sh logs" >&2
  return 1
}

case "${1:-}" in
  enable|instalar)
    preparar_ambiente
    escrever_unidades
    systemctl --user daemon-reload
    systemctl --user enable --now "$SERVER_UNIT" "$TUNNEL_UNIT"
    echo "[ok] Servico ativado e rodando em segundo plano."
    echo "     Acesso local: http://127.0.0.1:$PORT"
    echo "     Link publico:"
    mostrar_link
    ;;
  disable|remover)
    systemctl --user disable --now "$TUNNEL_UNIT" "$SERVER_UNIT" 2>/dev/null || true
    rm -f "$USER_UNIT_DIR/$SERVER_UNIT.service" "$USER_UNIT_DIR/$TUNNEL_UNIT.service"
    systemctl --user daemon-reload
    echo "[ok] Servico desativado e removido."
    ;;
  start)
    systemctl --user start "$SERVER_UNIT" "$TUNNEL_UNIT"
    echo "[ok] Iniciado."; mostrar_link
    ;;
  stop)
    systemctl --user stop "$TUNNEL_UNIT" "$SERVER_UNIT"
    echo "[ok] Parado."
    ;;
  restart)
    systemctl --user restart "$SERVER_UNIT"
    echo "[ok] Servidor reiniciado (link do tunel mantido)."; mostrar_link
    ;;
  status)
    systemctl --user --no-pager status "$SERVER_UNIT" "$TUNNEL_UNIT" 2>&1 | grep -E "Loaded|Active|Main PID|Description" || true
    echo
    echo -n "Link publico: "; [ -s "$LINK_FILE" ] && cat "$LINK_FILE" || echo "(nao disponivel)"
    echo
    echo -n "Teste local:  "; curl -sf "http://127.0.0.1:$PORT/api/health" >/dev/null 2>&1 && echo "servidor respondendo" || echo "servidor NAO responde"
    ;;
  link|url)
    mostrar_link
    ;;
  logs)
    journalctl --user -u "$SERVER_UNIT" -u "$TUNNEL_UNIT" -n 80 --no-pager
    ;;
  *)
    echo "Uso: ./ialegal.sh <comando>"
    echo
    echo "  enable    Instala e liga o servico (inicia no boot e reinicia se cair)"
    echo "  disable   Desliga e remove o servico"
    echo "  start     Liga o servico agora"
    echo "  stop      Desliga o servico"
    echo "  restart   Reinicia o servico"
    echo "  status    Mostra se esta rodando e o link atual"
    echo "  link      Mostra o link publico atual"
    echo "  logs      Mostra os ultimos registros"
    ;;
esac
