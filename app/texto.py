import re
import unicodedata
from functools import lru_cache
from typing import Pattern


def sem_acento(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", texto or "") if not unicodedata.combining(c)
    )


def normalizar(texto: str) -> str:
    texto = sem_acento((texto or "").lower())
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


@lru_cache(maxsize=4096)
def padrao_termo(termo: str) -> Pattern:
    return re.compile(r"\b" + re.escape(normalizar(termo)) + r"\b")


def contem_termo(texto_normalizado: str, termo: str) -> bool:
    return bool(padrao_termo(termo).search(texto_normalizado))


def _normalizado_com_mapa(texto: str) -> tuple[str, list[int]]:
    partes: list[str] = []
    mapa: list[int] = []
    espaco_pendente = True
    for indice, caractere in enumerate(texto):
        limpo = re.sub(r"[^a-z0-9]", "", sem_acento(caractere.lower()))
        if limpo:
            partes.append(limpo)
            mapa.append(indice)
            espaco_pendente = False
        elif not espaco_pendente:
            partes.append(" ")
            mapa.append(indice)
            espaco_pendente = True
    if partes and partes[-1] == " ":
        partes.pop()
        mapa.pop()
    return "".join(partes), mapa


def trecho_ao_redor(texto: str, termo: str, largura: int = 420, margem: int = 120) -> str:
    if not texto:
        return ""
    if len(texto) <= largura:
        return texto.strip()
    alvo = normalizar(termo)
    if not alvo:
        return texto[:largura].strip() + " ..."
    normalizado, mapa = _normalizado_com_mapa(texto)
    posicao = normalizado.find(alvo)
    if posicao < 0:
        return texto[:largura].strip() + " ..."
    inicio = max(0, mapa[posicao] - margem)
    fim_normalizado = posicao + len(alvo) - 1
    fim = min(len(texto), mapa[fim_normalizado] + largura - margem)
    prefixo = "..." if inicio > 0 else ""
    sufixo = " ..." if fim < len(texto) else ""
    return f"{prefixo}{texto[inicio:fim].strip()}{sufixo}"
