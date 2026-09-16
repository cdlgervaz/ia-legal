import hashlib
import re
import time
from pathlib import Path
from typing import Optional

from .config import CacheBusca, Config
from .extract import _parece_html, extrair_paginas, links_pdf, links_relevantes
from .fetch import baixar
from .parse import encontrar_disciplinas
from .search import (
    _Buscador,
    _do_dominio,
    _host,
    _relevante_letras,
    dominio_base,
    encontrar_documentos,
    resolver_dominio,
)
from .store import Store
from .universities import Universidade


def _extrair_disciplinas_doc(doc: dict) -> Optional[tuple[int, str, list[dict]]]:
    from .fetch import Resposta

    caminho = Path(doc["caminho"])
    if not caminho.exists():
        return None
    resp = Resposta(
        url=doc["url"], url_final=doc["url"], status=200,
        content_type="application/pdf" if doc["tipo"] == "pdf" else "text/html",
        conteudo=caminho.read_bytes(),
    )
    paginas = extrair_paginas(resp)
    return (doc["id"], doc["universidade"], encontrar_disciplinas(paginas))


def reprocessar_arquivos(cfg: Config, store: Store) -> dict:
    """Re-extrai disciplinas dos arquivos já baixados, sem nova busca/download."""
    from concurrent.futures import ThreadPoolExecutor

    with store.connect() as conn:
        docs = [dict(r) for r in conn.execute(
            "SELECT * FROM documentos WHERE status = 'ok' AND caminho IS NOT NULL"
        ).fetchall()]
    resultados: list[tuple[int, str, list[dict]]] = []
    workers = max(1, cfg.workers)
    if workers > 1:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            for r in executor.map(_extrair_disciplinas_doc, docs):
                if r:
                    resultados.append(r)
    else:
        for doc in docs:
            r = _extrair_disciplinas_doc(doc)
            if r:
                resultados.append(r)

    total = 0
    for doc_id, universidade, disciplinas in resultados:
        store.limpar_disciplinas(doc_id)
        total += store.inserir_disciplinas(doc_id, universidade, disciplinas)
    return {"documentos": len(resultados), "disciplinas": total}


def _slug(texto: str) -> str:
    texto = re.sub(r"[^A-Za-z0-9]+", "-", texto).strip("-")
    return texto[:80] or "doc"


def _caminho(cfg: Config, sigla: str, url: str, extensao: str) -> Path:
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
    pasta = cfg.docs_dir / _slug(sigla)
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta / f"{digest}.{extensao}"


def _processar_url(
    url: str,
    titulo: str,
    universidade: Universidade,
    cfg: Config,
    store: Store,
    forcar: bool,
    profundidade: int = 0,
    vistos: Optional[set[str]] = None,
    dominio: Optional[str] = None,
    orcamento: Optional[list[int]] = None,
    exigir_letras: bool = False,
) -> tuple[int, int]:
    """Baixa, extrai e grava um documento. Retorna (documentos, disciplinas)."""
    vistos = vistos if vistos is not None else set()
    if url in vistos:
        return 0, 0
    vistos.add(url)
    if profundidade > 0 and not _do_dominio(url, dominio):
        return 0, 0
    if orcamento is not None and orcamento[0] <= 0:
        return 0, 0

    existente = store.documento_por_url(url)
    if existente and existente["status"] == "ok" and not forcar:
        return 0, 0

    if orcamento is not None:
        orcamento[0] -= 1
    resp = baixar(url, cfg)
    if resp is None:
        store.inserir_documento(universidade.sigla, url, titulo, "?", None, "erro", 0, 0,
                                "falha no download")
        return 0, 0

    paginas = extrair_paginas(resp)
    chars = sum(len(t) for _, t in paginas)
    tipo = resp.tipo
    extensao = "pdf" if tipo == "pdf" else "html"
    caminho = _caminho(cfg, universidade.sigla, url, extensao)
    try:
        caminho.write_bytes(resp.conteudo)
    except OSError:
        caminho = None  # type: ignore[assignment]

    disc = encontrar_disciplinas(paginas)
    if exigir_letras and disc:
        conteudo = " ".join(t for _, t in paginas)[:20000]
        if not _relevante_letras(f"{url} {titulo} {conteudo}"):
            disc = []
    doc_id = store.inserir_documento(
        universidade.sigla, url, titulo, tipo, str(caminho) if caminho else None,
        "ok" if paginas else "vazio", chars, len(paginas),
    )
    store.limpar_disciplinas(doc_id)
    inseridas = store.inserir_disciplinas(doc_id, universidade.sigla, disc)

    documentos = 1
    if tipo == "html" and profundidade == 0:
        for link in links_pdf(resp.conteudo, resp.url_final)[:5]:
            d, i = _processar_url(
                link, f"{titulo} (anexo)", universidade, cfg, store,
                forcar, profundidade + 1, vistos, dominio, orcamento, exigir_letras,
            )
            documentos += d
            inseridas += i
    time.sleep(cfg.http_delay)
    return documentos, inseridas


def coletar_urls(
    universidade: Universidade,
    urls: list[str],
    cfg: Config,
    store: Store,
    forcar: bool = False,
) -> dict:
    dominio = dominio_base(store.get_dominio(universidade.sigla))
    total_docs = 0
    total_disc = 0
    vistos: set[str] = set()
    for url in urls:
        d, i = _processar_url(
            url, url, universidade, cfg, store, forcar, 0, vistos, dominio, None
        )
        total_docs += d
        total_disc += i
        print(f"  [manual] {url} -> {d} documento(s), {i} candidata(s)", flush=True)
    store.log(universidade.sigla, total_docs, total_disc, "urls manuais")
    return {"sigla": universidade.sigla, "documentos_novos": total_docs,
            "disciplinas": total_disc}


def coletar_seeds(
    universidade: Universidade,
    seeds: list[str],
    cfg: Config,
    store: Store,
    forcar: bool = False,
    max_links: int = 12,
) -> dict:
    """Crawleia páginas-índice em busca de cursos de Letras e seus PPCs."""
    dominio = None
    for s in seeds:
        d = dominio_base(_host(s))
        if d:
            dominio = d
            break
    dominio = dominio or dominio_base(store.get_dominio(universidade.sigla))
    store.upsert_universidade(
        universidade.sigla, universidade.nome, universidade.categoria,
        universidade.uf, universidade.regiao, dominio,
    )
    total_docs = 0
    total_disc = 0
    vistos: set[str] = set()
    for seed in seeds:
        resp = baixar(seed, cfg)
        if resp is None:
            store.inserir_documento(universidade.sigla, seed, seed, "?", None,
                                    "erro", 0, 0, "falha no download")
            print(f"  [seed] {seed} -> erro", flush=True)
            continue
        print(f"  [seed] {seed}", flush=True)
        links: list[str] = []
        if resp.tipo == "html" or _parece_html(resp.conteudo):
            links = links_relevantes(resp.conteudo, resp.url_final)
        for link in links[:max_links]:
            if not _do_dominio(link, dominio):
                continue
            if link in vistos:
                continue
            d, i = _processar_url(
                link, link, universidade, cfg, store, forcar, 0, vistos, dominio,
                None, exigir_letras=True,
            )
            total_docs += d
            total_disc += i

    store.log(universidade.sigla, total_docs, total_disc, "seeds")
    return {
        "sigla": universidade.sigla,
        "dominio": dominio,
        "documentos_novos": total_docs,
        "disciplinas": total_disc,
    }


def coletar_universidade(
    universidade: Universidade,
    cfg: Config,
    store: Store,
    cache: CacheBusca,
    buscador: _Buscador,
    forcar: bool = False,
) -> dict:
    dominio = store.get_dominio(universidade.sigla)
    if not dominio or forcar:
        resolvido = resolver_dominio(universidade, cfg, cache, buscador)
        dominio = resolvido or dominio or None
    dominio = dominio_base(dominio)
    store.upsert_universidade(
        universidade.sigla, universidade.nome, universidade.categoria,
        universidade.uf, universidade.regiao, dominio,
    )

    documentos_encontrados = encontrar_documentos(universidade, cfg, cache, dominio, buscador)
    total_docs = 0
    total_disc = 0
    vistos: set[str] = set()
    orcamento = [cfg.max_documentos_total]
    for doc in documentos_encontrados:
        if orcamento[0] <= 0:
            break
        d, i = _processar_url(
            doc["url"], doc.get("titulo") or doc["url"], universidade,
            cfg, store, forcar, profundidade=0, vistos=vistos, dominio=dominio,
            orcamento=orcamento,
        )
        total_docs += d
        total_disc += i

    store.log(universidade.sigla, total_docs, total_disc, f"dominio={dominio}")
    return {
        "sigla": universidade.sigla,
        "dominio": dominio,
        "documentos_encontrados": len(documentos_encontrados),
        "documentos_novos": total_docs,
        "disciplinas": total_disc,
    }
