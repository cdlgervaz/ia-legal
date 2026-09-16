#!/usr/bin/env python3
"""Busca candidatos a PPC de Letras-Espanhol para universidades sem link.

Uso:
  .venv/bin/python scripts/buscar_ppcs_letras.py [--sigla UFXX ...]

Saída:
  /tmp/opencode/ppc_candidatos.json
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from urllib.parse import urlparse

from ddgs import DDGS

RAIZ = Path(__file__).resolve().parent.parent
FONTES = RAIZ / "site" / "fontes" / "universidades.json"
SAIDA = Path("/tmp/opencode/ppc_candidatos.json")

IGNORADOS = {
    "scribd.com", "passeidireto.com", "studocu.com", "slideshare.net", "docsity.com",
    "yumpu.com", "academia.edu", "researchgate.net", "wikipedia.org", "youtube.com",
    "facebook.com", "instagram.com", "linkedin.com", "medium.com", "dokumen.tips",
    "dokumen.pub", "pt.scribd.com", "cupdf.com", "vdocuments.mx", "fdocumentos.com",
    "br.pinterest.com", "es.scribd.com",
}

SINAIS = ("ppc", "projeto-pedagogico", "projeto_pedagogico", "projetopedagogico",
          "projeto-pedagógico", "matriz", "curricul", "grade", "ementa")


def dominio(site: str | None) -> str | None:
    if not site:
        return None
    host = urlparse(site if "//" in site else "https://" + site).hostname or ""
    host = host.lower().replace("www.", "")
    return host or None


def host_de(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower().replace("www.", "")
    except ValueError:
        return ""


def do_dominio(host: str, dom: str | None) -> bool:
    if not dom:
        return True
    return host == dom or host.endswith("." + dom)


def ignorado(host: str) -> bool:
    return any(host == d or host.endswith("." + d) for d in IGNORADOS)


def score(url: str, titulo: str, dom: str | None) -> int:
    t = (url + " " + titulo).lower()
    s = 0
    if url.lower().endswith(".pdf"):
        s += 5
    if "espanhol" in t or "espanhola" in t:
        s += 6
    for sinal in SINAIS:
        if sinal in t:
            s += 2
    if "letras" in t:
        s += 3
    if do_dominio(host_de(url), dom):
        s += 4
    return s


def buscar_uni(sigla: str, nome: str, site: str | None) -> list[dict]:
    dom = dominio(site)
    consultas = [
        f'{sigla} Letras espanhol PPC projeto pedagógico pdf',
        f'{nome} licenciatura letras espanhol projeto pedagógico',
        f'{sigla} letras português e espanhol matriz curricular',
    ]
    if dom:
        consultas += [
            f'site:{dom} letras espanhol ppc',
            f'site:{dom} letras espanhol projeto pedagógico',
        ]
    vistos: dict[str, dict] = {}
    for consulta in consultas:
        for tent in range(2):
            try:
                with DDGS() as d:
                    brutos = list(d.text(consulta, region="br-pt", max_results=8))
                break
            except Exception:
                time.sleep(2)
                brutos = []
        for r in brutos:
            url = r.get("href") or r.get("url") or ""
            if not url.startswith("http"):
                continue
            host = host_de(url)
            if not host or ignorado(host):
                continue
            titulo = r.get("title") or ""
            if dom and not do_dominio(host, dom):
                # aceita se mencionar a sigla no título/url
                if sigla.lower() not in (url + titulo).lower():
                    continue
            if "letras" not in (url + titulo).lower() and "lingu" not in (url + titulo).lower():
                continue
            sc = score(url, titulo, dom)
            if sc < 6:
                continue
            if url not in vistos or sc > vistos[url]["score"]:
                vistos[url] = {"url": url, "titulo": titulo, "score": sc}
        time.sleep(1)
    return sorted(vistos.values(), key=lambda c: c["score"], reverse=True)[:5]


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--sigla", nargs="*", help="Filtra por siglas")
    args = ap.parse_args()

    dados = json.loads(FONTES.read_text(encoding="utf-8"))
    pendentes = []
    for regiao in dados["regioes"].values():
        for est in regiao["estados"].values():
            for u in est["universidades"]:
                if args.sigla and u["sigla"] not in args.sigla:
                    continue
                if not u.get("url_ppc"):
                    pendentes.append(u)

    print(f"Buscando PPCs para {len(pendentes)} instituições…\n")
    resultados = {}
    for u in pendentes:
        cands = buscar_uni(u["sigla"], u["nome"], u.get("site"))
        resultados[u["sigla"]] = cands
        print(f"### {u['sigla']} — {u['nome']}")
        for c in cands:
            print(f"   [{c['score']:>2}] {c['titulo'][:70]} | {c['url'][:120]}")
        if not cands:
            print("   (nada relevante)")
        print()

    SAIDA.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Candidatos salvos em {SAIDA}")


if __name__ == "__main__":
    main()
