#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "Criando ambiente virtual..."
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
  echo "Arquivo .env criado a partir de .env.example. Configure LLM_API_KEY para respostas com IA."
fi

exec .venv/bin/python -m uvicorn app.main:app --host "${HOST:-127.0.0.1}" --port "${PORT:-8000}" --reload
