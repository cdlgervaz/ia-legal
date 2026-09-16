#!/usr/bin/env python3
"""Gera os dados e o mapa SVG do site de Letras-Espanhol.

Entradas:
  site/fontes/universidades.json    (dataset curado)
  site/fontes/brasil-estados.geojson (malha dos estados)

Saídas:
  site/assets/data.js   (window.LETRAS_DATA)
  site/assets/mapa.js   (window.MAPA_BRASIL)
"""
from __future__ import annotations

import json
import math
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FONTES = RAIZ / "site" / "fontes"
ASSETS = RAIZ / "site" / "assets"

REGION_SLUG = {
    "Norte": "norte",
    "Nordeste": "nordeste",
    "Centro-Oeste": "centro-oeste",
    "Sudeste": "sudeste",
    "Sul": "sul",
}


def rdp(pontos: list[tuple[float, float]], eps: float) -> list[tuple[float, float]]:
    """Ramer-Douglas-Peucker simples."""
    if len(pontos) < 3:
        return pontos
    (x1, y1), (x2, y2) = pontos[0], pontos[-1]
    indice, dist_max = 0, 0.0
    for i in range(1, len(pontos) - 1):
        x0, y0 = pontos[i]
        if (x2 - x1) == 0 and (y2 - y1) == 0:
            d = math.hypot(x0 - x1, y0 - y1)
        else:
            num = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1)
            den = math.hypot(y2 - y1, x2 - x1)
            d = num / den
        if d > dist_max:
            indice, dist_max = i, d
    if dist_max > eps:
        esquerda = rdp(pontos[: indice + 1], eps)
        direita = rdp(pontos[indice:], eps)
        return esquerda[:-1] + direita
    return [pontos[0], pontos[-1]]


def mercator(lon: float, lat: float) -> tuple[float, float]:
    x = math.radians(lon)
    y = math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    return x, y


def construir_mapa() -> str:
    eps = 0.00035
    geo = json.loads((FONTES / "brasil-estados.geojson").read_text(encoding="utf-8"))
    dados = json.loads((FONTES / "universidades.json").read_text(encoding="utf-8"))

    uf_regiao = {}
    for regiao, r in dados["regioes"].items():
        for uf in r["estados"]:
            uf_regiao[uf] = REGION_SLUG[regiao]

    # 1) projeta e simplifica todos os anéis
    aneis: list[tuple[str, list[list[tuple[float, float]]]]] = []
    xs: list[float] = []
    ys: list[float] = []
    for feat in geo["features"]:
        sigla = feat["properties"]["sigla"]
        poligonos = []
        for poly in feat["geometry"]["coordinates"]:
            for anel in poly:
                pts = rdp([mercator(lon, lat) for lon, lat in anel], eps)
                if len(pts) < 2:
                    continue
                xs.extend(p[0] for p in pts)
                ys.extend(p[1] for p in pts)
                poligonos.append(pts)
        if poligonos:
            aneis.append((sigla, poligonos))

    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    escala = 1000.0 / (maxx - minx)
    vb_h = (maxy - miny) * escala
    pad = 8.0

    def t(px: float, py: float) -> tuple[float, float]:
        return (px - minx) * escala, (maxy - py) * escala

    partes = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-pad:.2f} {-pad:.2f} {1000 + 2 * pad:.2f} {vb_h + 2 * pad:.2f}" role="img" aria-label="Mapa do Brasil por estados">'
    ]
    for sigla, poligonos in aneis:
        regiao = uf_regiao.get(sigla, "outros")
        d = " ".join(
            "M" + "L".join(f"{x:.2f},{y:.2f}" for x, y in (t(px, py) for px, py in anel)) + "Z"
            for anel in poligonos
        )
        partes.append(
            f'<path class="uf regiao-{regiao}" data-uf="{sigla}" d="{d}"><title>{sigla}</title></path>'
        )
    partes.append("</svg>")
    return "".join(partes)


def slug(texto: str) -> str:
    import re
    import unicodedata

    base = unicodedata.normalize("NFKD", texto)
    base = "".join(c for c in base if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")


def main() -> None:
    dados = json.loads((FONTES / "universidades.json").read_text(encoding="utf-8"))

    universidades = 0
    cursos = 0
    por_regiao: dict[str, dict] = {}
    por_hab: dict[str, int] = {}
    por_mod: dict[str, int] = {}
    ppc_ok = 0
    estados_com_oferta = 0
    estados_total = 0

    for regiao, r in dados["regioes"].items():
        stats_r = {"universidades": 0, "cursos": 0, "estados": []}
        for uf, e in r["estados"].items():
            estados_total += 1
            if not e["universidades"]:
                continue
            estados_com_oferta += 1
            stats_r["estados"].append(uf)
            for u in e["universidades"]:
                universidades += 1
                stats_r["universidades"] += 1
                if u.get("url_ppc"):
                    ppc_ok += 1
                for c in u["cursos"]:
                    cursos += 1
                    stats_r["cursos"] += 1
                    por_hab[c["habilitacao"]] = por_hab.get(c["habilitacao"], 0) + 1
                    por_mod[c["modalidade"]] = por_mod.get(c["modalidade"], 0) + 1
        por_regiao[regiao] = stats_r

    # normaliza campos auxiliares (ids para navegação)
    for regiao, r in dados["regioes"].items():
        r["slug"] = REGION_SLUG[regiao]
        for uf, e in r["estados"].items():
            e["uf"] = uf
            e["slug"] = slug(e["nome"])
            for u in e["universidades"]:
                u["slug"] = slug(u["sigla"])
                u["regiao"] = regiao
                u["uf"] = uf

    stats = {
        "universidades": universidades,
        "cursos": cursos,
        "regioes": 5,
        "estados_com_oferta": estados_com_oferta,
        "estados_total": estados_total,
        "ppc_disponivel": ppc_ok,
        "ppc_pct": round(100 * ppc_ok / universidades) if universidades else 0,
        "por_regiao": {k: {"universidades": v["universidades"], "cursos": v["cursos"]} for k, v in por_regiao.items()},
        "por_habilitacao": por_hab,
        "por_modalidade": por_mod,
    }

    dados["stats"] = stats
    dados["gerado_em"] = "2026"

    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "data.js").write_text(
        "window.LETRAS_DATA = " + json.dumps(dados, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    (ASSETS / "mapa.js").write_text(
        "window.MAPA_BRASIL = " + json.dumps(construir_mapa(), ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )

    print(f"Universidades: {universidades} | Cursos: {cursos} | PPCs linkados: {ppc_ok}/{universidades}")
    print(f"Por região: {stats['por_regiao']}")
    print(f"Por habilitação: {por_hab}")
    print(f"Por modalidade: {por_mod}")
    print(f"Saídas em {ASSETS}")


if __name__ == "__main__":
    main()
