import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ingest import run_sync
from app.models import SyncRequest


def main() -> int:
    parser = argparse.ArgumentParser(description="Sincroniza legislação de tecnologia.")
    parser.add_argument("--anos", nargs="*", type=int, default=[], help="Anos a importar")
    parser.add_argument("--tipos", nargs="*", default=["PL", "PEC", "PLP", "MPV"])
    parser.add_argument("--max", type=int, default=60, help="Máximo de itens por ano")
    parser.add_argument("--sem-camara", action="store_true")
    parser.add_argument("--sem-senado", action="store_true")
    parser.add_argument("--sem-tramitacoes", action="store_true")
    parser.add_argument("--sem-comunicacoes", action="store_true")
    args = parser.parse_args()

    req = SyncRequest(
        camara=not args.sem_camara,
        senado=not args.sem_senado,
        anos=args.anos,
        tipos=args.tipos,
        max_itens_por_ano=args.max,
        buscar_tramitacoes=not args.sem_tramitacoes,
        incluir_comunicacoes=not args.sem_comunicacoes,
    )
    resposta = run_sync(req)
    print(json.dumps(resposta.model_dump(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
