#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

GH=".tools/gh"
REPO_NAME="${1:-ia-legal}"

if [ ! -x "$GH" ]; then
  echo "[erro] GitHub CLI não encontrado em $GH" >&2
  exit 1
fi

if ! "$GH" auth status >/dev/null 2>&1; then
  echo "Você ainda não entrou na sua conta do GitHub."
  echo "Rode primeiro:"
  echo
  echo "    .tools/gh auth login"
  echo
  echo "Escolha: GitHub.com > HTTPS > Login with a web browser."
  exit 1
fi

login="$("$GH" api user -q .login)"
name="$("$GH" api user -q '.name // .login')"
email="$("$GH" api user -q '.email // empty')"
[ -z "$email" ] && email="${login}@users.noreply.github.com"

git config user.name "$name"
git config user.email "$email"

if [ ! -d .git ]; then
  git init -b main >/dev/null
fi

if [ -f "data/chroma/chroma.sqlite3" ]; then
  echo "[info] Empacotando o indice em partes (abaixo de 100 MB)..."
  ./scripts/empacotar_indice.sh
elif [ ! -d "data/chroma_parts" ]; then
  echo "[aviso] Indice e partes nao encontrados; seguindo sem empacotar."
fi

git add -A
if ! git diff --cached --quiet; then
  git commit -m "IAgora, profe?: acervo de politicas educacionais" >/dev/null
fi

if git remote get-url origin >/dev/null 2>&1; then
  git push -u origin main
else
  "$GH" repo create "$REPO_NAME" --private --source=. --remote=origin --push
fi

echo
echo "=============================================================="
echo " Pronto! Repositório criado/enviado:"
echo "   https://github.com/$login/$REPO_NAME"
echo "=============================================================="
echo
echo "Próximo passo: publicar no Render (veja a seção no README)."
