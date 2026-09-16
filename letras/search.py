import re
import time
from typing import Optional
from urllib.parse import urlparse

from .config import CacheBusca, Config
from .keywords import normalizar
from .universities import Universidade

DOMINIOS_IGNORADOS = {
    "passeidireto.com", "scribd.com", "studocu.com", "slideshare.net",
    "docsity.com", "yumpu.com", "academia.edu", "researchgate.net",
    "pt.wikipedia.org", "wikipedia.org", "youtube.com", "facebook.com",
    "instagram.com", "linkedin.com", "twitter.com", "x.com", "tiktok.com",
    "medium.com", "thinkific.com", "hotmart.com", "udemy.com", "coursera.org",
    "mercadoshops.com.br", "amazon.com.br",
}

REPOSITORIOS = (
    "repositorio", "repositório", "bdm.", "pantheon", "tede", "bdtd",
    "biblioteca", "teses", "dissertacoes", "monografias", "/tcc", "tcc_",
)

SINAIS_PPC = (
    "projeto-pedagogico", "projeto_pedagogico", "projetopedagogico",
    "projeto pedagogico", "ppc", "matriz", "curricul", "ementa", "grade",
    "licenciatura", "graduacao", "graduação", "curso",
)

STOPWORDS_NOME = {
    "universidade", "federal", "estadual", "do", "de", "da", "dos", "das",
    "e", "julio", "mesquita", "filho", "darcy", "ribeiro", "jorge", "amaury",
}

try:
    from ddgs import DDGS
except ImportError:  # pragma: no cover
    DDGS = None


class _Buscador:
    def __init__(self, cfg: Config, cache: CacheBusca):
        self.cfg = cfg
        self.cache = cache

    def buscar(self, query: str, max_resultados: Optional[int] = None) -> list[dict]:
        if DDGS is None:
            raise RuntimeError("Pacote 'ddgs' não instalado. Rode: pip install ddgs")
        limite = max_resultados or self.cfg.max_resultados_busca
        chave = f"{query}|{limite}"
        if self.cfg.usar_cache_busca:
            cacheado = self.cache.get(chave)
            if cacheado is not None:
                return cacheado
        resultados: list[dict] = []
        for tentativa in range(3):
            try:
                with DDGS() as ddgs:
                    brutos = list(
                        ddgs.text(query, region=self.cfg.search_region, max_results=limite)
                    )
                resultados = [
                    {
                        "titulo": r.get("title") or "",
                        "url": r.get("href") or r.get("url") or "",
                        "trecho": r.get("body") or "",
                    }
                    for r in brutos
                ]
                break
            except Exception:
                time.sleep(2 * (tentativa + 1))
        if self.cfg.usar_cache_busca:
            self.cache.set(chave, resultados)
        time.sleep(self.cfg.search_delay)
        return resultados


def _host(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except ValueError:
        return ""


def _host_ignorado(host: str) -> bool:
    return any(host == d or host.endswith("." + d) for d in DOMINIOS_IGNORADOS)


def resolver_dominio(
    uni: Universidade, cfg: Config, cache: CacheBusca, buscador: Optional[_Buscador] = None
) -> Optional[str]:
    buscador = buscador or _Buscador(cfg, cache)
    consulta = f"{uni.sigla} {uni.nome} site oficial"
    resultados = buscador.buscar(consulta, max_resultados=8)
    sigla = normalizar(uni.sigla)
    tokens = [
        t for t in re.split(r"\W+", normalizar(uni.nome))
        if len(t) > 3 and t not in STOPWORDS_NOME
    ]
    melhor: tuple[int, Optional[str]] = (0, None)
    for r in resultados:
        host = _host(r["url"])
        if not host or _host_ignorado(host):
            continue
        score = 0
        if host.endswith(".br"):
            score += 2
        if ".edu" in host or host.endswith(".br") and "edu" in host:
            score += 1
        if sigla and sigla in host.replace(".", ""):
            score += 4
        score += sum(1 for t in tokens if t in host)
        if score > melhor[0]:
            melhor = (score, host)
    return dominio_base(melhor[1]) if melhor[0] >= 3 else None


def _score_url(url: str, dominio: Optional[str]) -> int:
    low = url.lower()
    score = 0
    score += 5 if low.endswith(".pdf") else 0
    score += 3 if re.search(r"\.(docx?|odt)$", low) else 0
    for termo in (
        "letras", "ppc", "projeto-pedagogico", "projeto_pedagogico", "projetopedagogico",
        "matriz", "curricul", "ementa", "licenciatura", "graduacao", "ppc-letras",
    ):
        if termo in low:
            score += 2
    if dominio and _host(url).endswith(dominio):
        score += 1
    return score


def _relevante_letras(texto: str) -> bool:
    t = normalizar(texto)
    return any(p in t for p in ("letras", "lingu", "literatur", "filolog", "idioma"))


def _documento_relevante(url: str, titulo: str) -> bool:
    t = normalizar(f"{url} {titulo}")
    if any(r in t for r in REPOSITORIOS):
        return False
    if not _relevante_letras(t):
        return False
    return any(s in t for s in SINAIS_PPC)


SLD_BR = {"com", "edu", "gov", "org", "net", "mil", "art", "blog", "eco", "emp", "tur"}


def dominio_base(dominio: Optional[str]) -> Optional[str]:
    if not dominio:
        return dominio
    labels = dominio.split(".")
    if labels[-1] == "br":
        if len(labels) >= 3 and labels[-2] in SLD_BR:
            return ".".join(labels[-3:])
        if len(labels) >= 2:
            return ".".join(labels[-2:])
    if len(labels) >= 2:
        return ".".join(labels[-2:])
    return dominio


def _dominio_aceito(host: str, dominio: Optional[str]) -> bool:
    if not host or not dominio:
        return False
    if host == dominio or host.endswith("." + dominio):
        return True
    labels = dominio.split(".")
    for i in range(1, len(labels) - 1):
        sufixo = ".".join(labels[i:])
        if len(sufixo.split(".")) >= 2 and host.endswith("." + sufixo):
            return True
    return False


def _do_dominio(url: str, dominio: Optional[str]) -> bool:
    if not dominio:
        return True
    return _dominio_aceito(_host(url), dominio)


def _menciona_universidade(texto: str, uni: Universidade) -> bool:
    t = normalizar(texto)
    if uni.sigla and normalizar(uni.sigla) in t:
        return True
    tokens = [
        tok for tok in re.split(r"\W+", normalizar(uni.nome))
        if len(tok) > 4 and tok not in STOPWORDS_NOME
    ]
    return sum(1 for tok in tokens if tok in t) >= 2


def encontrar_documentos(
    uni: Universidade,
    cfg: Config,
    cache: CacheBusca,
    dominio: Optional[str] = None,
    buscador: Optional[_Buscador] = None,
) -> list[dict]:
    buscador = buscador or _Buscador(cfg, cache)
    consultas = [
        f'{uni.nome} Letras projeto pedagogico pdf',
        f'{uni.nome} curso de Letras matriz curricular ementas',
        f'{uni.sigla} Letras PPC projeto pedagogico licenciatura',
    ]
    if dominio:
        consultas += [
            f"site:{dominio} Letras projeto pedagogico",
            f"site:{dominio} Letras matriz curricular",
            f"site:{dominio} Letras ementas disciplinas",
        ]
    candidatos: dict[str, dict] = {}
    for consulta in consultas:
        for r in buscador.buscar(consulta):
            url = r["url"]
            if not url.startswith("http"):
                continue
            host = _host(url)
            if not host or _host_ignorado(host):
                continue
            titulo = r.get("titulo", "") or ""
            if not _documento_relevante(url, titulo):
                continue
            if not _do_dominio(url, dominio) and not _menciona_universidade(
                f"{url} {titulo}", uni
            ):
                continue
            score = _score_url(url, dominio)
            if score < 2:
                continue
            if url not in candidatos or score > candidatos[url]["score"]:
                candidatos[url] = {**r, "score": score}
    ordenados = sorted(candidatos.values(), key=lambda c: c["score"], reverse=True)
    return ordenados[: cfg.max_documentos_por_universidade]
