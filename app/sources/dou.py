import html
import json
import re
import unicodedata
from datetime import date
from typing import List, Optional
from urllib.parse import urlencode

import httpx

from ..keywords import is_educacao, is_tech, termos_relevantes
from ..models import Proposicao

BASE_URL = "https://www.in.gov.br/consulta/-/buscar/dou"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)

CONSULTAS_PADRAO = [
    "computacao educacao basica",
    "educacao digital",
    "cultura digital escola",
    "letramento digital",
    "inteligencia artificial educacao",
    "formacao de professores tecnologia",
    "tecnologia da informacao educacao",
    "ensino a distancia",
]

TIPOS = [
    "MEDIDA PROVISORIA", "MEDIDA PROVISÓRIA", "INSTRUCAO NORMATIVA",
    "INSTRUÇÃO NORMATIVA", "RESOLUCAO", "RESOLUÇÃO", "PORTARIA", "DECRETO",
    "LEI COMPLEMENTAR", "LEI", "DESPACHO", "EDITAL", "RETIFICACAO",
    "RETIFICAÇÃO", "NOTA TECNICA", "NOTA TÉCNICA", "PARECER", "ATO",
]


def _limpar(texto: str) -> str:
    texto = re.sub(r"<[^>]+>", " ", texto or "")
    texto = html.unescape(texto)
    return re.sub(r"\s+", " ", texto).strip()


def _slug(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", texto).strip("-")[:80]


class DouClient:
    def __init__(self, timeout: float = 45.0, delay: float = 0.3, retries: int = 3):
        self.delay = delay
        self.retries = retries
        self._client = httpx.Client(
            timeout=timeout,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*"},
            follow_redirects=True,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "DouClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def _fetch(self, termo: str, data_inicio: str, data_fim: str, pagina: int, delta: int) -> List[dict]:
        params = {
            "q": termo,
            "s": "todos",
            "exactDate": "personalizado",
            "publishFrom": data_inicio,
            "publishTo": data_fim,
            "sortType": "0",
            "delta": str(delta),
            "currentPage": str(pagina),
        }
        url = f"{BASE_URL}?{urlencode(params)}"
        import time

        last_exc: Optional[Exception] = None
        for tentativa in range(1, self.retries + 1):
            try:
                resp = self._client.get(url)
                resp.raise_for_status()
                resultado = self._parse(resp.text)
                time.sleep(self.delay)
                return resultado
            except (httpx.HTTPError, ValueError) as exc:
                last_exc = exc
                time.sleep(min(2 ** tentativa, 10))
        raise RuntimeError(f"Falha na busca DOU '{termo}': {last_exc}")

    def _parse(self, texto: str) -> List[dict]:
        m = re.search(
            r'id="_br_com_seatecnologia_in_buscadou_BuscaDouPortlet_params"[^>]*>(.*?)</script>',
            texto,
            re.S,
        )
        if not m:
            return []
        try:
            dados = json.loads(html.unescape(m.group(1)))
        except json.JSONDecodeError:
            return []
        return dados.get("jsonArray", [])

    def buscar(
        self,
        termo: str,
        data_inicio: str,
        data_fim: str,
        paginas: int = 3,
        delta: int = 20,
    ) -> List[dict]:
        coletados: List[dict] = []
        for pagina in range(1, paginas + 1):
            itens = self._fetch(termo, data_inicio, data_fim, pagina, delta)
            if not itens:
                break
            coletados.extend(itens)
            if len(itens) < delta:
                break
        return coletados

    def normalize(self, item: dict) -> Optional[Proposicao]:
        titulo = _limpar(item.get("title"))
        conteudo = _limpar(item.get("content"))
        url_title = item.get("urlTitle") or ""
        if not titulo or not url_title:
            return None
        texto = f"{titulo} {conteudo}"
        if not (is_educacao(texto) and is_tech(texto)):
            return None
        tipo = "Ato"
        for candidato in TIPOS:
            if titulo.upper().startswith(candidato):
                tipo = candidato.title()
                break
        numero = None
        m = re.search(r"N[ºo°]\s*([\d\.]+)", titulo, re.I)
        if m:
            numero = m.group(1)
        ano = None
        m = re.search(r"(\d{2})/(\d{2})/(\d{4})", item.get("pubDate", ""))
        if m:
            ano = int(m.group(3))
        pub_name = item.get("pubName", "")
        url = f"https://www.in.gov.br/web/dou/-/{url_title}"
        ementa = titulo
        if conteudo:
            ementa = f"{titulo}. {conteudo[:400]}"
        return Proposicao(
            id=f"dou-{_slug(url_title)}",
            casa="Diário Oficial",
            tipo=tipo,
            numero=numero or "s/n",
            ano=ano or 0,
            ementa=ementa.strip(),
            autor=None,
            data=item.get("pubDate"),
            url=url,
            situacao=pub_name or None,
            orgao=pub_name or None,
            temas=termos_relevantes(texto)[:8],
            fonte="dou",
        )


def data_iso_para_br(valor: str) -> str:
    return valor


def intervalo_padrao(anos: int = 7) -> tuple:
    hoje = date.today()
    inicio = date(hoje.year - anos + 1, 1, 1)
    return inicio.strftime("%d-%m-%Y"), hoje.strftime("%d-%m-%Y")
