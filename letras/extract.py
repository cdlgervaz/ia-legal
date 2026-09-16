import io
import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .fetch import Resposta

logging.getLogger("pypdf").setLevel(logging.ERROR)

TAGS_IGNORADAS = ["script", "style", "noscript", "svg", "nav", "footer", "header", "form"]


def _texto_html(html: bytes) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(TAGS_IGNORADAS):
        tag.decompose()
    for br in soup.find_all(["br", "p", "li", "tr", "div", "h1", "h2", "h3", "h4"]):
        br.append("\n")
    texto = soup.get_text("\n", strip=True)
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto


def _texto_pdf(conteudo: bytes) -> list[tuple[int, str]]:
    from pypdf import PdfReader

    paginas: list[tuple[int, str]] = []
    try:
        leitor = PdfReader(io.BytesIO(conteudo))
        total = len(leitor.pages)
    except Exception:
        return paginas
    for i in range(total):
        try:
            texto = leitor.pages[i].extract_text() or ""
        except Exception:
            texto = ""
        if texto.strip():
            paginas.append((i + 1, texto))
    return paginas


def _parece_html(conteudo: bytes) -> bool:
    inicio = conteudo[:512].lstrip().lower()
    return inicio.startswith(b"<!doctype") or inicio.startswith(b"<html") or b"<html" in inicio


def extrair_paginas(resp: Resposta) -> list[tuple[int, str]]:
    try:
        eh_pdf = resp.conteudo[:5] == b"%PDF-"
        if resp.tipo == "pdf" or eh_pdf:
            paginas = _texto_pdf(resp.conteudo)
            if paginas:
                return paginas
            if eh_pdf:
                return []
        if resp.tipo == "html" or _parece_html(resp.conteudo):
            return [(1, _texto_html(resp.conteudo))]
        return [(1, resp.conteudo.decode("utf-8", errors="ignore"))]
    except Exception:
        return []


RE_LETRAS = re.compile(r"letras|lingu[íi]stica|literatur|filolog|idioma", re.IGNORECASE)
RE_CURSO = re.compile(
    r"ppc|projeto|matriz|curricul|ementa|curso|gradua|licenciatura|grade|"
    r"pedagog|tecnolog",
    re.IGNORECASE,
)


def links_relevantes(html: bytes, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "mailto:", "javascript:")):
            continue
        absoluto = urljoin(base_url, href)
        low = absoluto.lower()
        texto = a.get_text(" ", strip=True) or ""
        alvo = f"{low} {texto.lower()}"
        if not RE_LETRAS.search(alvo):
            continue
        if low.endswith(".pdf") or RE_CURSO.search(alvo) or "letras" in texto.lower():
            urls.append(absoluto)
    vistos: set[str] = set()
    unicos: list[str] = []
    for u in urls:
        if u not in vistos:
            vistos.add(u)
            unicos.append(u)
    return unicos


def links_pdf(html: bytes, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "mailto:", "javascript:")):
            continue
        absoluto = urljoin(base_url, href)
        low = absoluto.lower()
        texto = (a.get_text(" ", strip=True) or "").lower()
        if low.endswith(".pdf") and ("letras" in low or "ppc" in low or "projeto" in low
                                     or "matriz" in low or "curricul" in low
                                     or "letras" in texto or "ppc" in texto
                                     or "projeto" in texto or "matriz" in texto):
            urls.append(absoluto)
    vistos: set[str] = set()
    unicos: list[str] = []
    for u in urls:
        if u not in vistos:
            vistos.add(u)
            unicos.append(u)
    return unicos
