import time
from typing import Dict, List, Optional

import httpx

from ..models import Proposicao, Tramitacao

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"

TEMA_CIENCIA_TECNOLOGIA = 62
TEMA_COMUNICACOES = 37


class CamaraClient:
    def __init__(self, timeout: float = 30.0, delay: float = 0.25, retries: int = 3):
        self.timeout = timeout
        self.delay = delay
        self.retries = retries
        self._client = httpx.Client(
            base_url=BASE_URL,
            timeout=timeout,
            headers={"Accept": "application/json", "User-Agent": "IALegal/1.0"},
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "CamaraClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def _get(self, path: str, params: Optional[Dict] = None) -> dict:
        last_exc: Optional[Exception] = None
        for tentativa in range(1, self.retries + 1):
            try:
                resp = self._client.get(path, params=params)
                if resp.status_code == 429:
                    time.sleep(min(2 ** tentativa, 15))
                    continue
                resp.raise_for_status()
                time.sleep(self.delay)
                return resp.json()
            except (httpx.HTTPError, ValueError) as exc:
                last_exc = exc
                time.sleep(min(2 ** tentativa, 15))
        raise RuntimeError(f"Falha ao consultar {path}: {last_exc}")

    def listar_por_tema(
        self,
        cod_tema: int,
        tipo: str,
        ano: int,
        max_itens: int,
    ) -> List[dict]:
        coletados: List[dict] = []
        pagina = 1
        itens = 50
        while len(coletados) < max_itens:
            data = self._get(
                "/proposicoes",
                {
                    "codTema": cod_tema,
                    "siglaTipo": tipo,
                    "ano": ano,
                    "itens": itens,
                    "pagina": pagina,
                    "ordem": "DESC",
                    "ordenarPor": "id",
                },
            )
            dados = data.get("dados", [])
            if not dados:
                break
            coletados.extend(dados)
            if len(dados) < itens:
                break
            pagina += 1
        return coletados[:max_itens]

    def temas(self, proposicao_id: int) -> List[str]:
        data = self._get(f"/proposicoes/{proposicao_id}/temas")
        return [t.get("tema", "") for t in data.get("dados", []) if t.get("tema")]

    def detalhe(self, proposicao_id: int) -> dict:
        data = self._get(f"/proposicoes/{proposicao_id}")
        return data.get("dados", {})

    def autores(self, proposicao_id: int) -> List[str]:
        data = self._get(f"/proposicoes/{proposicao_id}/autores")
        nomes = []
        for item in data.get("dados", []):
            nome = item.get("nome") or item.get("nomeAutor")
            if nome:
                nomes.append(nome)
        return nomes

    def tramitacoes(self, proposicao_id: int, max_eventos: int = 15) -> List[Tramitacao]:
        data = self._get(f"/proposicoes/{proposicao_id}/tramitacoes")
        dados = data.get("dados", [])
        recorte = dados[-max_eventos:]
        eventos: List[Tramitacao] = []
        for item in recorte:
            eventos.append(
                Tramitacao(
                    sequencia=item.get("sequencia"),
                    data_hora=item.get("dataHora"),
                    orgao=item.get("siglaOrgao"),
                    descricao=item.get("descricaoTramitacao"),
                    situacao=item.get("descricaoSituacao"),
                    regime=item.get("regime"),
                )
            )
        return eventos

    def normalize(
        self,
        item: dict,
        temas: Optional[List[str]] = None,
        autor: Optional[str] = None,
        situacao: Optional[str] = None,
        orgao: Optional[str] = None,
    ) -> Proposicao:
        pid = int(item["id"])
        tipo = item.get("siglaTipo", "")
        numero = str(item.get("numero", ""))
        ano = int(item.get("ano") or 0)
        return Proposicao(
            id=f"camara-{pid}",
            casa="Câmara",
            tipo=tipo,
            numero=numero,
            ano=ano,
            ementa=(item.get("ementa") or "").strip(),
            autor=autor,
            data=(item.get("dataApresentacao") or "")[:10] or None,
            url=f"https://www.camara.leg.br/propostas-legislativas/{pid}",
            situacao=situacao,
            orgao=orgao,
            temas=temas or [],
            fonte="camara",
        )
