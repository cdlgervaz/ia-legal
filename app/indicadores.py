import csv
import io
import unicodedata
from typing import List, Tuple

CABECALHOS = {
    "indicador",
    "ano",
    "localidade",
    "uf",
    "rede",
    "valor",
    "unidade",
    "fonte",
    "url",
}

TEMPLATE = (
    "indicador,ano,localidade,uf,rede,valor,unidade,fonte,url\n"
    "IDEB - Anos Iniciais,2023,Brasil,BR,Pública,5.7,índice,INEP,https://www.gov.br/inep\n"
    "IDEB - Anos Finais,2023,Brasil,BR,Pública,4.9,índice,INEP,https://www.gov.br/inep\n"
)


def _normalizar(chave: str) -> str:
    chave = unicodedata.normalize("NFKD", (chave or "").strip().lower())
    return "".join(c for c in chave if not unicodedata.combining(c))


def _valor(valor: str):
    texto = (valor or "").strip().replace(".", "").replace(",", ".")
    if texto == "":
        return None
    try:
        return float(texto)
    except ValueError:
        return None


def parse_csv(texto: str) -> Tuple[List[dict], List[str]]:
    if not texto or not texto.strip():
        return [], ["CSV vazio."]
    amostra = texto[:4096]
    try:
        dialecto = csv.Sniffer().sniff(amostra, delimiters=",;\t")
    except csv.Error:
        dialecto = csv.excel
    leitor = csv.DictReader(io.StringIO(texto), dialect=dialecto)
    if not leitor.fieldnames:
        return [], ["Cabeçalho não encontrado."]
    mapa = {_normalizar(c): c for c in leitor.fieldnames if c}
    if "indicador" not in mapa:
        return [], ["A coluna obrigatória 'indicador' não foi encontrada. Veja o modelo."]

    itens: List[dict] = []
    erros: List[str] = []
    for numero, linha in enumerate(leitor, start=2):
        indicador = (linha.get(mapa["indicador"]) or "").strip()
        if not indicador:
            continue
        ano = None
        if "ano" in mapa:
            bruto = (linha.get(mapa["ano"]) or "").strip()
            if bruto[:4].isdigit():
                ano = int(bruto[:4])
        itens.append(
            {
                "indicador": indicador,
                "ano": ano,
                "localidade": (linha.get(mapa.get("localidade", ""), "") or "Brasil").strip()
                or "Brasil",
                "uf": (linha.get(mapa.get("uf", ""), "") or "").strip() or None,
                "rede": (linha.get(mapa.get("rede", ""), "") or "").strip() or None,
                "valor": _valor(linha.get(mapa.get("valor", ""), "")),
                "unidade": (linha.get(mapa.get("unidade", ""), "") or "").strip() or None,
                "fonte": (linha.get(mapa.get("fonte", ""), "") or "").strip() or None,
                "url": (linha.get(mapa.get("url", ""), "") or "").strip() or None,
            }
        )
    if not itens and not erros:
        erros.append("Nenhuma linha válida encontrada.")
    return itens, erros
