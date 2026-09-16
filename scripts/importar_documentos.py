import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.catalog import CATALOGO, get as get_catalogo
from app.config import get_settings
from app.db import Database
from app.documentos import importar, importar_arquivo_local
from app.models import ImportRequest
from app.temas import TEMAS


def listar() -> int:
    db = Database(get_settings().db_path)
    importados = {d["id"]: d for d in db.list_documentos()}
    print(f"{'ID':24s} {'TIPO':16s} {'ANO':5s} {'SITUAÇÃO':18s} TÍTULO")
    for item in CATALOGO:
        estado = importados.get(item.id)
        if estado and estado["chunks"]:
            situacao = f"{estado['chunks']} trechos"
        elif item.importavel:
            situacao = "não importado"
        else:
            situacao = "importar manual"
        print(
            f"{item.id:24s} {item.tipo:16s} {str(item.ano or ''):5s} {situacao:18s} {item.titulo}"
        )
    extras = [d for d in importados.values() if get_catalogo(d["id"]) is None]
    if extras:
        print("\nDocumentos importados localmente:")
        for doc in extras:
            print(f"  {doc['id']:24s} {doc['chunks']} trechos - {doc['titulo']}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Importa o acervo de Políticas Educacionais (leis, BNCC, BNC, pareceres)."
    )
    parser.add_argument("--listar", action="store_true", help="Lista o catálogo e o status")
    parser.add_argument("--ids", nargs="*", default=[], help="IDs do catálogo a importar")
    parser.add_argument("--todos", action="store_true", help="Importa todo o catálogo")
    parser.add_argument("--forcar", action="store_true", help="Reimporta mesmo se já indexado")
    parser.add_argument("--sem-baixar", action="store_true", help="Usa apenas arquivos locais")
    parser.add_argument("--arquivo", type=Path, help="Importa um PDF/HTML local")
    parser.add_argument("--id", dest="documento_id", help="ID do documento local")
    parser.add_argument("--titulo", help="Título do documento local")
    parser.add_argument("--tipo", default="Documento", help="Tipo do documento local")
    parser.add_argument("--ano", type=int, help="Ano do documento local")
    parser.add_argument("--orgao", default="", help="Órgão do documento local")
    parser.add_argument(
        "--temas",
        nargs="*",
        default=[],
        choices=sorted(TEMAS.keys()),
        help="Temas do documento local",
    )
    args = parser.parse_args()

    if args.listar:
        return listar()

    if args.arquivo:
        if not args.documento_id or not args.titulo:
            parser.error("--arquivo exige --id e --titulo")
        resultado = importar_arquivo_local(
            args.arquivo,
            documento_id=args.documento_id,
            titulo=args.titulo,
            tipo=args.tipo,
            ano=args.ano,
            orgao=args.orgao,
            temas=args.temas,
        )
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        return 0

    if not args.ids and not args.todos:
        parser.error("Informe --listar, --ids, --todos ou --arquivo.")

    ids = args.ids
    if args.todos:
        ids = [item.id for item in CATALOGO if item.importavel]
    if not ids:
        parser.error("Nenhum documento importável encontrado.")

    resposta = importar(
        ImportRequest(ids=ids, forcar=args.forcar, baixar=not args.sem_baixar)
    )
    print(json.dumps(resposta, ensure_ascii=False, indent=2))
    return 0 if not resposta.get("erros") else 1


if __name__ == "__main__":
    raise SystemExit(main())
