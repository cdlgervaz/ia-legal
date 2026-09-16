import argparse
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from letras.collect import coletar_universidade, coletar_urls
from letras.config import CacheBusca, get_config
from letras.search import _Buscador
from letras.store import Store
from letras.universities import carregar_universidades


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Coleta disciplinas sobre ensino de tecnologias em cursos de Letras "
                    "de universidades públicas."
    )
    parser.add_argument("--sigla", nargs="*", default=None,
                        help="Siglas de universidades específicas (ex.: --sigla UFRJ UnB)")
    parser.add_argument("--uf", default=None, help="Filtrar por UF (ex.: RJ)")
    parser.add_argument("--categoria", choices=["federal", "estadual"], default=None)
    parser.add_argument("--limite", type=int, default=None,
                        help="Máximo de universidades a processar")
    parser.add_argument("--max-docs", type=int, default=None,
                        help="Máximo de documentos por universidade")
    parser.add_argument("--forcar", action="store_true",
                        help="Reprocessa documentos já coletados")
    parser.add_argument("--sem-cache", action="store_true",
                        help="Ignora o cache de buscas")
    parser.add_argument("--so-listar", action="store_true",
                        help="Apenas lista universidades e candidatos, sem baixar")
    parser.add_argument("--url", nargs="*", default=[],
                        help="PPCs para baixar manualmente (requer --sigla com uma sigla)")
    parser.add_argument("--seed", nargs="*", default=[],
                        help="Páginas-índice de cursos para crawlear (requer --sigla)")
    parser.add_argument("--so-urls", action="store_true",
                        help="Processa apenas as URLs/seeds informadas")
    parser.add_argument("--reparse", action="store_true",
                        help="Re-extrai disciplinas dos arquivos já baixados (sem baixar de novo)")
    parser.add_argument("--workers", type=int, default=None,
                        help="Número de universidades processadas em paralelo")
    parser.add_argument("--max-total", type=int, default=None,
                        help="Máximo de documentos baixados por universidade (inclui anexos)")
    args = parser.parse_args()

    cfg = get_config()
    if args.max_docs:
        cfg.max_documentos_por_universidade = args.max_docs
    if args.max_total:
        cfg.max_documentos_total = args.max_total
    if args.workers:
        cfg.workers = max(1, args.workers)
    if args.sem_cache:
        cfg.usar_cache_busca = False

    cache = CacheBusca(cfg.cache_path)
    store = Store(cfg.db_path)
    buscador = _Buscador(cfg, cache)

    if args.reparse:
        from letras.collect import reprocessar_arquivos

        r = reprocessar_arquivos(cfg, store)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0

    if args.url or args.seed:
        if not args.sigla or len(args.sigla) != 1:
            print("Use --url/--seed junto com --sigla SIGLA (uma única sigla).",
                  file=sys.stderr)
            return 1
        alvo = carregar_universidades(cfg, siglas=args.sigla)[0]
        if args.seed:
            from letras.collect import coletar_seeds

            print(f"[seeds] {alvo.sigla} - {len(args.seed)} página(s)", flush=True)
            coletar_seeds(alvo, args.seed, cfg, store, forcar=args.forcar)
        if args.url:
            print(f"[manual] {alvo.sigla} - {len(args.url)} URL(s)", flush=True)
            coletar_urls(alvo, args.url, cfg, store, forcar=args.forcar)
        if args.so_urls:
            print(json.dumps(store.estatisticas(), ensure_ascii=False, indent=2))
            return 0

    universidades = carregar_universidades(
        cfg, siglas=args.sigla, uf=args.uf, categoria=args.categoria
    )
    if args.limite:
        universidades = universidades[: args.limite]
    if not universidades:
        print("Nenhuma universidade corresponde aos filtros.", file=sys.stderr)
        return 1

    if args.so_listar:
        from letras.search import encontrar_documentos, resolver_dominio

        for u in universidades:
            dominio = resolver_dominio(u, cfg, cache, buscador)
            docs = encontrar_documentos(u, cfg, cache, dominio, buscador)
            print(f"\n{u.sigla} ({u.uf}) - dominio: {dominio}")
            for d in docs:
                print(f"  [{d['score']}] {d['url']}")
        return 0

    lock = threading.Lock()
    total = len(universidades)
    resumo = []

    def processar(indice: int, u) -> dict | None:
        with lock:
            print(f"[{indice}/{total}] {u.sigla} - {u.nome}", flush=True)
        try:
            r = coletar_universidade(u, cfg, store, cache, buscador, forcar=args.forcar)
        except Exception as exc:  # noqa: BLE001
            with lock:
                print(f"  [{u.sigla}] erro: {exc}", flush=True)
            store.log(u.sigla, 0, 0, f"erro: {exc}")
            return None
        with lock:
            print(
                f"  [{u.sigla}] dominio={r['dominio']} docs={r['documentos_novos']} "
                f"disciplinas={r['disciplinas']}",
                flush=True,
            )
        return r

    if cfg.workers > 1:
        with ThreadPoolExecutor(max_workers=cfg.workers) as executor:
            futuros = [executor.submit(processar, i, u)
                       for i, u in enumerate(universidades, start=1)]
            for futuro in as_completed(futuros):
                r = futuro.result()
                if r:
                    resumo.append(r)
    else:
        for i, u in enumerate(universidades, start=1):
            r = processar(i, u)
            if r:
                resumo.append(r)

    est = store.estatisticas()
    print("\n=== Resumo ===")
    print(json.dumps(est, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
