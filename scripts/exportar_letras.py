import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from letras.config import LETRAS_DIR, get_config
from letras.store import Store

CAMPOS = [
    "universidade", "universidade_nome", "uf", "categoria", "nome", "palavras_chave",
    "score", "pagina", "documento_titulo", "url",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Exporta as disciplinas coletadas.")
    parser.add_argument("--universidade", default=None, help="Filtrar por sigla")
    parser.add_argument("--texto", default=None, help="Filtrar por termo")
    parser.add_argument("--saida", default=None, help="Arquivo de saída (csv ou json)")
    parser.add_argument("--formato", choices=["csv", "json"], default=None)
    parser.add_argument("--min-score", type=int, default=0, help="Filtrar por score mínimo")
    parser.add_argument("--sem-dedup", action="store_true",
                        help="Não remover duplicatas da mesma disciplina na universidade")
    args = parser.parse_args()

    cfg = get_config()
    store = Store(cfg.db_path)
    registros = store.listar_disciplinas(
        universidade=args.universidade, texto=args.texto, limit=100000
    )
    if args.min_score:
        registros = [r for r in registros if (r.get("score") or 0) >= args.min_score]
    if not args.sem_dedup:
        melhores: dict[tuple, dict] = {}
        for r in registros:
            chave = (r["universidade"], (r["nome"] or "").strip().lower())
            atual = melhores.get(chave)
            if atual is None or (r.get("score") or 0) > (atual.get("score") or 0):
                melhores[chave] = r
        registros = sorted(
            melhores.values(), key=lambda r: (r["universidade"], -(r.get("score") or 0))
        )

    formato = args.formato or ("json" if (args.saida or "").endswith(".json") else "csv")
    if args.saida:
        saida = Path(args.saida)
    else:
        saida = LETRAS_DIR / f"disciplinas.{formato}"
    saida.parent.mkdir(parents=True, exist_ok=True)

    if formato == "json":
        saida.write_text(
            json.dumps(registros, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    else:
        with saida.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CAMPOS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(registros)

    print(f"{len(registros)} disciplinas exportadas para {saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
