import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .config import Config


@dataclass
class Universidade:
    sigla: str
    nome: str
    categoria: str
    uf: str
    regiao: str
    dominio: Optional[str] = None


def carregar_universidades(
    cfg: Config,
    siglas: Optional[list[str]] = None,
    uf: Optional[str] = None,
    categoria: Optional[str] = None,
) -> list[Universidade]:
    caminho = Path(cfg.universidades_csv)
    if not caminho.exists():
        raise FileNotFoundError(
            f"{caminho} não encontrado. Rode scripts/atualizar_universidades.py"
        )
    siglas_norm = {s.upper() for s in siglas} if siglas else None
    universidades: list[Universidade] = []
    with caminho.open(encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            u = Universidade(
                sigla=(linha.get("sigla") or "").upper(),
                nome=linha.get("nome") or "",
                categoria=(linha.get("categoria") or "").lower(),
                uf=(linha.get("uf") or "").upper(),
                regiao=linha.get("regiao") or "",
            )
            if siglas_norm and u.sigla not in siglas_norm:
                continue
            if uf and u.uf != uf.upper():
                continue
            if categoria and u.categoria != categoria.lower():
                continue
            universidades.append(u)
    if siglas_norm:
        por_sigla = {u.sigla: u for u in universidades}
        universidades = [por_sigla[s] for s in (s.upper() for s in siglas) if s in por_sigla]
    return universidades
