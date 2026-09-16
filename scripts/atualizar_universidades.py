import csv
import re
import sys
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

BASE_DIR = Path(__file__).resolve().parent.parent
SAIDA = BASE_DIR / "data" / "universidades_publicas.csv"
WIKI_API = "https://pt.wikipedia.org/w/api.php"
USER_AGENT = "pesquisa-disciplinas-letras/1.0 (uso academico)"

REGIOES = {"CO": "Centro-Oeste", "NE": "Nordeste", "N": "Norte", "SE": "Sudeste", "S": "Sul"}

UFS = {
    "Acre": "AC", "Alagoas": "AL", "Amapá": "AP", "Amazonas": "AM", "Bahia": "BA",
    "Ceará": "CE", "Distrito Federal": "DF", "Espírito Santo": "ES", "Goiás": "GO",
    "Maranhão": "MA", "Mato Grosso": "MT", "Mato Grosso do Sul": "MS",
    "Minas Gerais": "MG", "Pará": "PA", "Paraíba": "PB", "Paraná": "PR",
    "Pernambuco": "PE", "Piauí": "PI", "Rio de Janeiro": "RJ",
    "Rio Grande do Norte": "RN", "Rio Grande do Sul": "RS", "Rondônia": "RO",
    "Roraima": "RR", "Santa Catarina": "SC", "São Paulo": "SP", "Sergipe": "SE",
    "Tocantins": "TO",
}


def _limpar(texto: str) -> str:
    texto = re.sub(r"\[[^\]]*\]", "", texto)
    return re.sub(r"\s+", " ", texto).strip()


def _wikitexto(titulo: str) -> str:
    resp = httpx.get(
        WIKI_API,
        params={"action": "parse", "page": titulo, "prop": "text", "format": "json",
                "formatversion": "2"},
        headers={"User-Agent": USER_AGENT},
        timeout=40,
    )
    resp.raise_for_status()
    return resp.json()["parse"]["text"]


def _sigla(texto: str) -> str:
    m = re.findall(r"\(\[?([A-Za-zÀ-ÿ]{2,12})\]?\)", texto)
    return m[-1].upper() if m else ""


def federais() -> list[dict]:
    soup = BeautifulSoup(_wikitexto("Lista de universidades federais do Brasil"), "html.parser")
    registros: list[dict] = []
    for tabela in soup.find_all("table", class_="wikitable"):
        cabecalho = [c.get_text(" ", strip=True) for c in tabela.find("tr").find_all(["th", "td"])]

        def col(*nomes: str) -> int | None:
            for nome in nomes:
                if nome in cabecalho:
                    return cabecalho.index(nome)
            return None

        i_sigla = col("Sigla")
        i_nome = col("Nome")
        i_uf = col("UF", "Unidade federativa")
        i_reg = col("Reg.", "Região")
        if i_sigla is None or i_nome is None:
            continue
        for linha in tabela.find_all("tr")[1:]:
            celulas = [c.get_text(" ", strip=True) for c in linha.find_all(["th", "td"])]
            if len(celulas) <= i_sigla:
                continue
            nome = _limpar(celulas[i_nome])
            if not nome.lower().startswith("universidade"):
                continue
            uf_txt = _limpar(celulas[i_uf]) if i_uf is not None and len(celulas) > i_uf else ""
            reg_txt = _limpar(celulas[i_reg]) if i_reg is not None and len(celulas) > i_reg else ""
            registros.append({
                "sigla": _limpar(celulas[i_sigla]).upper(),
                "nome": nome,
                "categoria": "federal",
                "uf": UFS.get(uf_txt, uf_txt),
                "regiao": REGIOES.get(reg_txt, reg_txt),
            })
    return registros


def estaduais() -> list[dict]:
    soup = BeautifulSoup(_wikitexto("Lista de universidades estaduais do Brasil"), "html.parser")
    registros: list[dict] = []
    regiao = ""
    uf = ""
    parar = False
    for no in soup.find_all(["h2", "h3", "ul"]):
        if no.name == "h2":
            titulo = _limpar(no.get_text(" ", strip=True))
            if titulo.startswith("Região"):
                regiao = titulo
            if "Ranking" in titulo or titulo in {"Ver também", "Referências", "Ligações externas"}:
                parar = True
            continue
        if parar:
            continue
        if no.name == "h3":
            titulo = re.sub(r"\([^)]*\)", "", _limpar(no.get_text(" ", strip=True)))
            uf = UFS.get(titulo.strip(), "")
            continue
        if not uf:
            continue
        for item in no.find_all("li", recursive=False):
            bruto = item.get_text(" ", strip=True)
            if "não possui" in bruto.lower() or "dissolvida" in bruto.lower():
                continue
            nome = re.split(r"\s*[–(]", _limpar(bruto))[0].strip()
            if not nome.startswith("Universidade "):
                continue
            if "Aberta do Brasil" in nome:
                continue
            registros.append({
                "sigla": _sigla(bruto),
                "nome": nome,
                "categoria": "estadual",
                "uf": uf,
                "regiao": regiao.replace("Região", "").split("(")[0].strip(),
            })
    return registros


def main() -> int:
    registros = federais() + estaduais()
    vistos: set[str] = set()
    unicos: list[dict] = []
    for r in registros:
        chave = r["sigla"] or r["nome"]
        if chave in vistos:
            continue
        vistos.add(chave)
        unicos.append(r)
    unicos.sort(key=lambda r: (r["categoria"], r["uf"], r["sigla"]))
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with SAIDA.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["sigla", "nome", "categoria", "uf", "regiao"])
        writer.writeheader()
        writer.writerows(unicos)
    print(f"{len(unicos)} universidades gravadas em {SAIDA}")
    print(f"  federais: {sum(1 for r in unicos if r['categoria'] == 'federal')}")
    print(f"  estaduais: {sum(1 for r in unicos if r['categoria'] == 'estadual')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
