import re
import unicodedata
from typing import List, Optional
from urllib.parse import unquote

import httpx

from ..models import Proposicao

BASE_PAGE = "https://www.gov.br/mec/pt-br/cne/pareceres-relatados"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)
MESES = [
    "janeiro", "fevereiro", "marco", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]


def _slug(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c)).lower()
    texto = re.sub(r"[^a-z0-9]+", "-", texto).strip("-")
    return texto[:60]


class CneClient:
    def __init__(self, timeout: float = 60.0, delay: float = 0.25, retries: int = 3):
        self.delay = delay
        self.retries = retries
        self._client = httpx.Client(
            timeout=timeout,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/pdf,*/*"},
            follow_redirects=True,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "CneClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def _get_html(self, url: str) -> str:
        last_exc: Optional[Exception] = None
        for tentativa in range(1, self.retries + 1):
            try:
                resp = self._client.get(url)
                resp.raise_for_status()
                return resp.text
            except httpx.HTTPError as exc:
                last_exc = exc
                import time
                time.sleep(min(2 ** tentativa, 10))
        raise RuntimeError(f"Falha ao acessar {url}: {last_exc}")

    def listar(self) -> List[dict]:
        html = self._get_html(BASE_PAGE)
        hrefs = set(re.findall(r'href="([^"]+\.pdf)"', html, re.I))
        itens: List[dict] = []
        for href in hrefs:
            href = href.replace("&amp;", "&")
            if "prel" not in href.lower() and "parecer" not in href.lower():
                continue
            info = self._parse(href)
            if info:
                itens.append(info)
        itens.sort(key=lambda i: (i["ano"], i["numero"] or 0))
        return itens

    def _parse(self, url: str) -> Optional[dict]:
        base = unquote(url.split("/")[-1])
        numero: Optional[int] = None
        ano: Optional[int] = None
        m = re.search(r"prel(\d{1,2})_(\d{4})", base, re.I)
        if m:
            numero, ano = int(m.group(1)), int(m.group(2))
        else:
            m = re.search(r"parecer_cne_?(\d{1,2})(\d{4})", base, re.I)
            if m:
                numero, ano = int(m.group(1)), int(m.group(2))
        if ano is None:
            m = re.search(r"/(\d{4})/", url)
            if not m:
                return None
            ano = int(m.group(1))
        mes = None
        alvo = _slug(url)
        for indice, nome in enumerate(MESES, start=1):
            if nome in alvo:
                mes = indice
                break
        identificador = f"cne-{_slug(base.rsplit('.', 1)[0])}"
        return {
            "id": identificador,
            "url": url,
            "numero": numero,
            "ano": ano,
            "mes": mes,
            "extraordinaria": "extraordin" in alvo,
        }

    def _cache_path(self, item_id: str):
        from ..config import get_settings

        pasta = get_settings().data_dir / "cne_textos"
        pasta.mkdir(parents=True, exist_ok=True)
        return pasta / f"{item_id}.txt"

    def extrair_texto(self, url: str, item_id: str = "", max_caracteres: int = 40000) -> str:
        if item_id:
            cache = self._cache_path(item_id)
            if cache.exists():
                return cache.read_text(encoding="utf-8", errors="ignore")[:max_caracteres]
        last_exc: Optional[Exception] = None
        for tentativa in range(1, self.retries + 1):
            try:
                resp = self._client.get(url)
                resp.raise_for_status()
                from io import BytesIO
                from pypdf import PdfReader

                leitor = PdfReader(BytesIO(resp.content))
                partes = []
                for pagina in leitor.pages:
                    partes.append(pagina.extract_text() or "")
                    if sum(len(p) for p in partes) > max_caracteres:
                        break
                texto = re.sub(r"[ \t]+", " ", "\n".join(partes)).strip()[:max_caracteres]
                if item_id:
                    self._cache_path(item_id).write_text(texto, encoding="utf-8")
                return texto
            except Exception as exc:
                last_exc = exc
                import time
                time.sleep(min(2 ** tentativa, 10))
        raise RuntimeError(f"Falha ao extrair PDF {url}: {last_exc}")

    def normalize(self, item: dict, texto: str) -> Proposicao:
        numero = item.get("numero")
        ano = item.get("ano")
        mes = item.get("mes")
        rotulo_mes = MESES[mes - 1] if mes else None
        periodo = f"{rotulo_mes}/{ano}" if rotulo_mes else str(ano)
        if numero:
            identificacao = f"Parecer CNE nº {numero}/{ano}"
        else:
            identificacao = f"Pareceres relatados CNE - {periodo}"
        ementa = (
            f"{identificacao}. Documento de pareceres relatados pelo Conselho Nacional "
            f"de Educação (reunião de {periodo})."
        )
        from ..keywords import termos_relevantes

        return Proposicao(
            id=item["id"],
            casa="CNE",
            tipo="Parecer",
            numero=f"{numero}/{ano}" if numero else str(ano),
            ano=ano or 0,
            ementa=ementa,
            autor="Conselho Nacional de Educação",
            data=None,
            url=item["url"],
            situacao="Pareceres relatados (pré-publicação)",
            orgao="CNE/MEC",
            temas=termos_relevantes(texto)[:8],
            fonte="cne",
        )
